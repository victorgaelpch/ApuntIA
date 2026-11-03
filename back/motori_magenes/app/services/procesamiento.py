"""Servicios de procesamiento de imágenes."""

import io
from pathlib import Path

from PIL import Image, ImageDraw


def convertir_a_grises(ruta: Path) -> Path:
    """Convierte la imagen ubicada en ``ruta`` a escala de grises (in situ)."""
    with Image.open(ruta) as imagen:
        imagen_gris = imagen.convert("L")
    imagen_gris.save(ruta)
    return ruta


def generar_imagen_ejemplo() -> io.BytesIO:
    """Genera en memoria una imagen PNG de ejemplo."""
    imagen = Image.new("RGB", (300, 100), color="blue")
    dibujo = ImageDraw.Draw(imagen)
    dibujo.text((10, 40), "Hola FastAPI", fill="white")

    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
