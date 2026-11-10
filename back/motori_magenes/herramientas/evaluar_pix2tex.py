"""Evalúa pix2tex (LatexOCR, MIT) sobre las fórmulas de los corpus de ApuntIA (BACK-28).

NO forma parte de ApuntIA: es la evaluación que justificó no integrarlo (PROCESAMIENTO.md,
sección BACK-28). Necesita un entorno aparte, porque pix2tex instala PyTorch (~6 GB):

    python -m venv /tmp/p2t && /tmp/p2t/bin/pip install torch pix2tex matplotlib
    /tmp/p2t/bin/python herramientas/evaluar_pix2tex.py      # desde back/motori_magenes
"""
import re
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from herramientas.corpus import FORMULAS, FORMULAS_2D, FUENTE
from herramientas.corpus_dificil import TEXTOS, _mathtext

def n(l):
    l = (l or "").replace(r"\left(", "(").replace(r"\right)", ")").replace(r"\,", "").replace(r"\;", "").replace(r"\!", "")
    l = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", l)
    l = re.sub(r"\{(\w)\}", r"\1", l)        # x^{2} = x^2
    return re.sub(r"\s+", "", l)

casos = []
for latex in FORMULAS_2D + TEXTOS["desarrollo"]["formulas_2d"] + TEXTOS["evaluacion"]["formulas_2d"]:
    img = _mathtext(latex).convert("RGB")
    fondo = Image.new("RGB", (img.width + 40, img.height + 40), (245, 245, 242)); fondo.paste(img, (20, 20))
    casos.append(("2d", latex, fondo))
for texto, latex in FORMULAS + TEXTOS["desarrollo"]["formulas"] + TEXTOS["evaluacion"]["formulas"]:
    f = ImageFont.truetype(str(FUENTE), 46)
    img = Image.new("RGB", (900, 90), (245, 245, 242)); ImageDraw.Draw(img).text((20, 15), texto, font=f, fill=(20, 20, 20))
    casos.append(("lineal", latex, img))

t0 = time.perf_counter()
from pix2tex.cli import LatexOCR
modelo = LatexOCR()
carga = time.perf_counter() - t0
ok = {"2d": 0, "lineal": 0}; tot = {"2d": 0, "lineal": 0}; tiempos = []
for tipo, esperado, img in casos:
    t = time.perf_counter(); salida = modelo(img); tiempos.append(time.perf_counter() - t)
    tot[tipo] += 1; acierto = n(salida) == n(esperado); ok[tipo] += acierto
    print(f"{tipo:6} {'OK ' if acierto else 'MAL'} esperado={esperado!r:32} pix2tex={salida!r}")
tiempos.sort()
print(f"\n2D exactas {ok['2d']}/{tot['2d']} · lineales exactas {ok['lineal']}/{tot['lineal']}")
print(f"carga del modelo {carga:.1f} s · p50 {tiempos[len(tiempos)//2]*1000:.0f} ms · p95 {tiempos[int(len(tiempos)*0.95)-1]*1000:.0f} ms")
print(f"memoria máxima {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024:.0f} MB")
