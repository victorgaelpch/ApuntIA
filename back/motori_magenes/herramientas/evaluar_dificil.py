"""Evalúa el reconocimiento con el corpus de casos difíciles (BACK-28).

    python -m herramientas.evaluar_dificil                         # modo configurado, las dos particiones
    python -m herramientas.evaluar_dificil --modo clasico          # el flujo anterior a BACK-28
    python -m herramientas.evaluar_dificil --particion evaluacion --json salida.json
    python -m herramientas.evaluar_dificil --comparar clasico.json adaptativo.json

Los espacios alrededor de los operadores matemáticos no cuentan como error («v=d/t» es lo
mismo que «v = d / t»), ni en el texto ni al buscar texto falso.

Por muestra mide, con el mismo flujo que usa la API (`reconocer_pagina`):
  - CER y WER del texto frente a la referencia;
  - bloques reconocidos / inciertos / sin leer;
  - «reconocidos con errores»: el error peligroso, un texto falso marcado como seguro;
  - fórmulas: exactas (LaTeX normalizado), válidas y falsas reconocidas;
  - avisos de calidad y bloques con alternativas;
  - tiempo y memoria máxima.
No inventa cifras: si Tesseract no está instalado termina con error.
"""

import argparse
import json
import re
import platform
import resource
import sys
import time

from app.services.ocr import motor_ocr
from app.services.reconocimiento import MODOS, reconocer_pagina
from herramientas.corpus_dificil import TEXTOS, corpus_dificil
from herramientas.metricas import cer, wer


OPERADORES = re.compile(r"\s*([=+\-*/^_()<>])\s*")


def _n(texto: str) -> str:
    """Espacios normalizados; alrededor de los operadores no cuentan («v=d/t» = «v = d / t»)."""
    return OPERADORES.sub(r"\1", " ".join((texto or "").split()))


def _texto_n(texto: str) -> str:
    return "\n".join(_n(l) for l in (texto or "").split("\n"))


def _latex_n(latex: str | None) -> str:
    return "".join((latex or "").split()).replace(r"\left(", "(").replace(r"\right)", ")")


def evaluar_muestra(m, modo: str) -> dict:
    inicio = time.perf_counter()
    r = reconocer_pagina(m.imagen, m.tipo_fuente, "spa+eng", modo=modo)
    ms = round((time.perf_counter() - inicio) * 1000)
    bloques = r.bloques
    texto = "\n".join(b.texto for b in bloques if b.texto)
    reales = {_n(l) for l in m.lineas}
    estados = [b.estado if b.texto else "no_reconocido" for b in bloques]
    # Texto falso dado por seguro. En la página mixta las celdas de la tabla se leen por separado,
    # así que una línea cuenta como correcta si está contenida en alguna línea de referencia.
    falsos = sum(1 for b in bloques if b.texto and b.estado == "reconocido"
                 and any(_n(l) and not any(_n(l) in real for real in reales) for l in b.texto.split("\n")))
    formulas = [b for b in bloques if b.tipo == "formula"]
    esperadas = {_latex_n(l) for l in m.latex}
    exactas = sum(1 for l in esperadas if any(_latex_n(getattr(b, "latex", None)) == l for b in formulas))
    falsas = sum(1 for b in formulas if b.estado == "reconocido" and _latex_n(getattr(b, "latex", None)) not in esperadas)
    fila = {
        "muestra": m.nombre, "escritura": m.escritura, "modo": r.modo, "ms": ms,
        "cer": round(cer(_texto_n(texto), _texto_n("\n".join(m.lineas))), 4) if m.lineas else None,
        "wer": round(wer(_texto_n(texto), _texto_n("\n".join(m.lineas))), 4) if m.lineas else None,
        "reconocidos": estados.count("reconocido"), "inciertos": estados.count("incierto"),
        "sin_leer": estados.count("no_reconocido"), "reconocidos_con_errores": falsos,
        "formulas_esperadas": len(esperadas), "formulas_exactas": exactas,
        "formulas_validas": sum(1 for b in formulas if getattr(b, "latex_valido", False)),
        "formulas_falsas": falsas,
        "con_alternativas": sum(1 for b in bloques if getattr(b, "alternativas", None)),
        # Recuperación asistida: bloques con texto erróneo cuya alternativa SÍ es el texto real
        # (el usuario lo corrige con un clic en lugar de escribirlo).
        "corregibles_con_alternativa": sum(
            1 for b in bloques if b.texto and any(_n(l) not in reales for l in b.texto.split("\n"))
            and any(all(_n(l) in reales for l in a["texto"].split("\n")) for a in getattr(b, "alternativas", []))),
        "bloques_con_error": sum(1 for b in bloques if b.texto and any(_n(l) and not any(_n(l) in real for real in reales)
                                                                       for l in b.texto.split("\n"))),
        "avisos": sorted(set(r.advertencias)),
        "texto": texto,
    }
    return fila


def evaluar(modo: str, particiones: list[str]) -> dict:
    filas = []
    inicio = time.perf_counter()
    for p in particiones:
        for m in corpus_dificil(p):
            fila = evaluar_muestra(m, modo)
            fila["particion"] = p
            filas.append(fila)
    info = motor_ocr().info()
    return {"modo": modo, "python": platform.python_version(), "tesseract": info.get("version"),
            "segundos": round(time.perf_counter() - inicio, 1),
            "memoria_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024),
            "muestras": filas}


