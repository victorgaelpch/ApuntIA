"""API HTTP del servidor IA (BACK-35, autenticación FULL-31). Contrato: fullstack/docs/servidor-ia.md §3.

Públicas (sin credencial, sin datos sensibles):
    GET  /salud                                       vivo + api_version
    POST /api/v1/vinculacion/solicitudes              pedir vinculación → código + secreto
    POST /api/v1/vinculacion/solicitudes/{id}/estado  sondear con el secreto → token (una vez)
Con credencial de dispositivo (Authorization: Bearer …):
    GET  /listo                 Ollama, modelo, disco y GPU (sin credencial: solo {"listo": bool})
    GET  /api/v1/yo             qué dispositivo es (comprobar la credencial)
    GET  /api/v1/capacidades    tareas, formatos, límites y modelo
    POST /api/v1/analisis       ?tarea=… con la imagen como cuerpo binario (no multipart)
    POST /api/v1/trabajos       igual, pero asíncrono: 202 + trabajo_id (BACK-37, ver trabajos.py)
    GET/DELETE /api/v1/trabajos/{id}   estado y progreso / cancelar

No hay rutas de administración por HTTP: aprobar y revocar se hace en la consola de la PC del
servidor (`python -m ia_servidor.admin`), porque por el túnel todo llega desde 127.0.0.1.
La imagen se lee por trozos con límite y nunca se escribe en disco.
"""

from __future__ import annotations

import collections
import logging
import threading
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ia_servidor import API_VERSION
from ia_servidor.config import Configuracion, carpeta_datos
from ia_servidor.dispositivos import Autorizado, ErrorVinculacion, Registro
from ia_servidor.errores import ErrorIA
from ia_servidor.ollama import ClienteOllama
from ia_servidor.esquemas import TAREAS_PUBLICAS
from ia_servidor.servicio import Servicio
from ia_servidor.trabajos import ColaTrabajos

logger = logging.getLogger("apuntia.ia")
CABECERA_ID = "X-ApuntIA-Id-Correlacion"
MAX_JSON = 4096  # bytes de las peticiones de vinculación


class PeticionVinculacion(BaseModel):
    dispositivo_id: str = Field(min_length=8, max_length=64)
    nombre: str = Field(default="", max_length=200)


class PeticionSondeo(BaseModel):
    secreto: str = Field(min_length=10, max_length=200)


class Limitador:
    """Ventana deslizante de 60 s por dispositivo (en memoria: se reinicia con el servicio)."""

    def __init__(self, maximo_min: int):
        self.maximo = maximo_min
        self.marcas: dict[str, collections.deque] = collections.defaultdict(collections.deque)
        self.cerrojo = threading.Lock()

    def permitir(self, clave: str) -> bool:
        ahora = time.monotonic()
        with self.cerrojo:
            q = self.marcas[clave]
            while q and ahora - q[0] > 60:
                q.popleft()
            if len(q) >= self.maximo:
                return False
            q.append(ahora)
            return True


def _error(codigo: str, estado: int, mensaje: str, id_correlacion: str, reintentable: bool = False, cabeceras=None):
    return JSONResponse({"error": {"codigo": codigo, "mensaje": mensaje, "reintentable": reintentable,
                                   "id_correlacion": id_correlacion}}, status_code=estado, headers=cabeceras)


