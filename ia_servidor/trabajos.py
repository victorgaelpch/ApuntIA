"""Cola asíncrona de análisis del servidor IA (BACK-37).

Por qué: un documento tarda 40–90 s. Con una sola petición HTTP larga, un corte de Internet o del
túnel a mitad hace perder el trabajo y la GPU lo repite. Con la cola:

    POST   /api/v1/trabajos?tarea=documento   (cuerpo = imagen, cabecera Idempotency-Key)  → 202
    GET    /api/v1/trabajos/{id}              → en_cola | procesando (progreso) | completado | fallido | cancelado
    DELETE /api/v1/trabajos/{id}              → cancela (si aún no terminó)

- Una sola GPU: un trabajador procesa los trabajos de uno en uno (y comparte el turno de GPU con
  /api/v1/analisis síncrono a través del mismo semáforo del servicio).
- Idempotencia: la misma Idempotency-Key del mismo dispositivo devuelve el MISMO trabajo (no se
  vuelve a gastar GPU), salvo que el anterior fallara o se cancelara.
- Si el cliente pierde la conexión, el resultado espera en memoria `ttl_s` (30 min por defecto)
  y se recoge por su id. Si el servidor se reinicia, la cola se pierde y el cliente recibe 404:
  vuelve a enviar con la misma clave (el backend de la laptop guarda la foto original).
- Límite de cola (`IA_MAX_COLA`): al llenarse responde 429 OCUPADO con Retry-After.
- Cada trabajo solo lo ve el dispositivo que lo creó (404 para los demás).
"""

from __future__ import annotations

import collections
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field

from ia_servidor.errores import ErrorIA

logger = logging.getLogger("apuntia.ia")
TERMINADOS = ("completado", "fallido", "cancelado")


class Cancelado(Exception):
    """El cliente canceló el trabajo mientras se procesaba."""


@dataclass
class TrabajoIA:
    id: str
    dispositivo: str
    clave: str | None
    tarea: str
    datos: bytes | None
    estado: str = "en_cola"
    progreso: int = 0
    creado: float = field(default_factory=time.time)
    terminado: float | None = None
    resultado: dict | None = None
    error: dict | None = None
    cancelar: bool = False

    def publico(self, posicion: int | None = None) -> dict:
        r = {"trabajo_id": self.id, "tarea": self.tarea, "estado": self.estado, "progreso": self.progreso}
        if posicion is not None:
            r["posicion"] = posicion
        if self.estado == "completado":
            r["resultado"] = self.resultado
        if self.error:
            r["error"] = self.error
        return r


class ColaTrabajos:
    def __init__(self, servicio, max_cola: int = 10, ttl_s: float = 1800, ahora=time.time):
        self.servicio = servicio
        self.max_cola, self.ttl_s, self.ahora = max_cola, ttl_s, ahora
        self.trabajos: dict[str, TrabajoIA] = {}
        self.cola: collections.deque[str] = collections.deque()
        self.cerrojo = threading.Lock()
        self.hay_trabajo = threading.Event()
        self._hilo: threading.Thread | None = None
        self._parar = threading.Event()

    # ------------------------------------------------------------------ API
    def encolar(self, dispositivo: str, tarea: str, datos: bytes, clave: str | None) -> tuple[TrabajoIA, bool]:
        """Devuelve (trabajo, nuevo). Con la misma clave y dispositivo, el mismo trabajo."""
        with self.cerrojo:
            self._purgar()
            if clave:
                previo = next((t for t in self.trabajos.values() if t.dispositivo == dispositivo and t.clave == clave
                               and t.estado not in ("fallido", "cancelado")), None)
                if previo:
                    return previo, False
            activos = sum(t.estado in ("en_cola", "procesando") for t in self.trabajos.values())
            if activos >= self.max_cola:
                raise ErrorIA("OCUPADO", f"cola llena ({activos})")
            t = TrabajoIA(uuid.uuid4().hex, dispositivo, clave, tarea, datos)
            self.trabajos[t.id] = t
            self.cola.append(t.id)
        self.iniciar()
        self.hay_trabajo.set()
        logger.info("ia: trabajo=%s tarea=%s encolado (cola %d)", t.id[:8], tarea, len(self.cola))
        return t, True

    def obtener(self, dispositivo: str, trabajo_id: str) -> tuple[TrabajoIA, int | None]:
        with self.cerrojo:
            self._purgar()
            t = self.trabajos.get(trabajo_id)
            if t is None or t.dispositivo != dispositivo:
                raise ErrorIA("TRABAJO_NO_ENCONTRADO", trabajo_id[:12])
            posicion = list(self.cola).index(t.id) + 1 if t.id in self.cola else None
            return t, posicion

    def cancelar(self, dispositivo: str, trabajo_id: str) -> TrabajoIA:
        t, _ = self.obtener(dispositivo, trabajo_id)
        with self.cerrojo:
            if t.estado == "en_cola":
                self.cola.remove(t.id)
                self._terminar(t, "cancelado")
            elif t.estado == "procesando":
                t.cancelar = True  # el trabajador lo comprueba entre regiones
        return t

    # ------------------------------------------------------------------ trabajador
    def iniciar(self) -> None:
        if self._hilo is None or not self._hilo.is_alive():
            self._parar.clear()
            self._hilo = threading.Thread(target=self._bucle, name="ia-trabajos", daemon=True)
            self._hilo.start()

    def detener(self) -> None:
        self._parar.set()
        self.hay_trabajo.set()

    def _bucle(self) -> None:
        while not self._parar.is_set():
            with self.cerrojo:
                tid = self.cola.popleft() if self.cola else None
                t = self.trabajos.get(tid) if tid else None
                if t:
                    t.estado = "procesando"
            if t is None:
                self.hay_trabajo.wait(timeout=1.0)
                self.hay_trabajo.clear()
                continue
            self.procesar(t)

    def procesar(self, t: TrabajoIA) -> None:
        def avance(hechas: int, total: int) -> None:
            t.progreso = int(100 * hechas / max(1, total))
            if t.cancelar:
                raise Cancelado()

        try:
            resultado = self.servicio.analizar(t.datos, t.tarea, t.id[:16], progreso=avance)
            with self.cerrojo:
                t.resultado, t.progreso = resultado, 100
                self._terminar(t, "completado")
        except Cancelado:
            with self.cerrojo:
                self._terminar(t, "cancelado")
        except ErrorIA as e:
            with self.cerrojo:
                t.error = e.cuerpo(t.id[:16])["error"]
                self._terminar(t, "fallido")
        except Exception:  # noqa: BLE001 — un fallo no detiene el trabajador
            logger.exception("ia: trabajo=%s error no controlado", t.id[:8])
            with self.cerrojo:
                t.error = ErrorIA("ERROR_INTERNO").cuerpo(t.id[:16])["error"]
                self._terminar(t, "fallido")
        logger.info("ia: trabajo=%s %s", t.id[:8], t.estado)

    # ------------------------------------------------------------------ interno (con el cerrojo tomado)
    def _terminar(self, t: TrabajoIA, estado: str) -> None:
        t.estado, t.terminado, t.datos = estado, self.ahora(), None  # la imagen se libera al terminar

    def _purgar(self) -> None:
        limite = self.ahora() - self.ttl_s
        for tid in [k for k, t in self.trabajos.items() if t.estado in TERMINADOS and (t.terminado or 0) < limite]:
            del self.trabajos[tid]
