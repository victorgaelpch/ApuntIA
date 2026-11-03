"""Rutas relacionadas con el procesamiento de imágenes.

Las rutas solo traducen HTTP <-> funciones: la validación vive en
services/validacion.py y el procesamiento en services/procesamiento.py.
"""

import logging
import time
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import Response, StreamingResponse

from app.services.procesamiento import (
    OpcionesProcesamiento,
    codificar_png,
    generar_imagen_ejemplo,
    procesar,
)
from app.services.validacion import validar_imagen

logger = logging.getLogger(__name__)

router = APIRouter(tags=["imagenes"])


@router.post(
    "/analisis",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}, "description": "Imagen procesada"}},
)
def motori_magenes(
    file: UploadFile | None = File(None, description="Foto del pizarrón (JPEG, PNG o WEBP)"),
    grises: bool = Query(False, description="Devolver el resultado en escala de grises"),
):
    """Recibe una foto del pizarrón (campo «file»), la valida y la devuelve procesada."""
    inicio = time.perf_counter()
    recibida = validar_imagen(file)

    opciones = OpcionesProcesamiento(grises=grises)
    resultado = procesar(recibida.imagen, opciones)
    png = codificar_png(resultado.imagen)

    total_ms = (time.perf_counter() - inicio) * 1000
    alto, ancho = resultado.imagen.shape[:2]
    logger.info("Procesada %s (%dx%d) en %.0f ms; etapas: %s", recibida.nombre, ancho, alto,
                total_ms, {k: round(v, 1) for k, v in resultado.tiempos_ms.items()})

    nombre_salida = f"{Path(recibida.nombre).stem}_apuntia.png"
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(nombre_salida)}",
            "X-ApuntIA-Archivo": quote(recibida.nombre),
            "X-ApuntIA-Perspectiva": resultado.perspectiva,
            "X-ApuntIA-Dimensiones": f"{ancho}x{alto}",
            "X-ApuntIA-Tiempo-Ms": str(round(total_ms)),
        },
    )


@router.post("/imagen-memoria")
def obtener_imagen_memoria():
    """Devuelve una imagen de ejemplo generada en memoria."""
    return StreamingResponse(generar_imagen_ejemplo(), media_type="image/png")
