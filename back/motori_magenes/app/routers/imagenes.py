"""Rutas relacionadas con el procesamiento de imágenes."""

import logging

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from app.services.almacenamiento import guardar_archivo
from app.services.procesamiento import convertir_a_grises, generar_imagen_ejemplo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["imagenes"])


@router.post("/analisis")
def motori_magenes(file: UploadFile = File(...)):
    """Recibe una imagen, la convierte a escala de grises y la devuelve."""
    logger.info("Nombre del archivo: %s", file.filename)
    ruta_archivo = guardar_archivo(file)
    convertir_a_grises(ruta_archivo)
    return FileResponse(
        ruta_archivo, media_type="image/png", filename=ruta_archivo.name
    )


@router.post("/imagen-memoria")
def obtener_imagen_memoria():
    """Devuelve una imagen de ejemplo generada en memoria."""
    return StreamingResponse(generar_imagen_ejemplo(), media_type="image/png")
