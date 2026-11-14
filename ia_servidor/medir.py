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
    t = re.sub(r"([\^_])\{(\\?[A-Za-z0-9])\}", r"\1\2", t)
    return "\n".join(re.sub(r"\s+", "", linea) for linea in t.splitlines() if linea.strip())


def notacion_equivalente(texto: str) -> str:
    r"""Como normalizar_latex, pero además trata como iguales notaciones equivalentes de una misma
    expresión: \frac{a}{b} == a/b, \sqrt{x} == sqrt(x), \cdot == *. NO es una comprobación
    matemática completa (eso sería SymPy, BACK-36): solo evita penalizar el estilo de escritura."""
    t = normalizar_latex(texto)
    for _ in range(3):  # fracciones y raíces anidadas sencillas
        t = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", lambda m: f"{_grupo(m[1])}/{_grupo(m[2])}", t)
        t = re.sub(r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)", t)
    return t.replace(r"\cdot", "*")


def _grupo(s: str) -> str:
    return s if re.fullmatch(r"\\?[A-Za-z0-9.]+", s) else f"({s})"


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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8100")
    p.add_argument("--salida", type=Path, default=RAIZ / "fullstack" / "evaluacion" / "resultados")
    a = p.parse_args()

    from herramientas.corpus import corpus
    from herramientas.metricas import cer, wer

    estado, listo = pedir(a.url + "/listo")
    if estado != 200:
        print("El servidor IA no está listo:", json.dumps(listo.get("componentes", listo), ensure_ascii=False)[:600])
        return 1
    base = {m["muestra"]: m for m in json.loads((RAIZ / "fullstack/evaluacion/linea-base.json").read_text("utf-8"))["texto"]}
    gpu = listo["componentes"].get("gpu", {})
    resultados = []
    for i, m in enumerate(corpus()):
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
        else:
            fila["error"] = r.get("error", {}).get("codigo")
        print(f"{m.nombre:24} {tarea:17} {estado} {segundos:6.1f}s  pico VRAM {vig.pico} MB  "
              f"CER {fila.get('cer', fila.get('cer_notacion_equivalente', '—'))} (LaTeX literal {fila.get('cer_latex_normalizado', '—')})  (Tesseract {fila.get('cer_tesseract_linea_base', '—')})")
        resultados.append(fila)
    _, ps = pedir(a.url + "/listo")
    informe = {
        "fecha_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gpu": gpu, "ollama": listo["componentes"].get("ollama"), "modelo": listo["componentes"].get("modelo"),
        "en_memoria_al_final": ps.get("componentes", {}).get("en_memoria"),
        "nota": "Corpus SINTÉTICO generado por código; no representa fotos reales de clase. CER de Tesseract: "
                "línea base guardada (otra canalización y otro equipo), solo como referencia.",
        "resultados": resultados,
    }
    a.salida.mkdir(parents=True, exist_ok=True)
    modelo = (listo["componentes"].get("modelo") or {}).get("nombre", "modelo").replace(":", "_").replace("/", "_")
    destino = a.salida / f"servidor-ia-medicion-{modelo}.json"
    destino.write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Guardado en", destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
