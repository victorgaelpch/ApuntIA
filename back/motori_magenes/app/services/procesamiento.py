"""Pipeline de procesamiento de imágenes con OpenCV (BACK-03).

Las funciones de este módulo no dependen de FastAPI: reciben y devuelven
matrices de NumPy (BGR, uint8), así que pueden reutilizarse desde scripts,
pruebas o un futuro procesamiento por lotes.

Orden de las etapas (cada una se puede desactivar con OpcionesProcesamiento):

    1. redimensionar -> limita el lado mayor a MAX_LADO_PROCESAMIENTO (BACK-09)
    2. perspectiva  -> detecta el pizarrón y lo endereza (BACK-04)
    3. ruido        -> elimina ruido antes de enfocar, para no amplificarlo (BACK-06)
    4. mejora       -> brillo, iluminación, contraste local y nitidez (BACK-05)
    5. grises       -> conversión de espacio de color (opcional)
    6. codificación -> PNG sin pérdida (codificar_png)
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
from app.services.mejora import mejorar
from app.services.perspectiva import corregir_perspectiva
from app.services.ruido import POR_DEFECTO as RUIDO_POR_DEFECTO
from app.services.ruido import eliminar_ruido

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpcionesProcesamiento:
    max_lado: int = 0  # 0 = sin redimensionar; la API usa settings.max_lado_procesamiento
    perspectiva: bool = True
    ruido: str = RUIDO_POR_DEFECTO  # ninguno | mediana | gaussiano | bilateral | combinado
    mejorar: bool = True
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


def redimensionar(img: np.ndarray, max_lado: int) -> np.ndarray:
    """Reduce la imagen (INTER_AREA) si su lado mayor supera max_lado. Nunca amplía."""
    lado = max(img.shape[:2])
    if max_lado <= 0 or lado <= max_lado:
        return img
    escala = max_lado / lado
    return cv2.resize(img, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)


def _etapa_redimensionar(img, opciones, _res):
    return redimensionar(img, opciones.max_lado)


def _etapa_perspectiva(img, _opciones, res):
    img, res.perspectiva = corregir_perspectiva(img)
    return img


def _etapa_ruido(img, opciones, _res):
    return eliminar_ruido(img, opciones.ruido)


def _etapa_mejora(img, _opciones, res):
    # La normalización de iluminación solo es segura si la imagen es el pizarrón.
    return mejorar(img, normalizar_iluminacion_fondo=res.perspectiva == "corregida")


def _etapa_grises(img, opciones, _res):
    return a_grises(img) if opciones.grises else img


def construir_etapas(opciones: OpcionesProcesamiento) -> list[tuple[str, Etapa]]:
    """Devuelve las etapas activas, en el orden en que se aplican."""
    etapas: list[tuple[str, Etapa]] = []
    if opciones.max_lado > 0:
        etapas.append(("redimensionar", _etapa_redimensionar))
    if opciones.perspectiva:
        etapas.append(("perspectiva", _etapa_perspectiva))
    if opciones.ruido != "ninguno":
        etapas.append(("ruido", _etapa_ruido))
    if opciones.mejorar:
        etapas.append(("mejora", _etapa_mejora))
    if opciones.grises:
        etapas.append(("grises", _etapa_grises))
    return etapas


def procesar(imagen: np.ndarray, opciones: OpcionesProcesamiento | None = None) -> ResultadoProcesamiento:
    """Aplica el pipeline a una copia de `imagen` y mide el tiempo de cada etapa."""
    opciones = opciones or OpcionesProcesamiento()
    if imagen is None or imagen.size == 0:
        raise ProcesamientoError("Imagen vacía")

    resultado = ResultadoProcesamiento(imagen=imagen)
    # Ninguna etapa modifica su entrada (todas devuelven una matriz nueva), así
    # que no hace falta copiar la imagen al empezar (BACK-09: ahorraba ~10 ms en 12 MP).
    actual = a_bgr(imagen)

    for nombre, etapa in construir_etapas(opciones):
        inicio = time.perf_counter()
        try:
            actual = etapa(actual, opciones, resultado)
        except cv2.error as exc:
            raise ProcesamientoError(f"Fallo en la etapa «{nombre}»: {exc}") from exc
        resultado.tiempos_ms[nombre] = (time.perf_counter() - inicio) * 1000

    # Si ninguna etapa actuó, se devuelve una copia para no compartir memoria con el original.
    resultado.imagen = actual.copy() if actual is imagen else actual
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
