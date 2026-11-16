"""Conexión con el servidor IA remoto (FULL-31). Guía: fullstack/docs/conexion-remota.md.

    GET    /api/v2/ia/estado         cualquier usuario con sesión: modo, URL, vinculado (nunca el token)
    PUT    /api/v2/ia/configuracion  {modo: auto|manual|local, url}: cómo usar el servidor IA  [local]
    POST   /api/v2/ia/vinculacion    pide un código para que el administrador lo apruebe      [local]
    GET    /api/v2/ia/vinculacion    comprueba si ya se aprobó (guarda la credencial cifrada) [local]
    DELETE /api/v2/ia/vinculacion    borra la credencial de este equipo                        [local]
    GET    /api/v2/ia/diagnostico    DNS, TLS, versión, credencial, modelo y GPU, con soluciones [local]

[local]: solo desde el propio equipo (127.0.0.1), con sesión y cabecera CSRF. Así un alumno
conectado por la red del aula (`iniciar.bat -Red`) no puede cambiar el servidor ni vincular.
Cambiar la URL nunca envía la credencial anterior al servidor nuevo: hay que volver a vincular.
"""

from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.core import contexto
from app.core.config import settings
from app.core.errores import ApiError
from app.core.seguridad import sesion_actual
from app.services.cuentas import Sesion
from app.services.ia_remota import Almacen, ClienteIARemota, ErrorIARemota, url_efectiva, validar_url

router = APIRouter(prefix="/api/v2/ia", tags=["v2: servidor IA remoto"])
LOCALES = {"127.0.0.1", "::1", "localhost"}
ESTADOS_HTTP = {"AI_NO_CONFIGURADO": 409, "AI_URL_INVALIDA": 400, "AI_NO_VINCULADO": 409, "AI_VINCULACION": 409,
                "AI_AUTH": 502, "AI_REVOCADO": 502, "AI_LIMITE": 429, "AI_CIRCUITO_ABIERTO": 503}


class Configuracion(BaseModel):
    modo: Literal["auto", "manual", "local"] = "auto"
    url: str | None = Field(default=None, max_length=300)   # solo con modo «manual»


def cliente() -> ClienteIARemota:
    almacen = Almacen(contexto.obtener().data_dir)
    return ClienteIARemota(url_efectiva(almacen, settings.ia_url), almacen, timeout_s=settings.ia_timeout_s, timeout_analisis_s=settings.ia_timeout_analisis_s)


def solo_local(request: Request, sesion: Sesion = Depends(sesion_actual)) -> Sesion:
    if not request.client or request.client.host not in LOCALES:
        raise ApiError(403, "SOLO_EQUIPO_LOCAL", "Esta acción solo se puede hacer en el propio equipo donde corre ApuntIA.")
    return sesion


def _como_api(e: ErrorIARemota) -> ApiError:
    return ApiError(ESTADOS_HTTP.get(e.codigo, 502), e.codigo, e.mensaje)


@router.get("/estado")
def estado(request: Request, sesion: Sesion = Depends(sesion_actual)):
    # puede_configurar: la petición viene del propio equipo (las acciones [local] están permitidas)
    return {**cliente().estado(), "puede_configurar": bool(request.client and request.client.host in LOCALES)}


@router.put("/configuracion")
def configurar(datos: Configuracion, sesion: Sesion = Depends(solo_local)):
    url = (datos.url or "").strip().rstrip("/") or None
    if datos.modo == "manual":
        motivo = validar_url(url)
        if motivo:
            raise ApiError(400, "AI_URL_INVALIDA", motivo)
    else:
        url = None  # «auto» vuelve a la URL de la instalación; «local» no usa ninguna
    Almacen(contexto.obtener().data_dir).actualizar(modo=datos.modo, url=url)
    return cliente().estado()


@router.post("/vinculacion", status_code=201)
async def iniciar_vinculacion(sesion: Sesion = Depends(solo_local)):
    try:
        r = await run_in_threadpool(cliente().solicitar_vinculacion, "ApuntIA de " + sesion.usuario.nombre)
    except ErrorIARemota as e:
        raise _como_api(e) from None
    return {**r, "instrucciones": "Dicta este código a quien administra la PC del servidor IA. "
                                  "Lo aprueba con: iniciar.bat -Modo dispositivos"}


@router.get("/vinculacion")
async def consultar_vinculacion(sesion: Sesion = Depends(solo_local)):
    try:
        return await run_in_threadpool(cliente().sondear_vinculacion)
    except ErrorIARemota as e:
        raise _como_api(e) from None


@router.delete("/vinculacion")
def desvincular(sesion: Sesion = Depends(solo_local)):
    c = cliente()
    c.desvincular()
    return {**c.estado(), "aviso": "Credencial borrada en este equipo. Para invalidarla también en el servidor, "
                                   "pide al administrador que revoque el dispositivo."}


@router.get("/diagnostico")
async def diagnostico(sesion: Sesion = Depends(solo_local)):
    c = cliente()
    pasos = await run_in_threadpool(c.diagnosticar)
    return {"estado": c.estado(), "pasos": pasos, "ok": all(p["ok"] for p in pasos)}
