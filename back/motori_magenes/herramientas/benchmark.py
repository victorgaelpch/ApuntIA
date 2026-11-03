"""Mide el tiempo del pipeline por etapa (BACK-09).

    python -m herramientas.benchmark            # tabla en Markdown
    python -m herramientas.benchmark --repes 5

Imágenes de referencia (sintéticas y reproducibles, más la foto real):
  - real_516x387:   back/bd/img/image.png
  - inclinada_1600: pizarrón inclinado de 1600x1200 (~2 MP)
  - movil_12mp:     el mismo pizarrón a 4032x3024 (cámara típica de celular)
  - movil_12mp_ruido: igual que la anterior, con ruido

Se mide de extremo a extremo, igual que en la API: decodificar el JPEG,
cada etapa del pipeline y codificar el PNG. Se informa la mediana de N
repeticiones.
"""

import argparse
import statistics
import time
from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings
from app.services.procesamiento import OpcionesProcesamiento, codificar_png, procesar
from herramientas.muestras import foto_inclinada, ruido

RAIZ = Path(__file__).resolve().parents[1]


def referencias() -> dict[str, bytes]:
    def jpg(img):
        return cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()

    inclinada, _ = foto_inclinada()
    movil, _ = foto_inclinada(ancho=4032, alto=3024)
    refs = {
        "inclinada_1600": jpg(inclinada),
        "movil_12mp": jpg(movil),
        "movil_12mp_ruido": jpg(ruido(movil)),
    }
    real = RAIZ.parent / "bd" / "img" / "image.png"
    if real.exists():
        refs = {"real_516x387": real.read_bytes(), **refs}
    return refs


def medir(datos: bytes, opciones: OpcionesProcesamiento) -> dict[str, float]:
    t = time.perf_counter()
    img = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
    decod = (time.perf_counter() - t) * 1000
    res = procesar(img, opciones)
    t = time.perf_counter()
    png = codificar_png(res.imagen)
    cod = (time.perf_counter() - t) * 1000
    tiempos = {"decodificar": decod, **res.tiempos_ms, "codificar_png": cod}
    tiempos["TOTAL"] = sum(tiempos.values())
    tiempos["_kb_salida"] = len(png) / 1024
    tiempos["_salida"] = f"{res.imagen.shape[1]}x{res.imagen.shape[0]}"
    return tiempos


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repes", type=int, default=3)
    args = parser.parse_args()
    opciones = OpcionesProcesamiento(max_lado=settings.max_lado_procesamiento)
    for nombre, datos in referencias().items():
        corridas = [medir(datos, opciones) for _ in range(args.repes)]
        claves = [k for k in corridas[0] if not k.startswith("_")]
        print(f"\n**{nombre}** → salida {corridas[0]['_salida']}, PNG {corridas[0]['_kb_salida']:.0f} KB\n")
        print("| Etapa | ms (mediana) |\n|---|---|")
        for k in claves:
            print(f"| {k} | {statistics.median(c[k] for c in corridas):.0f} |")


if __name__ == "__main__":
    main()
