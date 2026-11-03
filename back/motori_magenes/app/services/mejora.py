"""Mejora de calidad y nitidez (BACK-05).

Todo se aplica sobre el canal de luminancia L del espacio LAB, para no
alterar los colores de los marcadores:

  1. Brillo: si la imagen es oscura (L medio < UMBRAL_OSCURA), corrección
     gamma automática que lleva la luminancia media hacia el 50 %.
  2. Iluminación (solo si `normalizar_iluminacion`): se estima el fondo del
     pizarrón con un cierre morfológico (borra los trazos) y un desenfoque,
     y se divide L entre ese fondo. Elimina sombras y degradados. Solo se usa
     cuando la perspectiva se corrigió y la imagen es únicamente pizarrón: en
     fotos con pared o muebles, aclara las zonas oscuras y hace visibles los
     artefactos JPEG.
  3. Contraste local (solo si NO se normalizó la iluminación): CLAHE con
     clipLimit=2.0 y rejilla 8x8, un clipLimit bajo para no amplificar ruido
     ni crear halos. Tras normalizar no aporta contraste y crea bandas en los
     degradados.
  4. Nitidez: máscara de enfoque moderada (cantidad 0.6, sigma proporcional
     a la resolución).

Los parámetros se eligieron comparando variantes con
`python -m herramientas.evaluar_mejora` (resultados en el README del backend).
"""

import cv2
import numpy as np

UMBRAL_OSCURA = 105
CLAHE_CLIP = 2.0
CLAHE_REJILLA = (8, 8)
ENFOQUE_CANTIDAD = 0.6
BLANCO_OBJETIVO = 235


def _gamma_automatica(l: np.ndarray) -> np.ndarray:
    media = float(l.mean()) / 255.0
    if media * 255 >= UMBRAL_OSCURA or media <= 0:
        return l
    gamma = float(np.clip(np.log(0.5) / np.log(media), 0.4, 1.0))  # < 1 aclara
    tabla = (np.linspace(0, 1, 256) ** gamma * 255).astype(np.uint8)
    return cv2.LUT(l, tabla)


def normalizar_iluminacion(l: np.ndarray) -> np.ndarray:
    k = max(15, (max(l.shape[:2]) // 40) | 1)
    nucleo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    fondo = cv2.morphologyEx(l, cv2.MORPH_CLOSE, nucleo)
    fondo = cv2.GaussianBlur(fondo, (0, 0), k / 2)
    normal = l.astype(np.float32) / np.maximum(fondo.astype(np.float32), 1.0) * BLANCO_OBJETIVO
    return np.clip(normal, 0, 255).astype(np.uint8)


def enfocar(l: np.ndarray, cantidad: float = ENFOQUE_CANTIDAD) -> np.ndarray:
    sigma = max(0.8, max(l.shape[:2]) / 1500)
    difuminada = cv2.GaussianBlur(l, (0, 0), sigma)
    return cv2.addWeighted(l, 1 + cantidad, difuminada, -cantidad, 0)


def mejorar(imagen: np.ndarray, normalizar_iluminacion_fondo: bool = False) -> np.ndarray:
    """Devuelve una imagen BGR con brillo, contraste local y nitidez mejorados."""
    l, a, b = cv2.split(cv2.cvtColor(imagen, cv2.COLOR_BGR2LAB))
    l = _gamma_automatica(l)
    if normalizar_iluminacion_fondo:
        l = normalizar_iluminacion(l)
    else:
        l = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_REJILLA).apply(l)
    l = enfocar(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
