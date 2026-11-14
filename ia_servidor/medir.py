"""Medición real del servidor IA con el corpus sintético del proyecto (BACK-35 → base de BACK-36).

    python -m ia_servidor.medir [--url http://127.0.0.1:8100] [--salida carpeta]

Requiere el servidor IA en marcha con el modelo instalado. Para cada imagen del corpus
sintético (`back/motori_magenes/herramientas/corpus.py`, con verdad-terreno generada por código,
sin fotos de personas) envía UNA petición y registra: latencia, VRAM usada (nvidia-smi cada
0,25 s: antes, pico y después), CER/WER contra la verdad cuando el texto es comparable
(impreso, manuscrito, tabla) y la salida literal para revisión manual (fórmulas, diagramas).

La primera petición incluye la carga del modelo en la VRAM («en frío») y se informa aparte.
Compara con la línea base de Tesseract guardada en `fullstack/evaluacion/linea-base.json`
(otra canalización: página completa con OpenCV + Tesseract), solo como referencia.
"""

from __future__ import annotations

import argparse
import re
import json
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import cv2

from ia_servidor import compartido  # noqa: F401  (pone el backend en sys.path)

RAIZ = Path(__file__).resolve().parents[1]
TAREAS = {"impreso": "texto_impreso", "manuscrito": "texto_manuscrito", "formula": "formula",
          "diagrama": "diagrama", "tabla": "tabla"}
COMPARABLE = {"impreso", "manuscrito", "tabla"}


def normalizar_latex(texto: str) -> str:
    r"""LaTeX comparable: sin espacios, $, \left/\right ni llaves alrededor de un solo símbolo
    (x^{2} == x^2). Así el CER mide errores de lectura, no de estilo."""
    t = re.sub(r"\\(left|right)\b", "", texto.replace("$", ""))
    t = re.sub(r"\\(text|mathrm|operatorname)\{([^{}]*)\}", r"\2", t)   # \text{opposite} == opposite
    t = t.replace("²", "^2").replace("³", "^3")
    t = re.sub(r"([\^_])\{(\\?[A-Za-z0-9])\}", r"\1\2", t)
    return "\n".join(re.sub(r"\s+", "", linea) for linea in t.splitlines() if linea.strip())


SIMBOLOS = {r"\theta": "θ", r"\alpha": "α", r"\beta": "β", r"\pi": "π", r"\pm": "±", r"\Delta": "Δ",
            r"\heartsuit": "♥", r"\degree": "°", "^\\circ": "°", r"\circ": "°"}
FUNCIONES = ("sin", "cos", "tan", "csc", "sec", "cot")


def notacion_equivalente(texto: str) -> str:
    r"""Como normalizar_latex, pero además trata como iguales notaciones equivalentes de una misma
    expresión: \frac{a}{b} == a/b, \sqrt{x} == sqrt(x), \cdot == *. NO es una comprobación
    matemática completa (eso sería SymPy, BACK-36): solo evita penalizar el estilo de escritura."""
    t = normalizar_latex(texto)
    for _ in range(3):  # fracciones y raíces anidadas sencillas
        t = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", lambda m: f"{_grupo(m[1])}/{_grupo(m[2])}", t)
        t = re.sub(r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)", t)
    t = t.replace(r"\cdot", "*").replace("√", "sqrt")
    for orden, simbolo in SIMBOLOS.items():   # LaTeX y Unicode cuentan igual: \pi == π
        t = t.replace(orden, simbolo)
    for f in FUNCIONES:                          # \sin == sin
        t = t.replace("\\" + f, f)
    return t


def _grupo(s: str) -> str:
    return s if re.fullmatch(r"\\?[A-Za-zα-ωΑ-Ω0-9.]+", s) else f"({s})"


def cobertura(salida: str, elementos: list[str], umbral: float = 0.25) -> tuple[float, list[str]]:
    """Fracción de `elementos` que aparecen en `salida` sin depender del orden de lectura: cada
    elemento se compara con cada línea de la salida y con 2-3 líneas seguidas unidas (el modelo
    puede partir una fórmula), y cuenta si el CER en notación equivalente es <= `umbral`."""
    from herramientas.metricas import cer
    lineas = [notacion_equivalente(l).lower() for l in salida.splitlines() if l.strip()]
    lineas = [l for l in lineas if l]
    ventanas = [("".join(lineas[i:i + n])) for n in (1, 2, 3) for i in range(len(lineas) - n + 1)]
    faltan = []
    for e in elementos:
        objetivo = notacion_equivalente(e).lower()
        if not ventanas or min(cer(v, objetivo) for v in ventanas) > umbral:
            faltan.append(e)
    return (1 - len(faltan) / len(elementos) if elementos else 1.0), faltan


