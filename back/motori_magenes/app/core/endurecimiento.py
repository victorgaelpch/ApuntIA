"""Endurecimiento transversal de la API (BACK-24). Guía: docs/seguridad-api.md.

  - `CabecerasSeguridad`: nosniff, sin marcos, sin Referer, sin caché para los
    datos privados de /api/v2 y una CSP que no permite ejecutar nada en las
    respuestas de la API.
  - `LimiteCuerpo` (solo /api/v2): rechaza con 413 los cuerpos demasiado grandes ANTES de leerlos
    (por Content-Length) y también los enviados por trozos (contando bytes).
  - `limitar()`: límite de frecuencia por clave (IP o usuario) guardado en SQLite,
    así sobrevive a reinicios y vale con varios hilos.
  - `comprobar_cuota()`: espacio máximo por usuario.
"""

import json
import time

from app.core import contexto
from app.core.config import settings
from app.core.errores import ApiError

CABECERAS_COMUNES = {
    b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY",
    b"referrer-policy": b"no-referrer",
    b"cross-origin-opener-policy": b"same-origin",
}
CABECERAS_API_PRIVADA = {
    b"cache-control": b"private, no-store",
    b"content-security-policy": b"default-src 'none'; frame-ancestors 'none'; sandbox",
}
METODOS_CON_CUERPO = {"POST", "PUT", "PATCH", "DELETE"}


class CabecerasSeguridad:
    """Middleware ASGI: añade las cabeceras sin pisar las que ya puso la ruta."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        privada = scope["path"].startswith("/api/v2/")

        async def enviar(mensaje):
            if mensaje["type"] == "http.response.start":
                presentes = {k.lower() for k, _ in mensaje.get("headers", [])}
                extra = dict(CABECERAS_COMUNES)
                if privada:
                    extra.update(CABECERAS_API_PRIVADA)
                if settings.cookie_segura:  # solo detrás de HTTPS
                    extra[b"strict-transport-security"] = b"max-age=31536000"
                mensaje["headers"] = list(mensaje.get("headers", [])) + \
                    [(k, v) for k, v in extra.items() if k not in presentes]
            await send(mensaje)

        await self.app(scope, receive, enviar)


def limite_cuerpo(path: str, content_type: str) -> int:
    """Bytes máximos admitidos para una petición."""
    if content_type.startswith("multipart/"):
        return int(settings.max_upload_mb * settings.max_paginas * 1024 * 1024) + 256 * 1024
    return settings.max_json_kb * 1024


class _CuerpoGrande(Exception):
    pass


async def _responder_413(send, maximo: int) -> None:
    cuerpo = json.dumps({"error": {"codigo": "CARGA_DEMASIADO_GRANDE",
                                   "mensaje": f"La petición supera el máximo de {maximo // (1024 * 1024) or 1} MB."}},
                        ensure_ascii=False).encode()
    await send({"type": "http.response.start", "status": 413,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(cuerpo)).encode()),
                            (b"connection", b"close")]})
    await send({"type": "http.response.body", "body": cuerpo})


class LimiteCuerpo:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Solo /api/v2: el endpoint v1 /analisis conserva su contrato (413
        # ARCHIVO_DEMASIADO_GRANDE con su propio mensaje) y su lectura limitada.
        if (scope["type"] != "http" or scope["method"] not in METODOS_CON_CUERPO
                or not scope["path"].startswith("/api/v2/")):
            await self.app(scope, receive, send)
            return
        cabeceras = dict(scope.get("headers", []))
        maximo = limite_cuerpo(scope["path"], cabeceras.get(b"content-type", b"").decode("latin-1").lower())
        declarado = cabeceras.get(b"content-length")
        if declarado is not None:
            try:
                if int(declarado) > maximo:
                    await _responder_413(send, maximo)
                    return
            except ValueError:
                await _responder_413(send, maximo)
                return
        recibidos = 0
        excedido = iniciada = False

        async def recibir():
            nonlocal recibidos, excedido
            mensaje = await receive()
            if mensaje["type"] == "http.request":
                recibidos += len(mensaje.get("body", b""))
                if recibidos > maximo:
                    excedido = True
                    raise _CuerpoGrande
            return mensaje

        async def enviar(mensaje):
            # FastAPI convierte cualquier fallo al leer el cuerpo en un 400; si el
            # cuerpo se pasó del límite se descarta esa respuesta y se envía el 413.
            nonlocal iniciada
            if not excedido:
                iniciada = iniciada or mensaje["type"] == "http.response.start"
                await send(mensaje)

        try:
            await self.app(scope, recibir, enviar)
        except _CuerpoGrande:
            pass
        if excedido and not iniciada:
            await _responder_413(send, maximo)


# ------------------------------------------------------------------ límites de frecuencia

LIMITES = {  # acción → (máximo, ventana en segundos)
    "registro": (10, 3600),           # por IP
    "recuperacion_ip": (10, 3600),    # por IP
    "recuperacion_email": (3, 3600),  # por email (no revela si existe)
    "subida": (30, 3600),             # apuntes creados por usuario
    "formulas": (120, 60),            # vistas previas (mathtext usa CPU) por usuario
}


def limitar(accion: str, clave: str) -> None:
    """Cuenta un uso y lanza 429 DEMASIADAS_PETICIONES si se supera el límite."""
    maximo, ventana = LIMITES[accion]
    bd = contexto.obtener().bd
    ahora_s = time.time()
    id_clave = f"lim:{accion}:{clave}"
    with bd.transaccion() as con:
        con.execute("DELETE FROM intentos_login WHERE clave = ? AND momento < ?", (id_clave, ahora_s - ventana))
        con.execute("DELETE FROM intentos_login WHERE clave LIKE 'lim:%' AND momento < ?", (ahora_s - 86400,))
        usados = con.execute("SELECT COUNT(*) FROM intentos_login WHERE clave = ?", (id_clave,)).fetchone()[0]
        if usados >= maximo:
            raise ApiError(429, "DEMASIADAS_PETICIONES",
                           "Has hecho demasiadas peticiones seguidas. Espera un poco e inténtalo de nuevo.")
        con.execute("INSERT INTO intentos_login VALUES (?, ?)", (id_clave, ahora_s))


def comprobar_cuota(usuario_id: str, nuevos_bytes: int) -> None:
    usados = contexto.obtener().bd.uno("SELECT COALESCE(SUM(tamano), 0) AS n FROM archivos WHERE usuario_id = ?",
                                       (usuario_id,))["n"]
    if usados + nuevos_bytes > settings.cuota_mb_usuario * 1024 * 1024:
        raise ApiError(413, "CUOTA_EXCEDIDA",
                       f"Tu espacio ({settings.cuota_mb_usuario} MB) está lleno. Borra apuntes antiguos para subir más.")
