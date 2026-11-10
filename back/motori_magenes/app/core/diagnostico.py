"""Diagnóstico del sistema completo (FULL-21). Guía: docs/diagnostico.md.

- Identificador de petición `X-ApuntIA-Peticion-Id`: se acepta el que manda el cliente si
  es válido o se genera uno; viaja en la respuesta y en cada línea de log de esa petición.
  No contiene datos de la persona: sirve para correlacionar interfaz → API → trabajo.
- Logs con datos sensibles enmascarados (emails, tokens largos, contraseñas) y formato
  opcional JSON (`LOG_FORMATO=json`).
- Métricas en memoria de las peticiones (por grupo de ruta: número, errores, p50/p95) y
  alertas en el log cuando una petición tarda demasiado.
- Comprobaciones de disponibilidad para `GET /api/v2/listo`.
"""

import contextvars
import json
import logging
import os
import re
import shutil
import statistics
import threading
import time
import uuid
from collections import defaultdict, deque

from app.core.config import settings

peticion_actual: contextvars.ContextVar[str] = contextvars.ContextVar("peticion_actual", default="-")
ID_VALIDO = re.compile(r"^[A-Za-z0-9-]{8,64}$")
INICIO = time.time()

# ------------------------------------------------------------------ logs

PATRONES_SENSIBLES = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email]"),
    (re.compile(r"(?i)(password|contraseña|token|csrf|cookie|apuntia_sesion)\s*[=:]\s*\S+"), r"\1=[oculto]"),
    (re.compile(r"\b[A-Za-z0-9_-]{40,}\b"), "[token]"),
]


def redactar(texto: str) -> str:
    for patron, sustituto in PATRONES_SENSIBLES:
        texto = patron.sub(sustituto, texto)
    return texto


class FiltroDiagnostico(logging.Filter):
    """Añade el id de la petición y enmascara datos sensibles en TODAS las líneas."""

    def filter(self, registro: logging.LogRecord) -> bool:
        registro.peticion = peticion_actual.get()
        try:
            mensaje = registro.getMessage()
        except Exception:  # noqa: BLE001
            return True
        limpio = redactar(mensaje)
        if limpio != mensaje:
            registro.msg, registro.args = limpio, None
        return True


class FormatoJson(logging.Formatter):
    def format(self, registro: logging.LogRecord) -> str:
        datos = {"ts": self.formatTime(registro, "%Y-%m-%dT%H:%M:%S"), "nivel": registro.levelname,
                 "origen": registro.name, "peticion": getattr(registro, "peticion", "-"), "mensaje": registro.getMessage()}
        if registro.exc_info:
            datos["traza"] = redactar(self.formatException(registro.exc_info))
        return json.dumps(datos, ensure_ascii=False)


class SinConsulta(logging.Filter):
    """La línea de acceso de uvicorn no debe guardar la consulta (?q=… son búsquedas privadas)."""

    def filter(self, registro: logging.LogRecord) -> bool:
        if isinstance(registro.args, tuple) and len(registro.args) >= 3 and isinstance(registro.args[2], str):
            registro.args = registro.args[:2] + (registro.args[2].split("?")[0],) + registro.args[3:]
        return True


def configurar_logs() -> None:
    acceso = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, SinConsulta) for f in acceso.filters):
        acceso.addFilter(SinConsulta())
    raiz = logging.getLogger()
    if any(isinstance(f, FiltroDiagnostico) for h in raiz.handlers for f in h.filters):
        return
    if not raiz.handlers:
        logging.basicConfig(level=logging.INFO)
    formato = (FormatoJson() if os.getenv("LOG_FORMATO", "texto").lower() == "json"
               else logging.Formatter("%(asctime)s %(levelname)s %(name)s [%(peticion)s] %(message)s"))
    for manejador in raiz.handlers:
        manejador.addFilter(FiltroDiagnostico())
        manejador.setFormatter(formato)
    raiz.setLevel(logging.INFO)


# ------------------------------------------------------------------ métricas de peticiones

def grupo_de_ruta(ruta: str) -> str:
    """/api/v2/apuntes/abc123/versiones/2 → /api/v2/apuntes/{id}/versiones/{id} (sin ids ni consultas)."""
    partes = []
    for p in ruta.split("?")[0].strip("/").split("/"):
        partes.append("{id}" if re.fullmatch(r"[0-9a-f]{12,}|\d+|[A-Za-z0-9_-]{20,}", p) else p)
    return "/" + "/".join(partes)


