"""Validación de las imágenes recibidas (BACK-02).

Comprueba, en este orden: presencia del archivo, que no esté vacío, el tamaño
máximo, el formato por su firma binaria (no por la extensión ni por el
Content-Type) y que el contenido se pueda decodificar. Todo ocurre en memoria;
no se escriben archivos temporales.
"""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.errores import ApiError

FORMATOS_PERMITIDOS = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


@dataclass
class ImagenRecibida:
    nombre: str
    formato: str  # "jpeg" | "png" | "webp"
    datos: bytes
    imagen: np.ndarray  # BGR, uint8


def nombre_seguro(nombre: str | None) -> str:
    """Quita componentes de ruta y caracteres de control del nombre recibido."""
    limpio = Path((nombre or "").replace("\\", "/")).name
    limpio = "".join(c for c in limpio if c.isprintable() and c not in '"')
    return limpio[:150] or "imagen"


def detectar_formato(datos: bytes) -> str | None:
    """Identifica JPEG, PNG o WEBP a partir de los primeros bytes."""
    if datos.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(datos) >= 12 and datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        return "webp"
    return None


def _leer_con_limite(file: UploadFile, limite_bytes: int) -> bytes:
    """Lee como máximo limite_bytes + 1 para detectar el exceso sin cargar todo."""
    return file.file.read(limite_bytes + 1)


def validar_imagen(file: UploadFile | None) -> ImagenRecibida:
    if file is None:
        raise ApiError(400, "ARCHIVO_AUSENTE",
                       "No se recibió ninguna imagen. Envía el archivo en el campo «file».")

    limite = int(settings.max_upload_mb * 1024 * 1024)
    datos = _leer_con_limite(file, limite)

    if not datos:
        raise ApiError(400, "ARCHIVO_VACIO", "El archivo está vacío. Elige otra imagen.")
    if len(datos) > limite:
        raise ApiError(413, "ARCHIVO_DEMASIADO_GRANDE",
                       f"La imagen pesa más de {settings.max_upload_mb:g} MB. Elige una más ligera.")

    formato = detectar_formato(datos)
    if formato is None:
        raise ApiError(415, "TIPO_NO_PERMITIDO",
                       "Formato no admitido. Usa una imagen JPEG, PNG o WEBP.")

    # Se leen las dimensiones de la cabecera antes de decodificar, para no
    # reservar memoria con imágenes enormes ("bombas de descompresión").
    try:
        with Image.open(BytesIO(datos)) as cabecera:
            ancho, alto = cabecera.size
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ApiError(400, "IMAGEN_CORRUPTA",
                       "No se pudo leer la imagen; puede estar dañada. Elige otra.")

    if ancho * alto > settings.max_megapixeles * 1_000_000:
        raise ApiError(413, "IMAGEN_DEMASIADO_GRANDE",
                       f"La imagen supera los {settings.max_megapixeles:g} megapíxeles. "
                       "Usa una de menor resolución.")

    imagen = cv2.imdecode(np.frombuffer(datos, dtype=np.uint8), cv2.IMREAD_COLOR)
    if imagen is None or imagen.size == 0:
        raise ApiError(400, "IMAGEN_CORRUPTA",
                       "No se pudo leer la imagen; puede estar dañada. Elige otra.")

    return ImagenRecibida(
        nombre=nombre_seguro(file.filename),
        formato=formato,
        datos=datos,
        imagen=imagen,
    )
