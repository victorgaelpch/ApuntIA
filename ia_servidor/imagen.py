"""Validación de la imagen recibida y diagnóstico de calidad (BACK-35).

La validación es propia porque la del backend (`app/services/validacion.py`) depende de su
configuración y de `UploadFile`; aquí todo es en memoria y sin archivos temporales:

1. bytes > 0 y ≤ IA_MAX_MB (el cuerpo se lee con límite, no entero);
2. formato por firma binaria (JPEG, PNG, WEBP), no por extensión ni Content-Type;
3. dimensiones leídas de la CABECERA antes de decodificar → rechaza «bombas de descompresión»;
4. decodificación real con OpenCV.

El diagnóstico de calidad y la detección de la hoja reutilizan `calidad.py` y `perspectiva.py`
del backend (OpenCV puro, sin base de datos ni configuración): ver `compartido.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from ia_servidor.errores import ErrorIA

FIRMAS = (
    (b"\xff\xd8\xff", "jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)


def formato_por_firma(datos: bytes) -> str | None:
    for firma, nombre in FIRMAS:
        if datos.startswith(firma):
            return nombre
    if len(datos) >= 12 and datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        return "webp"
    return None


@dataclass
class ImagenValida:
    formato: str
    ancho: int
    alto: int
    bytes: int
    imagen: np.ndarray  # BGR uint8


def validar(datos: bytes, max_mb: int, max_megapixeles: int) -> ImagenValida:
    if not datos:
        raise ErrorIA("IMAGEN_VACIA")
    if len(datos) > max_mb * 1024 * 1024:
        raise ErrorIA("IMAGEN_DEMASIADO_GRANDE", f"{len(datos)} bytes")
    formato = formato_por_firma(datos)
    if formato is None:
        raise ErrorIA("FORMATO_NO_SOPORTADO")
    try:
        with Image.open(BytesIO(datos)) as cabecera:  # solo lee la cabecera, no los píxeles
            ancho, alto = cabecera.size
    except Image.DecompressionBombError:  # Pillow ya la reconoce por la cabecera
        raise ErrorIA("RESOLUCION_EXCESIVA", "bomba de descompresión") from None
    except (UnidentifiedImageError, OSError):
        raise ErrorIA("IMAGEN_CORRUPTA", "cabecera ilegible") from None
    if ancho <= 0 or alto <= 0:
        raise ErrorIA("IMAGEN_CORRUPTA", "dimensiones nulas")
    if ancho * alto > max_megapixeles * 1_000_000:
        raise ErrorIA("RESOLUCION_EXCESIVA", f"{ancho}x{alto}")
    imagen = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
    if imagen is None or imagen.size == 0:
        raise ErrorIA("IMAGEN_CORRUPTA", "no decodifica")
    return ImagenValida(formato, int(imagen.shape[1]), int(imagen.shape[0]), len(datos), imagen)


def reducir(imagen: np.ndarray, max_lado: int) -> np.ndarray:
    """Copia reducida para el modelo; la original no se modifica."""
    lado = max(imagen.shape[:2])
    if lado <= max_lado:
        return imagen
    escala = max_lado / lado
    return cv2.resize(imagen, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)