class Metricas:
    def __init__(self, ventana: int = 500):
        self._bloqueo = threading.Lock()
        self.total = 0
        self.por_clase = defaultdict(int)
        self.tiempos: dict[str, deque] = defaultdict(lambda: deque(maxlen=ventana))
        self.errores: dict[str, int] = defaultdict(int)

    def registrar(self, metodo: str, ruta: str, estado: int, ms: float) -> None:
        clave = f"{metodo} {grupo_de_ruta(ruta)}"
        with self._bloqueo:
            self.total += 1
            self.por_clase[f"{estado // 100}xx"] += 1
            self.tiempos[clave].append(ms)
            if estado >= 500:
                self.errores[clave] += 1

    def resumen(self) -> dict:
        with self._bloqueo:
            rutas = {}
            for clave, valores in self.tiempos.items():
                ordenados = sorted(valores)
                rutas[clave] = {"n": len(ordenados), "p50_ms": round(statistics.median(ordenados), 1),
                                "p95_ms": round(ordenados[min(len(ordenados) - 1, int(len(ordenados) * 0.95))], 1),
                                "errores_5xx": self.errores.get(clave, 0)}
            return {"total": self.total, "por_clase": dict(self.por_clase),
                    "rutas": dict(sorted(rutas.items(), key=lambda kv: -kv[1]["n"])[:30])}


metricas = Metricas()
logger_acceso = logging.getLogger("apuntia.peticiones")


