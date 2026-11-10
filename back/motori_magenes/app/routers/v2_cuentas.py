"""Rutas de autenticación y perfil de la API v2 (BACK-23). Contrato: docs/api-v2.md §4."""

import hashlib

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from app.core.endurecimiento import limitar
from app.core.seguridad import (COOKIE_SESION, comprobar_origen, cuentas, poner_cookie, quitar_cookie,
                                sesion_actual)
from app.services.cuentas import Sesion

router = APIRouter(prefix="/api/v2", tags=["v2: cuenta"])


class Registro(BaseModel):
    email: str = Field(max_length=320)
    nombre: str = Field(max_length=80)
    password: str = Field(max_length=256)


class Credenciales(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=256)


class SolicitudRecuperacion(BaseModel):
    email: str = Field(max_length=320)


class ConfirmacionRecuperacion(BaseModel):
    token: str = Field(max_length=200)
    password: str = Field(max_length=256)


class CambioPassword(BaseModel):
    actual: str = Field(max_length=256)
    nueva: str = Field(max_length=256)


class CambioPerfil(BaseModel):
    nombre: str | None = Field(default=None, max_length=80)
    preferencias: dict | None = None


class BorrarCuenta(BaseModel):
    password: str = Field(max_length=256)


def _ip(request: Request) -> str:
    return request.client.host if request.client else "desconocida"


def _respuesta_sesion(sesion: Sesion) -> dict:
    return {"usuario": sesion.usuario.publico(), "csrf": sesion.csrf}


@router.post("/auth/registro", status_code=201)
def registrar(datos: Registro, request: Request, response: Response):
    comprobar_origen(request)
    limitar("registro", _ip(request))
    servicio = cuentas()
    usuario = servicio.registrar(datos.email, datos.nombre, datos.password)
    sesion = servicio.crear_sesion(usuario.id)
    poner_cookie(response, sesion.token)
    return _respuesta_sesion(sesion)


@router.post("/auth/sesion")
def iniciar_sesion(datos: Credenciales, request: Request, response: Response):
    comprobar_origen(request)
    sesion = cuentas().iniciar_sesion(datos.email, datos.password, _ip(request))
    poner_cookie(response, sesion.token)
    return _respuesta_sesion(sesion)


@router.get("/auth/sesion")
def sesion_vigente(request: Request):
    return _respuesta_sesion(cuentas().sesion(request.cookies.get(COOKIE_SESION)))


@router.delete("/auth/sesion", status_code=204)
def cerrar_sesion(request: Request, response: Response, sesion: Sesion = Depends(sesion_actual)):
    cuentas().cerrar_sesion(sesion.token)
    quitar_cookie(response)


@router.post("/auth/recuperacion", status_code=202)
def solicitar_recuperacion(datos: SolicitudRecuperacion, request: Request):
    comprobar_origen(request)
    limitar("recuperacion_ip", _ip(request))
    limitar("recuperacion_email", hashlib.sha256(datos.email.strip().lower().encode()).hexdigest())
    cuentas().solicitar_recuperacion(datos.email, str(request.base_url) + "app/cuenta.html")
    return {"mensaje": "Si existe una cuenta con ese email, recibirás un enlace para recuperarla."}


@router.post("/auth/recuperacion/confirmar", status_code=204)
def confirmar_recuperacion(datos: ConfirmacionRecuperacion, request: Request, response: Response):
    comprobar_origen(request)
    cuentas().confirmar_recuperacion(datos.token, datos.password)
    quitar_cookie(response)


@router.put("/auth/password", status_code=204)
def cambiar_password(datos: CambioPassword, sesion: Sesion = Depends(sesion_actual)):
    cuentas().cambiar_password(sesion, datos.actual, datos.nueva)


@router.get("/perfil")
def ver_perfil(sesion: Sesion = Depends(sesion_actual)):
    return {"usuario": sesion.usuario.publico()}


@router.patch("/perfil")
def cambiar_perfil(datos: CambioPerfil, sesion: Sesion = Depends(sesion_actual)):
    usuario = cuentas().actualizar_perfil(sesion.usuario.id, datos.nombre, datos.preferencias)
    return {"usuario": usuario.publico()}


@router.delete("/perfil", status_code=204)
def borrar_cuenta(datos: BorrarCuenta, response: Response, sesion: Sesion = Depends(sesion_actual)):
    from app.core import contexto
    cuentas().borrar_cuenta(sesion, datos.password)
    contexto.obtener().almacen.borrar_de_usuario(sesion.usuario.id)
    quitar_cookie(response)
