"""API HTTP del servidor IA (BACK-35). Contrato: fullstack/docs/servidor-ia.md §3.

    GET  /salud                 vivo (sin datos sensibles)
    GET  /listo                 Ollama, modelo, disco y GPU → 200 listo / 503 no listo
    GET  /api/v1/capacidades    tareas, formatos, límites y modelo
    POST /api/v1/analisis       ?tarea=… con la imagen como cuerpo binario (no multipart)

La imagen se envía como cuerpo binario y se lee por trozos con límite: así nunca se escribe en
disco (multipart guarda en archivos temporales los cuerpos grandes) y un cuerpo enorme se corta
sin leerlo entero.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ia_servidor import API_VERSION
from ia_servidor.config import Configuracion
from ia_servidor.errores import ErrorIA
from ia_servidor.ollama import ClienteOllama
from ia_servidor.servicio import Servicio

logger = logging.getLogger("apuntia.ia")
CABECERA_ID = "X-ApuntIA-Id-Correlacion"


def crear_app(config: Configuracion | None = None, servicio: Servicio | None = None) -> FastAPI:
    config = config or Configuracion.desde_entorno()
    servicio = servicio or Servicio(config, ClienteOllama(config.ollama_url))
    app = FastAPI(title="ApuntIA — servidor IA", version=API_VERSION, docs_url="/docs", redoc_url=None)
    app.state.servicio = servicio

    @app.middleware("http")
    async def registro(request: Request, siguiente):
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
        # Sin cabeceras, consulta ni cuerpo en el log: solo método, ruta, estado y tiempo.
        logger.info("ia: id=%s %s %s %d %.0fms", id_correlacion, request.method, request.url.path,
                    respuesta.status_code, (time.perf_counter() - inicio) * 1000)
        return respuesta

    @app.exception_handler(ErrorIA)
    async def error_ia(request: Request, e: ErrorIA):
        id_correlacion = getattr(request.state, "id", "-")
        logger.warning("ia: id=%s codigo=%s detalle=%s", id_correlacion, e.codigo, e.detalle)
        cabeceras = {"Retry-After": str(max(5, config.espera_cola_s))} if e.codigo == "OCUPADO" else None
        return JSONResponse(e.cuerpo(id_correlacion), status_code=e.estado, headers=cabeceras)

    @app.exception_handler(StarletteHTTPException)
    async def error_http(request: Request, e: StarletteHTTPException):
        codigo = {404: "RUTA_NO_ENCONTRADA", 405: "METODO_NO_PERMITIDO"}.get(e.status_code, "ERROR_HTTP")
        return JSONResponse({"error": {"codigo": codigo, "mensaje": "Ruta o método no válidos.", "reintentable": False,
                                       "id_correlacion": getattr(request.state, "id", "-")}}, status_code=e.status_code)

    @app.get("/salud")
    def salud():
        return {"estado": "ok", "servicio": "apuntia-ia", "api_version": API_VERSION}

    @app.get("/listo")
    async def listo():
        ok, cuerpo = await run_in_threadpool(servicio.listo)
        return JSONResponse(cuerpo, status_code=200 if ok else 503)

    @app.get("/api/v1/capacidades")
    def capacidades():
        return servicio.capacidades()

    @app.post("/api/v1/analisis")
    async def analisis(request: Request, tarea: str = "pagina"):
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
        datos = b"".join(trozos)
        del trozos
        return await run_in_threadpool(servicio.analizar, datos, tarea, request.state.id)

    return app
