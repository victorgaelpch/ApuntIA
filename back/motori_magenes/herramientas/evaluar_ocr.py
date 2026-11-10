"""Evalúa el OCR sobre el corpus sintético etiquetado (BACK-12/13/14, FULL-19).

    python -m herramientas.evaluar_ocr                 # con el preprocesado por perfil
    python -m herramientas.evaluar_ocr --sin-preprocesar

Para cada muestra informa CER y WER (menor es mejor) y cuántos bloques quedaron
reconocidos, inciertos o no reconocidos. No inventa métricas: si el OCR no está
instalado, lo dice y termina con error.
"""

import argparse
import sys
import time

from app.services.ocr import ErrorOCR, motor_ocr, reconocer
from herramientas.corpus import corpus
from herramientas.metricas import cer, wer


def _norm(t: str) -> str:
    return " ".join(t.split())


def reconocidos_con_errores(bloques, lineas_reales) -> int:
    """Bloques marcados «reconocido» cuyo texto no coincide exactamente con el real:
    es el error más peligroso, porque el usuario confiaría en él sin revisarlo."""
    reales = {_norm(l) for l in lineas_reales}
    return sum(1 for b in bloques if b.texto and b.estado == "reconocido"
               and any(_norm(l) not in reales for l in b.texto.split("\n")))


def preparar(muestra, preprocesar: bool):
    if not preprocesar:
        return muestra.imagen, 3
    from app.services.preprocesado_ocr import preprocesar_para_ocr
    pre = preprocesar_para_ocr(muestra.imagen, muestra.tipo_fuente)
    return pre.imagen_ocr, pre.psm


def evaluar(preprocesar: bool = True) -> list[dict]:
    filas = []
    for m in corpus():
        inicio = time.perf_counter()
        imagen, psm = preparar(m, preprocesar)
        bloques = reconocer(imagen, psm=psm)
        if preprocesar:  # flujo de producción: con el respaldo de manuscritos (BACK-14)
            from app.services.manuscrito import leer_con_respaldo
            bloques = leer_con_respaldo(imagen, bloques, "spa+eng")
        texto = "\n".join(b.texto for b in bloques if b.texto)
        real = "\n".join(m.lineas)
        estados = [b.estado if b.texto else "no_reconocido" for b in bloques]
        filas.append({"muestra": m.nombre, "escritura": m.escritura, "cer": cer(texto, real), "wer": wer(texto, real),
                      "reconocidos": estados.count("reconocido"), "inciertos": estados.count("incierto"),
                      "no_reconocidos": estados.count("no_reconocido"),
                      "falsos": reconocidos_con_errores(bloques, m.lineas),
                      "ms": (time.perf_counter() - inicio) * 1000, "texto": texto})
    return filas


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sin-preprocesar", action="store_true")
    parser.add_argument("--texto", action="store_true", help="muestra el texto reconocido")
    args = parser.parse_args()
    if not motor_ocr().disponible():
        print("ERROR: el motor de OCR no está disponible (instala Tesseract). No se generan métricas.")
        return 1
    try:
        filas = evaluar(not args.sin_preprocesar)
    except ErrorOCR as exc:
        print(f"ERROR: {exc.mensaje}")
        return 1
    modo = "sin preprocesar" if args.sin_preprocesar else "con preprocesado por perfil"
    print(f"OCR {motor_ocr().info().get('version', '')} — {modo}\n")
    print("| Muestra | Escritura | CER | WER | Bloques (rec./inc./no rec.) | Reconocidos con errores | ms |")
    print("|---|---|---|---|---|---|---|")
    for f in filas:
        print(f"| {f['muestra']} | {f['escritura']} | {f['cer']:.1%} | {f['wer']:.1%} | "
              f"{f['reconocidos']}/{f['inciertos']}/{f['no_reconocidos']} | {f['falsos']} | {f['ms']:.0f} |")
        if args.texto:
            print("```\n" + f["texto"] + "\n```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
