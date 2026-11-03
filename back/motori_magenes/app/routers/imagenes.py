"""Rutas relacionadas con el procesamiento de imágenes."""

import logging
from pathlib import Path
from urllib.parse import quote

import cv2
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response, StreamingResponse

from app.services.procesamiento import generar_imagen_ejemplo
from app.services.validacion import validar_imagen

logger = logging.getLogger(__name__)

router = APIRouter(tags=["imagenes"])


@router.post(
    "/analisis",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}, "description": "Imagen procesada"}},
)
def motori_magenes(file: UploadFile | None = File(None)):
    """Recibe una foto del pizarrón (campo «file»), la valida y la devuelve procesada."""
    recibida = validar_imagen(file)
    logger.info("Imagen recibida: %s (%s, %d bytes)", recibida.nombre, recibida.formato, len(recibida.datos))

    gris = cv2.cvtColor(recibida.imagen, cv2.COLOR_BGR2GRAY)
    _, png = cv2.imencode(".png", gris)

    nombre_salida = f"{Path(recibida.nombre).stem}_apuntia.png"
    return Response(
        content=png.tobytes(),
        media_type="image/png",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(nombre_salida)}",
            "X-ApuntIA-Archivo": quote(recibida.nombre),
        },
    )


@router.post("/imagen-memoria")
def obtener_imagen_memoria():
    """Devuelve una imagen de ejemplo generada en memoria."""
    return StreamingResponse(generar_imagen_ejemplo(), media_type="image/png")
