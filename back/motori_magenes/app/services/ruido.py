"""Eliminación de ruido (BACK-06).

Filtros disponibles (parámetro `ruido` de POST /analisis):

- "mediana":   cv2.medianBlur 3x3. El mejor contra sal y pimienta.
- "gaussiano": cv2.GaussianBlur 3x3. Rápido, pero suaviza también los bordes.
- "bilateral": cv2.bilateralFilter (d=7, sigmaColor=40, sigmaSpace=7). Suaviza
               zonas planas y preserva los bordes de los trazos.
- "combinado": mediana 3x3 + bilateral. Ruido mixto de cámara (por defecto).
- "ninguno":   sin filtrar.

La comparación que justifica la elección está en el README del backend
(`python -m herramientas.evaluar_ruido`).
"""

from typing import Callable

import cv2
import numpy as np

POR_DEFECTO = "combinado"


def mediana(img: np.ndarray) -> np.ndarray:
    return cv2.medianBlur(img, 3)


def gaussiano(img: np.ndarray) -> np.ndarray:
    return cv2.GaussianBlur(img, (3, 3), 0)


def bilateral(img: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(img, d=7, sigmaColor=40, sigmaSpace=7)


def combinado(img: np.ndarray) -> np.ndarray:
    return bilateral(mediana(img))


FILTROS: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "mediana": mediana,
    "gaussiano": gaussiano,
    "bilateral": bilateral,
    "combinado": combinado,
}

METODOS = ("ninguno", *FILTROS)


def eliminar_ruido(img: np.ndarray, metodo: str = POR_DEFECTO) -> np.ndarray:
    if metodo == "ninguno":
        return img
    return FILTROS[metodo](img)