class IdPeticion:
    """Middleware ASGI: id de petición, línea de acceso (sin consultas) y métricas."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        recibido = dict(scope.get("headers", [])).get(b"x-apuntia-peticion-id", b"").decode("latin-1")
        pid = recibido if ID_VALIDO.match(recibido) else uuid.uuid4().hex[:16]
        token = peticion_actual.set(pid)
        inicio = time.monotonic()
        estado = 500

        async def enviar(mensaje):
            nonlocal estado
            if mensaje["type"] == "http.response.start":
                estado = mensaje["status"]
                mensaje["headers"] = list(mensaje.get("headers", [])) + [(b"x-apuntia-peticion-id", pid.encode())]
            await send(mensaje)

        try:
            await self.app(scope, receive, enviar)
        finally:
            ms = (time.monotonic() - inicio) * 1000
            ruta = scope["path"]
            if not ruta.startswith(("/front/", "/salud")):  # sin ruido de estáticos ni sondas
                metricas.registrar(scope["method"], ruta, estado, ms)
                nivel = logging.WARNING if ms > settings.alerta_peticion_ms or estado >= 500 else logging.INFO
                logger_acceso.log(nivel, "%s %s %s %.0fms%s", scope["method"], grupo_de_ruta(ruta), estado, ms,
                                  " LENTA" if ms > settings.alerta_peticion_ms else "")
            peticion_actual.reset(token)


# ------------------------------------------------------------------ disponibilidad

def comprobar_dependencias() -> dict[str, dict]:
    """Cada dependencia: {ok, obligatoria, detalle}. Sin datos de usuarios."""
    from app.core import contexto
    from app.services import investigacion
    from app.services.ocr import motor_ocr
    resultado: dict[str, dict] = {}
    ctx = contexto.obtener()
    try:
        ctx.bd.uno("SELECT 1")
        version = ctx.bd.version_esquema()
        esperada = len(list(_carpeta_migraciones().glob("[0-9][0-9][0-9][0-9]_*.sql")))
        ok = version == esperada
        resultado["base_datos"] = {"ok": ok, "obligatoria": True,
                                   "detalle": f"esquema {version}/{esperada}" if ok else
                                   f"esquema {version} de {esperada}: faltan migraciones; reinicia el servidor"}
    except Exception as exc:  # noqa: BLE001
        resultado["base_datos"] = {"ok": False, "obligatoria": True, "detalle": f"no responde ({type(exc).__name__})"}
    try:
        prueba = ctx.data_dir / "tmp" / f"listo-{uuid.uuid4().hex}"
        prueba.parent.mkdir(parents=True, exist_ok=True)
        prueba.write_bytes(b"ok")
        prueba.unlink()
        libre = shutil.disk_usage(ctx.data_dir).free // (1024 * 1024)
        ok = libre >= settings.minimo_disco_mb
        resultado["almacenamiento"] = {"ok": ok, "obligatoria": True, "libre_mb": libre,
                                       "detalle": "escribible" if ok else f"quedan {libre} MB: libera espacio en DATA_DIR"}
    except Exception as exc:  # noqa: BLE001
        resultado["almacenamiento"] = {"ok": False, "obligatoria": True,
                                       "detalle": f"no se puede escribir en DATA_DIR ({type(exc).__name__}): revisa permisos"}
    vivo = bool(ctx.trabajos._hilo and ctx.trabajos._hilo.is_alive())
    resultado["trabajos"] = {"ok": vivo, "obligatoria": True,
                             "detalle": "procesando la cola" if vivo else "el despachador de trabajos no está activo"}
    info = motor_ocr().info()
    requerido = settings.ocr_motor != "ninguno"
    resultado["ocr"] = {"ok": info["disponible"], "obligatoria": requerido,
                        "detalle": (f"{info['motor']} {info.get('version', '')}".strip() if info["disponible"] else
                                    "Tesseract no responde: instálalo o define TESSERACT_CMD" if requerido else
                                    "desactivado (OCR_MOTOR=ninguno)")}
    from app.services.ia import registro as ia
    vlm = ia.registro().motores.get("ollama_vlm")
    if vlm is not None:
        ok, info = vlm.estado()
        resultado["ia_local"] = {"ok": ok, "obligatoria": False,
                                 "detalle": f"{info.modelo} en Ollama {info.version}" if ok else info.detalle}
    prov = investigacion.proveedor()
    resultado["investigacion"] = {"ok": prov.disponible(), "obligatoria": False,
                                  "detalle": f"proveedor {prov.nombre}" if prov.disponible() else "desactivada: opcional"}
    return resultado


def _carpeta_migraciones():
    from app.datos.bd import MIGRACIONES
    return MIGRACIONES


def resumen_trabajos() -> dict:
    from app.core import contexto
    bd = contexto.obtener().bd
    estados = {f["estado"]: f["n"] for f in bd.todos("SELECT estado, COUNT(*) AS n FROM trabajos GROUP BY estado")}
    por_tipo = {}
    for f in bd.todos("SELECT tipo, estado, creado, actualizado, error_codigo FROM trabajos ORDER BY actualizado DESC LIMIT 1000"):
        t = por_tipo.setdefault(f["tipo"], {"completados": 0, "parciales": 0, "fallidos": 0, "cancelados": 0, "duraciones": [], "codigos": {}})
        if f["estado"] in ("completado", "parcial", "fallido", "cancelado"):
            t[{"completado": "completados", "parcial": "parciales", "fallido": "fallidos", "cancelado": "cancelados"}[f["estado"]]] += 1
            try:
                from datetime import datetime
                d = (datetime.fromisoformat(f["actualizado"]) - datetime.fromisoformat(f["creado"])).total_seconds()
                t["duraciones"].append(d)
            except ValueError:
                pass
        if f["error_codigo"]:
            t["codigos"][f["error_codigo"]] = t["codigos"].get(f["error_codigo"], 0) + 1
    for t in por_tipo.values():
        d = sorted(t.pop("duraciones"))
        terminados = t["completados"] + t["parciales"] + t["fallidos"]
        t["tasa_exito"] = round((t["completados"] + t["parciales"]) / terminados, 3) if terminados else None
        t["duracion_s"] = {"p50": round(statistics.median(d), 1), "p95": round(d[min(len(d) - 1, int(len(d) * 0.95))], 1)} if d else None
    return {"por_estado": estados, "pendientes": estados.get("pendiente", 0), "en_curso": estados.get("procesando", 0),
            "por_tipo": por_tipo}


def tamano_datos_mb() -> float:
    from app.core import contexto
    total = 0
    for raiz, _, archivos in os.walk(contexto.obtener().data_dir):
        for a in archivos:
            try:
                total += os.path.getsize(os.path.join(raiz, a))
            except OSError:
                pass
    return round(total / (1024 * 1024), 1)


def memoria_mb() -> float | None:
    try:
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    except Exception:  # noqa: BLE001 — en Windows no existe resource
        return None
