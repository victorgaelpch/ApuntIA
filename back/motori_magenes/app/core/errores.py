"""Manejo de errores de la API (BACK-07).

Todas las respuestas de error usan la estructura acordada en docs/api.md:

    {"error": {"codigo": "TIPO_NO_PERMITIDO", "mensaje": "..."}}

- Errores del cliente (4xx): `codigo` y `mensaje` explican qué corregir.
- Errores del servidor (5xx): mensaje genérico. El detalle técnico y la traza
  solo se escriben en el log del servidor, junto con un identificador que
  también se devuelve en la cabecera X-ApuntIA-Error-Id para poder rastrearlo.
"""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("apuntia.errores")


class ApiError(Exception):
    """Error previsto que se devuelve al cliente con un código estable."""

    def __init__(self, status_code: int, codigo: str, mensaje: str):
        super().__init__(mensaje)
        self.status_code = status_code
        self.codigo = codigo
        self.mensaje = mensaje


class ProcesamientoError(Exception):
    """Fallo dentro del pipeline de OpenCV. Se responde con 500 ERROR_PROCESAMIENTO."""


MENSAJES_HTTP = {
    404: ("RUTA_NO_ENCONTRADA", "La ruta solicitada no existe."),
    405: ("METODO_NO_PERMITIDO", "Método HTTP no permitido en esta ruta."),
}


def respuesta_error(status_code: int, codigo: str, mensaje: str,
                    headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"codigo": codigo, "mensaje": mensaje}},
        headers=headers,
    )


async def manejar_api_error(_: Request, exc: ApiError) -> JSONResponse:
    logger.info("Petición rechazada: %s %s", exc.status_code, exc.codigo)
    respuesta = respuesta_error(exc.status_code, exc.codigo, exc.mensaje)
    detalles = getattr(exc, "detalles", None)
    if detalles:  # campo adicional (p. ej. qué páginas fallaron); la estructura base no cambia
        import json
        cuerpo = json.loads(respuesta.body)
        cuerpo["error"]["detalles"] = detalles
        respuesta = JSONResponse(status_code=exc.status_code, content=cuerpo)
    return respuesta


async def manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    campos = sorted({str(e.get("loc", ["?"])[-1]) for e in exc.errors()})
    if request.url.path.startswith("/api/v2/"):
        # API v2: los datos del cuerpo inválidos son un 400 (docs/api-v2.md §6).
        return respuesta_error(400, "DATOS_INVALIDOS",
                               f"Revisa estos campos: {', '.join(campos)}.")
    return respuesta_error(
        422, "PARAMETRO_INVALIDO",
        f"Valor no válido en: {', '.join(campos)}. Revisa los parámetros de la petición.",
    )


async def manejar_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    codigo, mensaje = MENSAJES_HTTP.get(
        exc.status_code,
        ("ERROR_CLIENTE" if exc.status_code < 500 else "ERROR_INTERNO",
         "La petición no se pudo completar."),
    )
    return respuesta_error(exc.status_code, codigo, mensaje, headers=getattr(exc, "headers", None))


def _error_servidor(request: Request, exc: Exception, codigo: str, mensaje: str) -> JSONResponse:
    error_id = uuid.uuid4().hex[:12]
    logger.error("Error %s en %s %s (id=%s)", codigo, request.method, request.url.path,
                 error_id, exc_info=exc)
    return respuesta_error(500, codigo, mensaje, headers={"X-ApuntIA-Error-Id": error_id})


async def manejar_procesamiento(request: Request, exc: ProcesamientoError) -> JSONResponse:
    return _error_servidor(request, exc, "ERROR_PROCESAMIENTO",
                           "No se pudo procesar la imagen. Inténtalo de nuevo o prueba con otra foto.")


async def manejar_inesperado(request: Request, exc: Exception) -> JSONResponse:
    return _error_servidor(request, exc, "ERROR_INTERNO",
                           "Ocurrió un error inesperado en el servidor. Inténtalo más tarde.")


class CapturarErroresInesperados:
    """Middleware ASGI que convierte las excepciones no previstas en un 500 JSON.

    Corrige el defecto D1 (FULL-08): Starlette ejecuta el manejador de
    `Exception` en ServerErrorMiddleware, que está FUERA de CORSMiddleware. Así,
    el 500 salía sin Access-Control-Allow-Origin, el navegador lo bloqueaba y la
    interfaz mostraba «sin conexión». Este middleware se registra antes que
    CORS (y por tanto queda dentro de él), de modo que el 500 sí lleva las
    cabeceras CORS.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        respuesta_iniciada = False

        async def enviar(mensaje):
            nonlocal respuesta_iniciada
            if mensaje["type"] == "http.response.start":
                respuesta_iniciada = True
            await send(mensaje)

        try:
            await self.app(scope, receive, enviar)
        except Exception as exc:  # noqa: BLE001 — es precisamente el último recurso
            if respuesta_iniciada:
                raise  # ya no se puede cambiar la respuesta
            respuesta = _error_servidor(Request(scope), exc, "ERROR_INTERNO",
                                        "Ocurrió un error inesperado en el servidor. Inténtalo más tarde.")
            await respuesta(scope, receive, send)


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, manejar_api_error)
    app.add_exception_handler(RequestValidationError, manejar_validacion)
    app.add_exception_handler(StarletteHTTPException, manejar_http)
    app.add_exception_handler(ProcesamientoError, manejar_procesamiento)
    app.add_exception_handler(Exception, manejar_inesperado)
