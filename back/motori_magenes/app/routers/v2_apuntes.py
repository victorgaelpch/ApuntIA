"""Rutas de apuntes de la API v2. Contrato: docs/api-v2.md §5."""

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from fastapi.responses import JSONResponse, Response

from app.core import contexto
from app.core.seguridad import sesion_actual
from app.datos.almacen import ArchivoNoEncontrado
from app.datos.apuntes import RepositorioApuntes
from app.services.cuentas import Sesion
from app.services.entrada import validar_paginas
from app.core.errores import ApiError

router = APIRouter(prefix="/api/v2", tags=["v2: apuntes"])


def repositorio() -> RepositorioApuntes:
    ctx = contexto.obtener()
    return RepositorioApuntes(ctx.bd, ctx.almacen)


@router.post("/apuntes", status_code=202)
def crear_apunte(
    paginas: list[UploadFile] | None = File(None, description="Fotos en orden (JPEG, PNG o WEBP)"),
    tipos: list[str] | None = Form(None, description="Un tipo por página: pizarron o cuaderno"),
    titulo: str = Form("", max_length=200),
    idempotency_key: str | None = Header(None, max_length=100),
    sesion: Sesion = Depends(sesion_actual),
):
    recibidas = validar_paginas(paginas, tipos)
    apunte, creado = repositorio().crear(sesion.usuario.id, titulo, recibidas, idempotency_key)
    return JSONResponse({"apunte": apunte, "trabajo": None}, status_code=202 if creado else 200)


@router.get("/apuntes/{apunte_id}")
def ver_apunte(apunte_id: str, sesion: Sesion = Depends(sesion_actual)):
    return {"apunte": repositorio().obtener(sesion.usuario.id, apunte_id)}


@router.get("/apuntes/{apunte_id}/archivos/{archivo_id}")
def ver_archivo(apunte_id: str, archivo_id: str, sesion: Sesion = Depends(sesion_actual)):
    repositorio().obtener(sesion.usuario.id, apunte_id, con_documento=False)  # el apunte es suyo
    try:
        archivo = contexto.obtener().almacen.obtener(sesion.usuario.id, archivo_id)
    except ArchivoNoEncontrado:
        raise ApiError(404, "NO_ENCONTRADO", "No encontramos ese archivo.") from None
    if archivo.apunte_id != apunte_id or archivo.tipo == "pdf":
        raise ApiError(404, "NO_ENCONTRADO", "No encontramos ese archivo.")
    return Response(archivo.ruta.read_bytes(), media_type=archivo.mime,
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
