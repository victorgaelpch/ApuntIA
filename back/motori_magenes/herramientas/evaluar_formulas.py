"""Evalúa el reconocimiento de fórmulas sobre el corpus (BACK-15, FULL-19).

    python -m herramientas.evaluar_formulas

Para cada fórmula de la muestra informa si el OCR la detectó como fórmula, el
LaTeX obtenido, si coincide exactamente con el esperado y si se pudo dibujar.
"""

import sys

from app.services.formulas import separar_formulas
from app.services.manuscrito import leer_con_respaldo
from app.services.ocr import motor_ocr, reconocer
from app.services.preprocesado_ocr import preprocesar_para_ocr
from herramientas.corpus import formulas_2d, formulas_pizarron


def _n(latex):
    return " ".join((latex or "").split())


def evaluar(m):
    pre = preprocesar_para_ocr(m.imagen, m.tipo_fuente)
    bloques = separar_formulas(leer_con_respaldo(pre.imagen_ocr, reconocer(pre.imagen_ocr, psm=pre.psm), "spa+eng"))
    obtenidas = [b for b in bloques if b.tipo == "formula" or b.recortar]
    filas = []
    for latex_real in m.latex:
        b = next((f for f in obtenidas if _n(getattr(f, "latex", None)) == _n(latex_real)), None)
        filas.append((latex_real, b))
    return filas, obtenidas


def main() -> int:
    if not motor_ocr().disponible():
        print("ERROR: el motor de OCR no está disponible. No se generan métricas.")
        return 1
    for m in (formulas_pizarron(), formulas_2d()):
        filas, obtenidas = evaluar(m)
        print(f"\n### {m.nombre}\n")
        print("| LaTeX esperado | Encontrada exacta | Estado |\n|---|---|---|")
        for latex_real, b in filas:
            print(f"| `{latex_real}` | {'✅' if b else '❌'} | {b.estado if b else '—'} |")
        exactas = sum(1 for _, b in filas if b)
        falsas = sum(1 for f in obtenidas if f.tipo == "formula" and f.estado == "reconocido"
                     and _n(getattr(f, "latex", None)) not in {_n(l) for l in m.latex})
        print(f"\nExactas: {exactas}/{len(m.latex)} · bloques de fórmula o recorte: {len(obtenidas)} · "
              f"fórmulas «reconocidas» incorrectas: {falsas}")
        for f in obtenidas:
            print(f"  - {f.tipo:8} {f.estado:13} texto={f.texto!r} latex={getattr(f, 'latex', None)!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
