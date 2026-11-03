"""Servicios de procesamiento de imágenes."""

import io

from PIL import Image, ImageDraw


def generar_imagen_ejemplo() -> io.BytesIO:
    """Genera en memoria una imagen PNG de ejemplo."""
    imagen = Image.new("RGB", (300, 100), color="blue")
    dibujo = ImageDraw.Draw(imagen)
    dibujo.text((10, 40), "Hola FastAPI", fill="white")

    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
