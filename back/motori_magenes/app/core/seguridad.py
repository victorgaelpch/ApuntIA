"""Dependencias de seguridad de la API v2 (BACK-23, BACK-24).

`sesion_actual` resuelve el usuario a partir de la cookie HttpOnly y, en las
peticiones que modifican datos, exige la cabecera X-CSRF-Token y que el origen
(si el navegador lo envía) sea el mismo servidor.
"""

import hmac
from urllib.parse import urlsplit

from fastapi import Request, Response

from app.core import contexto
from app.core.config import settings
from app.core.errores import ApiError
from app.services.cuentas import DURACION_MAXIMA_S, Cuentas, Sesion, Usuario

COOKIE_SESION = "apuntia_sesion"
METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}


def cuentas() -> Cuentas:
    ctx = contexto.obtener()
    return Cuentas(ctx.bd, ctx.data_dir / "buzon")


def comprobar_origen(request: Request) -> None:
    origen = request.headers.get("origin")
    if origen and origen != "null":
        propio = f"{request.url.scheme}://{request.url.netloc}"
        if urlsplit(origen)._replace(path="").geturl().rstrip("/") != propio:
            raise ApiError(403, "ORIGEN_NO_PERMITIDO", "La petición viene de otro sitio y se rechazó.")


def sesion_actual(request: Request) -> Sesion:
    sesion = cuentas().sesion(request.cookies.get(COOKIE_SESION))
    if request.method not in METODOS_SEGUROS:
        comprobar_origen(request)
        enviado = request.headers.get("x-csrf-token", "")
        if not hmac.compare_digest(enviado, sesion.csrf):
            raise ApiError(403, "CSRF_INVALIDO", "La página caducó. Recárgala e inténtalo de nuevo.")
    return sesion


def usuario_actual(request: Request) -> Usuario:
    """Usuario autenticado (con las mismas comprobaciones de CSRF y origen que `sesion_actual`).

    Regla de autorización (BACK-24): toda consulta de un recurso privado filtra por
    `usuario_id = usuario.id` en el servidor. Si el recurso existe pero es de otro
    usuario se responde 404 NO_ENCONTRADO, igual que si no existiera, para no
    revelar qué identificadores existen.
    """
    return sesion_actual(request).usuario


def poner_cookie(response: Response, token: str) -> None:
    response.set_cookie(COOKIE_SESION, token, max_age=DURACION_MAXIMA_S, httponly=True,
                        secure=settings.cookie_segura, samesite="lax", path="/")


def quitar_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_SESION, path="/", httponly=True, samesite="lax", secure=settings.cookie_segura)