class VigilanteVram(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.pico, self.parar = 0, threading.Event()

    @staticmethod
    def leer() -> int:
        try:
            r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                               capture_output=True, text=True, timeout=5)
            return int(r.stdout.strip().splitlines()[0])
        except Exception:
            return -1

    def run(self):
        while not self.parar.is_set():
            self.pico = max(self.pico, self.leer())
            time.sleep(0.25)


def _cabecera_admin() -> dict:
    """Token de administrador local (FULL-31): este medidor solo corre en la PC del servidor."""
    import os

    from ia_servidor.config import carpeta_datos
    from ia_servidor.dispositivos import Registro
    return {"Authorization": "Bearer " + Registro(carpeta_datos(os.environ.get("IA_DATOS", "").strip())).token_admin()}


def pedir(url: str, metodo: str = "GET", datos: bytes | None = None, timeout: float = 600) -> tuple[int, dict]:
    cabeceras = {**_cabecera_admin(), **({"Content-Type": "image/png"} if datos else {})}
    req = urllib.request.Request(url, data=datos, method=metodo, headers=cabeceras)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


ESCRITURAS = {"impreso", "manuscrito", "formula", "tabla", "diagrama", "pagina"}


def cargar_corpus(carpeta: Path) -> list:
    """Corpus privado de fotos reales (BACK-36), FUERA de Git (fullstack/evaluacion/privado/).

    carpeta/verdad.json: {"nombre": {"archivo": "foto.jpg", "tipo_fuente": "pizarron|cuaderno",
    "escritura": "impreso|manuscrito|formula|tabla|diagrama|pagina", "lineas": [...], "latex": [...],
    "permiso": "quién autorizó su uso y cuándo"}}. Mismo formato que el corpus sintético.
    Ver fullstack/docs/evaluacion-multimodal.md."""
    from types import SimpleNamespace

    import numpy as np
    verdad = json.loads((carpeta / "verdad.json").read_text(encoding="utf-8"))
    muestras = []
    for nombre, v in verdad.items():
        if v.get("escritura") not in ESCRITURAS:
            raise ValueError(f"{nombre}: «escritura» debe ser una de {sorted(ESCRITURAS)}")
        if not v.get("permiso"):
            raise ValueError(f"{nombre}: falta «permiso» (quién autorizó usar la foto): no se evalúa sin él")
        ruta = carpeta / v["archivo"]
        if ruta.resolve().parent != carpeta.resolve():
            raise ValueError(f"{nombre}: el archivo debe estar dentro de la carpeta del corpus")
        imagen = cv2.imdecode(np.fromfile(str(ruta), np.uint8), cv2.IMREAD_COLOR)
        if imagen is None:
            raise ValueError(f"{nombre}: no se puede abrir {v['archivo']}")
        muestras.append(SimpleNamespace(nombre=nombre, escritura=v["escritura"], imagen=imagen,
                                        lineas=list(v.get("lineas", [])), latex=list(v.get("latex", [])),
                                        tipo_fuente=v.get("tipo_fuente", ""), archivo=v["archivo"],
                                        origen=v.get("origen"),  # origen: foto de la que es un recorte
                                        trampas=list(v.get("trampas", []))))
    return muestras


def fidelidad(salida: str, trampas: list[dict]) -> dict:
    """«Trampas»: errores REALES del original que deben transcribirse tal cual. Para cada una,
    `literal` (lo escrito) y `corregido` (lo que un modelo «servicial» escribiría). Clasifica:
    fiel (aparece lo escrito), corregida (aparece la corrección: alucinación de fidelidad) o
    no_leida. Comparación en notación equivalente, sin mayúsculas."""
    texto = notacion_equivalente(salida).lower().replace("\n", "")
    detalle = []
    for t in trampas:
        literal = notacion_equivalente(t["literal"]).lower().replace("\n", "")
        corregido = notacion_equivalente(t["corregido"]).lower().replace("\n", "")
        estado = "fiel" if literal in texto else "corregida" if corregido in texto else "no_leida"
        detalle.append({"trampa": t["descripcion"], "estado": estado})
    return {"fieles": sum(d["estado"] == "fiel" for d in detalle),
            "corregidas": sum(d["estado"] == "corregida" for d in detalle),
            "no_leidas": sum(d["estado"] == "no_leida" for d in detalle), "detalle": detalle}


