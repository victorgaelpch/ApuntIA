"""Métricas de reconocimiento de texto (FULL-19).

CER (Character Error Rate) = distancia de edición entre el texto reconocido y el
real, dividida por la longitud del real. 0 % es perfecto; puede superar el 100 %
si el OCR inventa mucho texto. WER es lo mismo por palabras.
"""

import re
import unicodedata


def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto)
    return re.sub(r"\s+", " ", texto).strip()


def distancia(a, b) -> int:
    previa = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        actual = [i]
        for j, cb in enumerate(b, 1):
            actual.append(min(previa[j] + 1, actual[j - 1] + 1, previa[j - 1] + (ca != cb)))
        previa = actual
    return previa[-1]


def cer(reconocido: str, real: str) -> float:
    real, reconocido = _norm(real), _norm(reconocido)
    return distancia(reconocido, real) / max(1, len(real))


def wer(reconocido: str, real: str) -> float:
    real_p, rec_p = _norm(real).split(), _norm(reconocido).split()
    return distancia(rec_p, real_p) / max(1, len(real_p))