def resumen(filas: list[dict]) -> dict:
    con_texto = [f for f in filas if f["cer"] is not None]
    return {
        "cer_medio": round(sum(f["cer"] for f in con_texto) / max(1, len(con_texto)), 4),
        "wer_medio": round(sum(f["wer"] for f in con_texto) / max(1, len(con_texto)), 4),
        "reconocidos_con_errores": sum(f["reconocidos_con_errores"] for f in filas),
        "formulas_exactas": sum(f["formulas_exactas"] for f in filas),
        "formulas_esperadas": sum(f["formulas_esperadas"] for f in filas),
        "formulas_falsas": sum(f["formulas_falsas"] for f in filas),
        "bloques_con_error": sum(f.get("bloques_con_error", 0) for f in filas),
        "corregibles_con_alternativa": sum(f.get("corregibles_con_alternativa", 0) for f in filas),
        "ms_total": sum(f["ms"] for f in filas),
    }


def tabla(datos: dict) -> str:
    filas = ["| Partición | Muestra | CER | WER | Rec./inc./sin leer | Rec. con errores | Fórmulas exactas | Avisos | ms |",
             "|---|---|---:|---:|---|---:|---:|---|---:|"]
    for f in datos["muestras"]:
        pct = lambda v: "—" if v is None else f"{v:.1%}"  # noqa: E731
        form = f"{f['formulas_exactas']}/{f['formulas_esperadas']}" if f["formulas_esperadas"] else "—"
        filas.append(f"| {f['particion']} | {f['muestra'].rsplit('_', 1)[0]} | {pct(f['cer'])} | {pct(f['wer'])} | "
                     f"{f['reconocidos']}/{f['inciertos']}/{f['sin_leer']} | {f['reconocidos_con_errores']} | {form} | "
                     f"{', '.join(f['avisos']) or '—'} | {f['ms']} |")
    return "\n".join(filas)


def comparar(antes: dict, despues: dict) -> str:
    salida = ["| Partición | Muestra | CER antes → después | WER antes → después | Rec. con errores | Fórmulas exactas |",
              "|---|---|---|---|---|---|"]
    previas = {(f["particion"], f["muestra"]): f for f in antes["muestras"]}
    for f in despues["muestras"]:
        a = previas.get((f["particion"], f["muestra"]))
        if not a:
            continue
        pct = lambda v: "—" if v is None else f"{v:.1%}"  # noqa: E731
        form = (f"{a['formulas_exactas']} → {f['formulas_exactas']} de {f['formulas_esperadas']}"
                if f["formulas_esperadas"] else "—")
        salida.append(f"| {f['particion']} | {f['muestra'].rsplit('_', 1)[0]} | {pct(a['cer'])} → {pct(f['cer'])} | "
                      f"{pct(a['wer'])} → {pct(f['wer'])} | {a['reconocidos_con_errores']} → {f['reconocidos_con_errores']} | {form} |")
    for p in TEXTOS:
        ra = resumen([f for f in antes["muestras"] if f["particion"] == p])
        rd = resumen([f for f in despues["muestras"] if f["particion"] == p])
        salida.append(f"\n**{p}:** CER medio {ra['cer_medio']:.1%} → {rd['cer_medio']:.1%} · WER medio "
                      f"{ra['wer_medio']:.1%} → {rd['wer_medio']:.1%} · reconocidos con errores "
                      f"{ra['reconocidos_con_errores']} → {rd['reconocidos_con_errores']} · fórmulas exactas "
                      f"{ra['formulas_exactas']} → {rd['formulas_exactas']} de {rd['formulas_esperadas']} · "
                      f"fórmulas falsas {ra['formulas_falsas']} → {rd['formulas_falsas']} · bloques con error "
                      f"corregibles con una alternativa {ra['corregibles_con_alternativa']} → "
                      f"{rd['corregibles_con_alternativa']} de {rd['bloques_con_error']} · tiempo "
                      f"{ra['ms_total'] / 1000:.1f} s → {rd['ms_total'] / 1000:.1f} s")
    return "\n".join(salida)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", choices=MODOS, default=None)
    ap.add_argument("--particion", choices=list(TEXTOS), action="append")
    ap.add_argument("--json")
    ap.add_argument("--comparar", nargs=2, metavar=("ANTES", "DESPUES"))
    args = ap.parse_args()
    if args.comparar:
        antes, despues = (json.load(open(a, encoding="utf-8")) for a in args.comparar)
        print(comparar(antes, despues))
        return 0
    if not motor_ocr().disponible():
        print("ERROR: Tesseract no está disponible: no se generan métricas.", file=sys.stderr)
        return 1
    from app.core.config import settings
    datos = evaluar(args.modo or settings.reconocimiento_modo, args.particion or list(TEXTOS))
    print(tabla(datos))
    for p in TEXTOS:
        print(f"\n{p}: {resumen([f for f in datos['muestras'] if f['particion'] == p])}")
    print(f"\nModo {datos['modo']} · {datos['segundos']} s · memoria máxima {datos['memoria_mb']} MB")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