def comparar_pagina_y_regiones(muestras: list, salidas: dict) -> list[dict]:
    """Para cada página completa del corpus cuyas regiones también están (campo «origen»), compara
    sobre los MISMOS elementos: ¿cuántos aparecen enviando la página entera y cuántos enviando cada
    región por separado? Mide si segmentar ayuda (decisión de BACK-36)."""
    resultado = []
    for p in muestras:
        if p.escritura != "pagina" or p.nombre not in salidas:
            continue
        regiones = [m for m in muestras if getattr(m, "origen", None) == getattr(p, "archivo", None) and m.nombre in salidas]
        elementos, cubiertos = [], 0
        for r in regiones:
            propios = r.latex or r.lineas
            elementos += propios
            cob, _ = cobertura(salidas[r.nombre][1], propios)
            cubiertos += round(cob * len(propios))
        if not elementos:
            continue
        cob_pagina, faltan = cobertura(salidas[p.nombre][1], elementos)
        trampas = [t for r in regiones for t in getattr(r, "trampas", [])]
        fid_regiones = {"fieles": 0, "corregidas": 0, "no_leidas": 0}
        for r in regiones:
            f = fidelidad(salidas[r.nombre][1], getattr(r, "trampas", []))
            for k in fid_regiones:
                fid_regiones[k] += f[k]
        resultado.append({"pagina": p.nombre, "regiones": len(regiones), "elementos": len(elementos),
                          "cobertura_pagina_completa": round(cob_pagina, 3),
                          "cobertura_por_regiones": round(cubiertos / len(elementos), 3),
                          "faltan_en_pagina_completa": faltan,
                          "fidelidad_pagina_completa": fidelidad(salidas[p.nombre][1], trampas),
                          "fidelidad_por_regiones": fid_regiones})
    return resultado


