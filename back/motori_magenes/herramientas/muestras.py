"""Generador de fotografías sintéticas de pizarrón para pruebas y comparativas.

Permite probar el pipeline de forma reproducible (semilla fija) sin depender
de fotos reales: pizarrón inclinado, oscuro, con sombra, con ruido, etc.

    python -m herramientas.muestras ../bd/muestras   # guarda los ejemplos en disco
"""

import sys
from pathlib import Path

import cv2
import numpy as np

LINEAS = [
    "Derivadas: f'(x) = lim h->0",
    "(f(x+h) - f(x)) / h",
    "Ejemplo: x^2 -> 2x",
    "Tarea: ejercicios 1 a 10",
]


def pizarron_plano(ancho: int = 1200, alto: int = 800) -> np.ndarray:
    """Pizarrón blanco con texto en negro, azul y rojo, visto de frente."""
    img = np.full((alto, ancho, 3), 245, np.uint8)
    colores = [(30, 30, 30), (160, 60, 20), (40, 40, 190), (30, 30, 30)]
    for i, (texto, color) in enumerate(zip(LINEAS, colores)):
        y = int(alto * (0.2 + 0.18 * i))
        cv2.putText(img, texto, (int(ancho * 0.06), y), cv2.FONT_HERSHEY_SIMPLEX,
                    ancho / 900, color, max(2, ancho // 400), cv2.LINE_AA)
    cv2.rectangle(img, (0, 0), (ancho - 1, alto - 1), (120, 120, 120), max(4, ancho // 150))
    return img


def foto_inclinada(esquinas_rel=((0.14, 0.12), (0.88, 0.2), (0.84, 0.86), (0.1, 0.8)),
                   ancho: int = 1600, alto: int = 1200, fondo=(70, 85, 95)) -> tuple[np.ndarray, np.ndarray]:
    """Coloca el pizarrón en perspectiva sobre una pared. Devuelve (foto, esquinas_px)."""
    plano = pizarron_plano()
    h, w = plano.shape[:2]
    origen = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    destino = np.float32([[x * ancho, y * alto] for x, y in esquinas_rel])
    m = cv2.getPerspectiveTransform(origen, destino)
    foto = np.empty((alto, ancho, 3), np.uint8)
    foto[:] = fondo
    cv2.warpPerspective(plano, m, (ancho, alto), dst=foto, borderMode=cv2.BORDER_TRANSPARENT)
    return foto, destino


def oscurecer(img: np.ndarray, factor: float = 0.35) -> np.ndarray:
    return cv2.convertScaleAbs(img, alpha=factor, beta=0)


def sombra(img: np.ndarray, intensidad: float = 0.55) -> np.ndarray:
    """Gradiente de iluminación: el lado derecho queda en sombra."""
    h, w = img.shape[:2]
    grad = np.linspace(1.0, 1.0 - intensidad, w, dtype=np.float32)[None, :, None]
    return np.clip(img.astype(np.float32) * grad, 0, 255).astype(np.uint8)


def ruido(img: np.ndarray, sigma: float = 18, sal_pimienta: float = 0.01, semilla: int = 7) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    out = img.astype(np.float32) + rng.normal(0, sigma, img.shape)
    out = np.clip(out, 0, 255).astype(np.uint8)
    mascara = rng.random(img.shape[:2])
    out[mascara < sal_pimienta / 2] = 0
    out[mascara > 1 - sal_pimienta / 2] = 255
    return out


def muestras() -> dict[str, np.ndarray]:
    inclinada, _ = foto_inclinada()
    return {
        "frontal": pizarron_plano(),
        "inclinada": inclinada,
        "oscura": oscurecer(inclinada),
        "sombra": sombra(inclinada),
        "ruido": ruido(inclinada),
        "sin_pizarron": ruido(np.full((900, 1200, 3), (70, 85, 95), np.uint8)),
    }


if __name__ == "__main__":
    destino = Path(sys.argv[1] if len(sys.argv) > 1 else "muestras")
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, img in muestras().items():
        cv2.imwrite(str(destino / f"{nombre}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print("guardada", destino / f"{nombre}.jpg")
