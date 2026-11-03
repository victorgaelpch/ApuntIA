"""Compara el contraste texto/fondo antes y después de la mejora (BACK-05).

    python -m herramientas.evaluar_mejora

Usa el pizarrón sintético frontal, donde se conoce qué píxeles son texto, en
tres condiciones: clara, oscura y con sombra. Métricas:
  - contraste: diferencia media de luminancia entre el fondo y el texto
    (más alto = texto más legible);
  - contraste_sombra: el mismo valor en la franja con texto más afectada por
    la sombra (45 %-75 % del ancho);
  - saturados: % de píxeles a 0 o 255 (si sube mucho = sobreprocesamiento).
"""

import cv2
import numpy as np

from app.services.mejora import mejorar
from herramientas.muestras import oscurecer, pizarron_plano, sombra


def metricas(img: np.ndarray, texto: np.ndarray) -> dict[str, float]:
    l = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    fondo = ~texto
    franja = np.zeros_like(texto)
    w = img.shape[1]
    franja[:, int(w * 0.45):int(w * 0.75)] = True
    return {
        "contraste": float(l[fondo].mean() - l[texto].mean()),
        "contraste_sombra": float(l[fondo & franja].mean() - l[texto & franja].mean()),
        "saturados": float(((l <= 0) | (l >= 255)).mean() * 100),
    }


VARIANTES = {
    "sin mejora": lambda img: img,
    "CLAHE + enfoque (foto con pared)": lambda img: mejorar(img, False),
    "Iluminación + enfoque (pizarrón rectificado)": lambda img: mejorar(img, True),
}


def main() -> None:
    plano = pizarron_plano()
    texto = cv2.cvtColor(plano, cv2.COLOR_BGR2GRAY) < 200
    borde = max(4, plano.shape[1] // 150) + 2
    texto[:borde, :] = texto[-borde:, :] = False
    texto[:, :borde] = texto[:, -borde:] = False
    casos = {"clara": plano, "oscura": oscurecer(plano), "sombra": sombra(plano, 0.7)}
    print("| Variante | " + " | ".join(f"{c}: contraste / en sombra / % saturados" for c in casos) + " |")
    print("|---" * (len(casos) + 1) + "|")
    for nombre, f in VARIANTES.items():
        celdas = []
        for img in casos.values():
            m = metricas(f(img), texto)
            celdas.append(f"{m['contraste']:.1f} / {m['contraste_sombra']:.1f} / {m['saturados']:.1f}")
        print(f"| {nombre} | " + " | ".join(celdas) + " |")


if __name__ == "__main__":
    main()
