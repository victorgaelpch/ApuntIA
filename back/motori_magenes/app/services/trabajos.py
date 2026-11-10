"""Gestor de trabajos durables para OCR, investigación y PDF (BACK-27).

Diseño proporcional al proyecto, sin servicios extra (Redis, Celery):
  - Los trabajos viven en SQLite (tabla `trabajos`): sobreviven a reinicios.
  - Un hilo despachador toma los pendientes en orden de llegada y los ejecuta en
    un pool de MAX_TRABAJOS_SIMULTANEOS hilos. La API sigue respondiendo.
  - Cancelar marca una bandera que el manejador comprueba en cada avance; un
    trabajo pendiente se cancela al instante.
  - Al arrancar, los trabajos que quedaron «procesando» (el proceso se cayó) se
    vuelven a encolar mientras queden intentos (máx. 3); si no, quedan
    «fallido» con un motivo visible.
  - Límite de 3 trabajos activos por usuario → 429 DEMASIADOS_TRABAJOS.
Funciona igual con los scripts de arranque y en Docker: solo usa la base de datos.
"""

import json
import logging
import secrets
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable

from app.core.config import settings
from app.core.errores import ApiError
from app.datos.bd import BaseDatos, ahora

logger = logging.getLogger("apuntia.trabajos")

ACTIVOS = ("pendiente", "procesando")
MAX_ACTIVOS_POR_USUARIO = 3


class Cancelado(Exception):
    """El usuario canceló el trabajo."""


class ErrorTrabajo(Exception):
    """Fallo previsto: se muestra al usuario con su código."""

    def __init__(self, codigo: str, mensaje: str):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


@dataclass
class Resultado:
    estado: str = "completado"   # completado | parcial
    datos: dict = field(default_factory=dict)
    aviso: str | None = None      # para «parcial»: qué falló


@dataclass
class Trabajo:
    id: str
    usuario_id: str
    apunte_id: str | None
    tipo: str
    parametros: dict
    gestor: "GestorTrabajos"

    def avance(self, etapa: str, progreso: int) -> None:
        """Informa la etapa y lanza Cancelado si el usuario canceló."""
        fila = self.gestor.bd.uno("SELECT cancelar FROM trabajos WHERE id = ?", (self.id,))
        if fila is None or fila["cancelar"]:
            raise Cancelado()
        self.gestor.bd.ejecutar("UPDATE trabajos SET etapa = ?, progreso = ?, actualizado = ? WHERE id = ?",
                                (etapa, max(0, min(99, progreso)), ahora(), self.id))


Manejador = Callable[[Trabajo], Resultado]


def publico(fila) -> dict:
    d = {k: fila[k] for k in ("id", "tipo", "estado", "etapa", "progreso", "intentos", "apunte_id",
                              "creado", "actualizado")}
    d["resultado"] = json.loads(fila["resultado"]) if fila["resultado"] else None
    d["error"] = ({"codigo": fila["error_codigo"], "mensaje": fila["error"], "referencia": fila["error_id"]}
                  if fila["error_codigo"] else None)
    return d