def reevaluar(informe_ruta: Path, carpeta: Path) -> dict:
    """Recalcula cobertura, fidelidad y la comparación página/regiones con las salidas YA guardadas
    en un informe (sin volver a usar la GPU). Útil al mejorar la verdad o las métricas."""
    informe = json.loads(informe_ruta.read_text(encoding="utf-8"))
    muestras = {m.nombre: m for m in cargar_corpus(carpeta)}
    salidas = {}
    for fila in informe["resultados"]:
        m = muestras.get(fila["muestra"])
        if m is None or fila.get("http") != 200:
            continue
        salida = "\n".join(x for x in (fila.get("texto"), fila.get("latex"), fila.get("descripcion")) if x)
        salidas[m.nombre] = (m, salida)
        elementos = m.latex or m.lineas
        if elementos:
            cob, faltan = cobertura(salida, elementos)
            fila["cobertura"], fila["faltan"] = round(cob, 3), faltan
        if getattr(m, "trampas", None):
            fila["fidelidad"] = fidelidad(salida, m.trampas)
    informe["comparacion_pagina_regiones"] = comparar_pagina_y_regiones(list(muestras.values()), salidas)
    return informe


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8100")
    p.add_argument("--salida", type=Path, default=RAIZ / "fullstack" / "evaluacion" / "resultados")
    p.add_argument("--corpus", type=Path, help="carpeta con fotos reales y verdad.json (por defecto: corpus sintético)")
    p.add_argument("--reevaluar", type=Path, help="informe ya guardado: recalcular métricas sin usar la GPU (requiere --corpus)")
    a = p.parse_args()
    if a.reevaluar:
        if not a.corpus:
            print("--reevaluar necesita --corpus")
            return 1
        informe = reevaluar(a.reevaluar, a.corpus)
        destino = a.reevaluar.with_name(a.reevaluar.stem + "-reevaluado.json")
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
        for c in informe["comparacion_pagina_regiones"]:
            fp, fr = c["fidelidad_pagina_completa"], c["fidelidad_por_regiones"]
            print(f"«{c['pagina']}»: cobertura {c['cobertura_pagina_completa']:.0%} página / {c['cobertura_por_regiones']:.0%} regiones; "
                  f"fidelidad página: {fp['fieles']} fieles, {fp['corregidas']} corregidas, {fp['no_leidas']} no leídas; "
                  f"regiones: {fr['fieles']} fieles, {fr['corregidas']} corregidas, {fr['no_leidas']} no leídas")
        print("Guardado en", destino)
        return 0

    from herramientas.corpus import corpus
    from herramientas.metricas import cer, wer
    muestras = cargar_corpus(a.corpus) if a.corpus else corpus()

    estado, listo = pedir(a.url + "/listo")
    if estado != 200:
        print("El servidor IA no está listo:", json.dumps(listo.get("componentes", listo), ensure_ascii=False)[:600])
        return 1
    base = {m["muestra"]: m for m in json.loads((RAIZ / "fullstack/evaluacion/linea-base.json").read_text("utf-8"))["texto"]}
    gpu = listo["componentes"].get("gpu", {})
    resultados, salidas = [], {}
    for i, m in enumerate(muestras):
        tarea = TAREAS.get(m.escritura, "pagina")
        png = cv2.imencode(".png", m.imagen)[1].tobytes()
        antes = VigilanteVram.leer()
        vig = VigilanteVram(); vig.start()
        t0 = time.perf_counter()
        estado, r = pedir(f"{a.url}/api/v1/analisis?tarea={tarea}", "POST", png)
        segundos = round(time.perf_counter() - t0, 2)
        vig.parar.set(); vig.join()
        fila = {"muestra": m.nombre, "escritura": m.escritura, "tarea": tarea, "http": estado, "segundos": segundos,
                "en_frio": i == 0, "vram_antes_mb": antes, "vram_pico_mb": vig.pico}
        if estado == 200:
            res = r["resultado"]
            fila.update(modelo=r["modelo"]["nombre"], estado=res["estado"], dudas=len(res["dudas"]),
                        tokens=r["metricas"].get("tokens_salida"), texto=res["texto"], latex=res["latex"],
                        descripcion=res["descripcion"], calidad=r["calidad"].get("nivel"))
            if m.escritura in COMPARABLE:
                real = "\n".join(m.lineas)
                fila["cer"], fila["wer"] = round(cer(res["texto"], real), 4), round(wer(res["texto"], real), 4)
                if m.nombre in base and base[m.nombre].get("cer") is not None:
                    fila["cer_tesseract_linea_base"] = base[m.nombre]["cer"]
            if m.escritura == "formula" and m.latex:
                fila["cer_latex_normalizado"] = round(cer(normalizar_latex(res["latex"] or res["texto"]),
                                                          normalizar_latex("\n".join(m.latex))), 4)
                fila["cer_notacion_equivalente"] = round(cer(notacion_equivalente(res["latex"] or res["texto"]),
                                                             notacion_equivalente("\n".join(m.latex))), 4)
            elementos = m.latex or m.lineas
            if elementos:
                salida = "\n".join(x for x in (res["texto"], res["latex"], res["descripcion"]) if x)
                cob, faltan = cobertura(salida, elementos)
                fila["cobertura"], fila["faltan"] = round(cob, 3), faltan
            if getattr(m, "trampas", None):
                fila["fidelidad"] = fidelidad("\n".join(x for x in (res["texto"], res["latex"], res["descripcion"]) if x),
                                              m.trampas)
            salidas[m.nombre] = (m, "\n".join(x for x in (res["texto"], res["latex"], res["descripcion"]) if x))
        else:
            fila["error"] = r.get("error", {}).get("codigo")
        print(f"{m.nombre:24} {tarea:17} {estado} {segundos:6.1f}s  pico VRAM {vig.pico} MB  "
              f"CER {fila.get('cer', fila.get('cer_notacion_equivalente', '—'))} (LaTeX literal {fila.get('cer_latex_normalizado', '—')})  "
              f"cobertura {fila.get('cobertura', '—')}  (Tesseract {fila.get('cer_tesseract_linea_base', '—')})")
        resultados.append(fila)
    comparacion = comparar_pagina_y_regiones(muestras, salidas)
    for c in comparacion:
        print(f"Página «{c['pagina']}»: cobertura de los elementos de las {c['regiones']} regiones = "
              f"{c['cobertura_pagina_completa']:.0%} enviando la página completa, {c['cobertura_por_regiones']:.0%} "
              f"enviando cada región ({c['elementos']} elementos).")
    _, ps = pedir(a.url + "/listo")
    informe = {
        "fecha_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gpu": gpu, "ollama": listo["componentes"].get("ollama"), "modelo": listo["componentes"].get("modelo"),
        "en_memoria_al_final": ps.get("componentes", {}).get("en_memoria"),
        "corpus": "privado (fotos reales)" if a.corpus else "sintético",
        "nota": ("Corpus PRIVADO de fotos reales con permiso; el informe contiene texto transcrito: no subirlo a Git."
                 if a.corpus else
                 "Corpus SINTÉTICO generado por código; no representa fotos reales de clase. CER de Tesseract: "
                 "línea base guardada (otra canalización y otro equipo), solo como referencia."),
        "resultados": resultados,
        "comparacion_pagina_regiones": comparacion,
    }
    a.salida.mkdir(parents=True, exist_ok=True)
    modelo = (listo["componentes"].get("modelo") or {}).get("nombre", "modelo").replace(":", "_").replace("/", "_")
    destino = a.salida / f"servidor-ia-medicion-{modelo}{'-privado' if a.corpus else ''}.json"
    destino.write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Guardado en", destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
