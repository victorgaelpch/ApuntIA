"""Compara filtros de eliminación de ruido (BACK-06).

    python -m herramientas.evaluar_ruido

Sobre el pizarrón sintético con ruido gaussiano (sigma 18) y sal y pimienta
(1 %), mide para cada filtro:
  - PSNR frente a la imagen limpia (dB, más alto = más parecido);
  - contraste del texto (diferencia de L entre fondo y trazos): si cae, el
    filtro está borrando escritura;
  - nitidez de bordes (varianza del laplaciano dentro de la zona de texto,
    en % de la imagen limpia);
  - tiempo en ms.
"""

import time

import cv2
import numpy as np

from app.services.ruido import FILTROS
from herramientas.muestras import pizarron_plano, ruido


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    return float(cv2.PSNR(a, b))


def main() -> None:
    limpia = pizarron_plano(1600, 1066)
    texto = cv2.cvtColor(limpia, cv2.COLOR_BGR2GRAY) < 200
    b = 14
    texto[:b] = texto[-b:] = False
    texto[:, :b] = texto[:, -b:] = False
    zona = cv2.dilate(texto.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)

    def lap(img):
        return float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F)[zona].var())

    def contraste(img):
        l = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
        return float(l[~zona].mean() - l[texto].mean())

    ruidosa = ruido(limpia)
    ref_lap = lap(limpia)
    print("| Filtro | PSNR (dB) | Contraste texto | Nitidez bordes | Tiempo (ms) |")
    print("|---|---|---|---|---|")
    print(f"| (limpia) | ∞ | {contraste(limpia):.1f} | 100 % | — |")
    for nombre, filtro in {"(sin filtro)": lambda x: x, **FILTROS}.items():
        inicio = time.perf_counter()
        for _ in range(3):
            salida = filtro(ruidosa)
        ms = (time.perf_counter() - inicio) * 1000 / 3
        print(f"| {nombre} | {psnr(limpia, salida):.1f} | {contraste(salida):.1f} | "
              f"{lap(salida) / ref_lap * 100:.0f} % | {ms:.0f} |")


if __name__ == "__main__":
    main()