class GestorTrabajos:
    def __init__(self, bd: BaseDatos, simultaneos: int | None = None, intervalo: float = 0.2):
        self.bd = bd
        self.manejadores: dict[str, Manejador] = {}
        self.al_cancelar: dict[str, Callable[[Trabajo], None]] = {}
        self.simultaneos = simultaneos or settings.max_trabajos_simultaneos
        self.intervalo = intervalo
        self._pool: ThreadPoolExecutor | None = None
        self._hilo: threading.Thread | None = None
        self._parar = threading.Event()
        self._despertar = threading.Event()
        self._en_curso = threading.Semaphore(self.simultaneos)

    def registrar(self, tipo: str, manejador: Manejador, al_cancelar: Callable[[Trabajo], None] | None = None):
        self.manejadores[tipo] = manejador
        if al_cancelar:
            self.al_cancelar[tipo] = al_cancelar

    # ---------------------------------------------------------------- ciclo de vida

    def iniciar(self) -> None:
        if self._hilo and self._hilo.is_alive():
            return
        self.recuperar()
        self._parar.clear()
        self._pool = ThreadPoolExecutor(max_workers=self.simultaneos, thread_name_prefix="trabajo")
        self._hilo = threading.Thread(target=self._despachar, name="despachador", daemon=True)
        self._hilo.start()

    def detener(self, esperar: bool = True) -> None:
        self._parar.set()
        self._despertar.set()
        if self._hilo:
            self._hilo.join(timeout=5)
        if self._pool:
            self._pool.shutdown(wait=esperar, cancel_futures=False)

    def recuperar(self) -> int:
        """Trabajos interrumpidos por un reinicio: se reencolan o se marcan fallidos."""
        filas = self.bd.todos("SELECT id, intentos, max_intentos FROM trabajos WHERE estado = 'procesando'")
        for f in filas:
            if f["intentos"] < f["max_intentos"]:
                self.bd.ejecutar("UPDATE trabajos SET estado = 'pendiente', etapa = NULL, actualizado = ? WHERE id = ?",
                                 (ahora(), f["id"]))
            else:
                self.bd.ejecutar("UPDATE trabajos SET estado = 'fallido', error_codigo = 'INTERRUMPIDO', "
                                 "error = 'El servidor se reinició varias veces durante este trabajo.', actualizado = ? "
                                 "WHERE id = ?", (ahora(), f["id"]))
        if filas:
            logger.info("Trabajos recuperados tras reinicio: %d", len(filas))
        return len(filas)

    # ---------------------------------------------------------------- API

    def encolar(self, usuario_id: str, tipo: str, apunte_id: str | None = None, parametros: dict | None = None) -> dict:
        if tipo not in self.manejadores:
            raise ValueError(f"tipo de trabajo desconocido: {tipo}")
        with self.bd.transaccion() as con:
            activos = con.execute("SELECT COUNT(*) AS n FROM trabajos WHERE usuario_id = ? AND estado IN (?, ?)",
                                  (usuario_id, *ACTIVOS)).fetchone()["n"]
            if activos >= MAX_ACTIVOS_POR_USUARIO:
                raise ApiError(429, "DEMASIADOS_TRABAJOS",
                               "Ya tienes varios procesos en curso. Espera a que terminen e inténtalo de nuevo.")
            tid = secrets.token_hex(16)
            con.execute("INSERT INTO trabajos (id, usuario_id, apunte_id, tipo, estado, parametros, creado, actualizado) "
                        "VALUES (?, ?, ?, ?, 'pendiente', ?, ?, ?)",
                        (tid, usuario_id, apunte_id, tipo, json.dumps(parametros or {}), ahora(), ahora()))
        self.iniciar()
        self._despertar.set()
        return self.obtener(usuario_id, tid)

    def obtener(self, usuario_id: str, trabajo_id: str) -> dict:
        fila = self.bd.uno("SELECT * FROM trabajos WHERE id = ? AND usuario_id = ?", (trabajo_id, usuario_id))
        if fila is None:
            raise ApiError(404, "NO_ENCONTRADO", "No encontramos ese proceso.")
        return publico(fila)

    def cancelar(self, usuario_id: str, trabajo_id: str) -> dict:
        trabajo = self.obtener(usuario_id, trabajo_id)
        if trabajo["estado"] == "pendiente":
            self.bd.ejecutar("UPDATE trabajos SET estado = 'cancelado', cancelar = 1, actualizado = ? "
                             "WHERE id = ? AND estado = 'pendiente'", (ahora(), trabajo_id))
        elif trabajo["estado"] == "procesando":
            self.bd.ejecutar("UPDATE trabajos SET cancelar = 1, actualizado = ? WHERE id = ?", (ahora(), trabajo_id))
        return self.obtener(usuario_id, trabajo_id)

    def reintentar(self, usuario_id: str, trabajo_id: str) -> dict:
        trabajo = self.obtener(usuario_id, trabajo_id)
        if trabajo["estado"] not in ("fallido", "cancelado", "parcial"):
            raise ApiError(409, "TRABAJO_NO_REINTENTABLE", "Solo se puede reintentar un proceso fallido, parcial o cancelado.")
        # El mismo trabajo vuelve a la cola: no se duplica ni se crea otro apunte o PDF.
        self.bd.ejecutar("UPDATE trabajos SET estado = 'pendiente', cancelar = 0, etapa = NULL, progreso = 0, "
                         "intentos = 0, error_codigo = NULL, error = NULL, error_id = NULL, actualizado = ? WHERE id = ?",
                         (ahora(), trabajo_id))
        self.iniciar()
        self._despertar.set()
        return self.obtener(usuario_id, trabajo_id)

    # ---------------------------------------------------------------- ejecución

    def _tomar(self):
        with self.bd.transaccion() as con:
            fila = con.execute("SELECT * FROM trabajos WHERE estado = 'pendiente' ORDER BY creado, rowid LIMIT 1").fetchone()
            if fila is None:
                return None
            con.execute("UPDATE trabajos SET estado = 'procesando', intentos = intentos + 1, progreso = 0, "
                        "actualizado = ? WHERE id = ?", (ahora(), fila["id"]))
            return fila

    def _despachar(self) -> None:
        while not self._parar.is_set():
            if not self._en_curso.acquire(timeout=self.intervalo):
                continue
            try:
                fila = self._tomar()
            except Exception:  # noqa: BLE001
                logger.exception("Error al tomar trabajos")
                fila = None
            if fila is None:
                self._en_curso.release()
                self._despertar.wait(self.intervalo)
                self._despertar.clear()
                continue
            self._pool.submit(self._ejecutar, fila)

    def _ejecutar(self, fila) -> None:
        trabajo = Trabajo(fila["id"], fila["usuario_id"], fila["apunte_id"], fila["tipo"],
                          json.loads(fila["parametros"]), self)
        try:
            resultado = self.manejadores[trabajo.tipo](trabajo)
            self._terminar(trabajo.id, resultado.estado, resultado=resultado.datos,
                           codigo="PARCIAL" if resultado.estado == "parcial" else None, mensaje=resultado.aviso)
        except Cancelado:
            if trabajo.tipo in self.al_cancelar:
                try:
                    self.al_cancelar[trabajo.tipo](trabajo)
                except Exception:  # noqa: BLE001
                    logger.exception("Error al limpiar un trabajo cancelado")
            self._terminar(trabajo.id, "cancelado")
        except ErrorTrabajo as exc:
            self._terminar(trabajo.id, "fallido", codigo=exc.codigo, mensaje=exc.mensaje)
        except ApiError as exc:  # p. ej. ALMACENAMIENTO_LLENO: error previsto con mensaje para el usuario
            self._terminar(trabajo.id, "fallido", codigo=exc.codigo, mensaje=exc.mensaje)
        except Exception as exc:  # noqa: BLE001
            error_id = uuid.uuid4().hex[:12]
            logger.error("Trabajo %s (%s) falló (id=%s)", trabajo.id, trabajo.tipo, error_id, exc_info=exc)
            self._terminar(trabajo.id, "fallido", codigo="ERROR_INTERNO",
                           mensaje="Ocurrió un error inesperado. Puedes reintentarlo.", error_id=error_id)
        finally:
            self._en_curso.release()
            self._despertar.set()

    def _terminar(self, tid, estado, resultado=None, codigo=None, mensaje=None, error_id=None):
        self.bd.ejecutar("UPDATE trabajos SET estado = ?, progreso = ?, resultado = ?, error_codigo = ?, error = ?, "
                         "error_id = ?, actualizado = ? WHERE id = ?",
                         (estado, 100 if estado in ("completado", "parcial") else 0,
                          json.dumps(resultado) if resultado is not None else None, codigo, mensaje, error_id,
                          ahora(), tid))
