"""Pipeline de procesamiento de imágenes con OpenCV (BACK-03).

Las funciones de este módulo no dependen de FastAPI: reciben y devuelven
matrices de NumPy (BGR, uint8), así que pueden reutilizarse desde scripts,
pruebas o un futuro procesamiento por lotes.

Orden de las etapas (cada una se puede desactivar con OpcionesProcesamiento):

    1. copia        -> el original nunca se modifica
    2. perspectiva  -> detecta el pizarrón y lo endereza (BACK-04)
    3. grises       -> conversión de espacio de color (opcional)
    4. codificación -> PNG sin pérdida (codificar_png)
"""

import io
import logging
import time
from dataclasses import dataclass, field
from typing import Callable

import cv2
import numpy as np
from PIL import Image, ImageDraw

from app.core.errores import ProcesamientoError
from app.services.perspectiva import corregir_perspectiva

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpcionesProcesamiento:
    perspectiva: bool = True
    grises: bool = False


@dataclass
class ResultadoProcesamiento:
    imagen: np.ndarray
    perspectiva: str = "desactivada"  # corregida | no_detectada | desactivada
    tiempos_ms: dict[str, float] = field(default_factory=dict)

    @property
    def tiempo_total_ms(self) -> float:
        return sum(self.tiempos_ms.values())


# --------------------------------------------------------------------------
# Utilidades de espacio de color
# --------------------------------------------------------------------------

def a_bgr(imagen: np.ndarray) -> np.ndarray:
    """Normaliza cualquier entrada (gris, BGR o BGRA) a BGR de 3 canales."""
    if imagen.ndim == 2:
        return cv2.cvtColor(imagen, cv2.COLOR_GRAY2BGR)
    if imagen.shape[2] == 4:
        return cv2.cvtColor(imagen, cv2.COLOR_BGRA2BGR)
    return imagen


def a_grises(imagen: np.ndarray) -> np.ndarray:
    """Convierte a un solo canal de luminancia."""
    return imagen if imagen.ndim == 2 else cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

Etapa = Callable[[np.ndarray, OpcionesProcesamiento, ResultadoProcesamiento], np.ndarray]


def _etapa_perspectiva(img, _opciones, res):
    img, res.perspectiva = corregir_perspectiva(img)
    return img


def _etapa_grises(img, opciones, _res):
    return a_grises(img) if opciones.grises else img


def construir_etapas(opciones: OpcionesProcesamiento) -> list[tuple[str, Etapa]]:
    """Devuelve las etapas activas, en el orden en que se aplican."""
    etapas: list[tuple[str, Etapa]] = []
    if opciones.perspectiva:
        etapas.append(("perspectiva", _etapa_perspectiva))
    if opciones.grises:
        etapas.append(("grises", _etapa_grises))
    return etapas


def procesar(imagen: np.ndarray, opciones: OpcionesProcesamiento | None = None) -> ResultadoProcesamiento:
    """Aplica el pipeline a una copia de `imagen` y mide el tiempo de cada etapa."""
    opciones = opciones or OpcionesProcesamiento()
    if imagen is None or imagen.size == 0:
        raise ProcesamientoError("Imagen vacía")

    resultado = ResultadoProcesamiento(imagen=imagen)
    inicio = time.perf_counter()
    actual = a_bgr(imagen).copy()  # 1. nunca se modifica el original
    resultado.tiempos_ms["copia"] = (time.perf_counter() - inicio) * 1000

    for nombre, etapa in construir_etapas(opciones):
        inicio = time.perf_counter()
        try:
            actual = etapa(actual, opciones, resultado)
        except cv2.error as exc:
            raise ProcesamientoError(f"Fallo en la etapa «{nombre}»: {exc}") from exc
        resultado.tiempos_ms[nombre] = (time.perf_counter() - inicio) * 1000

    resultado.imagen = actual
    logger.debug("Tiempos por etapa (ms): %s", resultado.tiempos_ms)
    return resultado


def codificar_png(imagen: np.ndarray, compresion: int = 3) -> bytes:
    """Codifica la imagen en PNG (sin pérdida, adecuado para trazos finos)."""
    ok, buffer = cv2.imencode(".png", imagen, [cv2.IMWRITE_PNG_COMPRESSION, compresion])
    if not ok:
        raise ProcesamientoError("No se pudo codificar el resultado en PNG")
    return buffer.tobytes()


# --------------------------------------------------------------------------
# Ejemplo heredado (POST /imagen-memoria)
# --------------------------------------------------------------------------

def generar_imagen_ejemplo() -> io.BytesIO:
    """Genera en memoria una imagen PNG de ejemplo."""
    imagen = Image.new("RGB", (300, 100), color="blue")
    dibujo = ImageDraw.Draw(imagen)
    dibujo.text((10, 40), "Hola FastAPI", fill="white")

    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