def crear_app(config: Configuracion | None = None, servicio: Servicio | None = None,
              registro: Registro | None = None) -> FastAPI:
    config = config or Configuracion.desde_entorno()
    servicio = servicio or Servicio(config, ClienteOllama(config.ollama_url))
    registro = registro or Registro(carpeta_datos(config.datos))
    registro.token_admin()  # se crea al arrancar para las herramientas locales
    limitador = Limitador(config.max_analisis_min)
    cola = ColaTrabajos(servicio, config.max_cola, config.ttl_trabajos_s)
    app = FastAPI(title="ApuntIA — servidor IA", version=API_VERSION, docs_url=None, redoc_url=None,
                  openapi_url=None)  # sin documentación pública: el contrato está en el repositorio
    app.state.servicio, app.state.registro, app.state.cola = servicio, registro, cola

    @app.middleware("http")
    async def registro_peticiones(request: Request, siguiente):
        id_correlacion = uuid.uuid4().hex[:16]
        request.state.id = id_correlacion
        inicio = time.perf_counter()
        try:
            respuesta = await siguiente(request)
        except Exception:  # noqa: BLE001 — nunca se devuelve una traza al cliente
            logger.exception("ia: id=%s error no controlado en %s", id_correlacion, request.url.path)
            respuesta = JSONResponse(ErrorIA("ERROR_INTERNO").cuerpo(id_correlacion), status_code=500)
        respuesta.headers[CABECERA_ID] = id_correlacion
        respuesta.headers["Cache-Control"] = "no-store"
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        # Sin cabeceras (Authorization), consulta ni cuerpo en el log.
        logger.info("ia: id=%s %s %s %d %.0fms", id_correlacion, request.method, request.url.path,
                    respuesta.status_code, (time.perf_counter() - inicio) * 1000)
        return respuesta

    @app.exception_handler(ErrorIA)
    async def error_ia(request: Request, e: ErrorIA):
        id_correlacion = getattr(request.state, "id", "-")
        logger.warning("ia: id=%s codigo=%s detalle=%s", id_correlacion, e.codigo, e.detalle)
        cabeceras = None
        if e.codigo == "OCUPADO" and "cola llena" in e.detalle:
            cabeceras = {"Retry-After": "30"}
        elif e.codigo == "OCUPADO":
            cabeceras = {"Retry-After": str(max(5, config.espera_cola_s))}
        elif e.codigo == "LIMITE_PETICIONES":
            cabeceras = {"Retry-After": "60"}
        return JSONResponse(e.cuerpo(id_correlacion), status_code=e.estado, headers=cabeceras)

    @app.exception_handler(ErrorVinculacion)
    async def error_vinculacion(request: Request, e: ErrorVinculacion):
        id_correlacion = getattr(request.state, "id", "-")
        logger.warning("ia: id=%s codigo=%s", id_correlacion, e.codigo)
        return _error(e.codigo, e.estado, e.mensaje, id_correlacion, reintentable=e.estado in (429, 503),
                      cabeceras={"Retry-After": "60"} if e.estado == 429 else None)

    @app.exception_handler(StarletteHTTPException)
    async def error_http(request: Request, e: StarletteHTTPException):
        codigo = {404: "RUTA_NO_ENCONTRADA", 405: "METODO_NO_PERMITIDO"}.get(e.status_code, "ERROR_HTTP")
        return _error(codigo, e.status_code, "Ruta o método no válidos.", getattr(request.state, "id", "-"))

    def autorizar(request: Request) -> Autorizado:
        return registro.autorizar(request.headers.get("authorization"))

    async def json_acotado(request: Request, modelo):
        cuerpo = await request.body()
        if len(cuerpo) > MAX_JSON:
            raise ErrorVinculacion("DATOS_INVALIDOS", 413, "Petición demasiado grande.")
        try:
            return modelo.model_validate_json(cuerpo)
        except ValidationError:
            raise ErrorVinculacion("DATOS_INVALIDOS", 400, "Datos de vinculación no válidos.") from None

    # ------------------------------------------------------------------ públicas
    @app.get("/salud")
    def salud():
        return {"estado": "ok", "servicio": "apuntia-ia", "api_version": API_VERSION}

    @app.post("/api/v1/vinculacion/solicitudes", status_code=201)
    async def solicitar(request: Request):
        datos = await json_acotado(request, PeticionVinculacion)
        r = await run_in_threadpool(registro.solicitar, datos.dispositivo_id, datos.nombre)
        logger.info("ia: id=%s solicitud de vinculación creada (código no se registra)", request.state.id)
        return {**r, "instrucciones": "Dile este código a quien administra el servidor IA para que lo apruebe."}

    @app.post("/api/v1/vinculacion/solicitudes/{solicitud_id}/estado")
    async def sondear(solicitud_id: str, request: Request):
        datos = await json_acotado(request, PeticionSondeo)
        return await run_in_threadpool(registro.sondear, solicitud_id[:64], datos.secreto)

    # ------------------------------------------------------------------ con credencial
    @app.get("/listo")
    async def listo(request: Request):
        ok, cuerpo = await run_in_threadpool(servicio.listo)
        try:
            await run_in_threadpool(autorizar, request)
        except ErrorVinculacion:
            cuerpo = {"listo": ok, "api_version": API_VERSION}  # sin credencial: nada del equipo
        return JSONResponse(cuerpo, status_code=200 if ok else 503)

    @app.get("/api/v1/yo")
    async def yo(request: Request):
        a = await run_in_threadpool(autorizar, request)
        return {"dispositivo_id": a.dispositivo_id, "nombre": a.nombre, "api_version": API_VERSION}

    @app.get("/api/v1/capacidades")
    async def capacidades(request: Request):
        await run_in_threadpool(autorizar, request)
        return servicio.capacidades()

    async def leer_imagen(request: Request) -> bytes:
        limite = config.max_mb * 1024 * 1024
        declarado = request.headers.get("content-length")
        if declarado and declarado.isdigit() and int(declarado) > limite:
            raise ErrorIA("IMAGEN_DEMASIADO_GRANDE", f"Content-Length {declarado}")
        tipo = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if tipo.startswith("multipart/"):
            raise ErrorIA("FALTA_IMAGEN", "se espera el cuerpo binario de la imagen, no multipart")
        trozos, total = [], 0
        async for trozo in request.stream():
            total += len(trozo)
            if total > limite:
                raise ErrorIA("IMAGEN_DEMASIADO_GRANDE", f"más de {limite} bytes")
            trozos.append(trozo)
        return b"".join(trozos)

    async def autorizar_analisis(request: Request) -> Autorizado:
        a = await run_in_threadpool(autorizar, request)
        if not a.admin and not limitador.permitir(a.dispositivo_id):
            raise ErrorIA("LIMITE_PETICIONES", f"dispositivo {a.dispositivo_id[:8]}")
        return a

    @app.post("/api/v1/analisis")
    async def analisis(request: Request, tarea: str = "pagina"):
        await autorizar_analisis(request)
        datos = await leer_imagen(request)
        return await run_in_threadpool(servicio.analizar, datos, tarea, request.state.id)

    # ------------------------------------------------------------------ trabajos asíncronos (BACK-37)
    @app.post("/api/v1/trabajos", status_code=202)
    async def crear_trabajo(request: Request, tarea: str = "documento"):
        a = await autorizar_analisis(request)
        if tarea not in TAREAS_PUBLICAS:
            raise ErrorIA("TAREA_INVALIDA", tarea[:40])
        clave = (request.headers.get("idempotency-key") or "")[:100] or None
        datos = await leer_imagen(request)
        t, nuevo = cola.encolar(a.dispositivo_id, tarea, datos, clave)
        _, posicion = cola.obtener(a.dispositivo_id, t.id)
        return JSONResponse(t.publico(posicion), status_code=202 if nuevo else 200)

    @app.get("/api/v1/trabajos/{trabajo_id}")
    async def ver_trabajo(trabajo_id: str, request: Request):
        a = await run_in_threadpool(autorizar, request)
        t, posicion = cola.obtener(a.dispositivo_id, trabajo_id[:64])
        return t.publico(posicion)

    @app.delete("/api/v1/trabajos/{trabajo_id}")
    async def cancelar_trabajo(trabajo_id: str, request: Request):
        a = await run_in_threadpool(autorizar, request)
        return cola.cancelar(a.dispositivo_id, trabajo_id[:64]).publico()

    return app
