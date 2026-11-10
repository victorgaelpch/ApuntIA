"""Corpus de casos DIFÍCILES para el reconocimiento adaptativo (BACK-28).

Complementa a `corpus.py` (FULL-19) con lo que el issue BACK-28 señala como
problemático: tinta tenue, letra pequeña, palabras juntas, fotos inclinadas,
sombras fuertes sobre cuadrícula, escritura «a mano» irregular, fórmulas con
fracciones, raíces, potencias y subíndices, páginas mixtas y fotos borrosas.

Dos particiones con textos y semillas DISTINTOS, para no ajustar el sistema a
los ejemplos conocidos:
  - «desarrollo»: con estas se probaron y ajustaron los cambios;
  - «evaluacion»: solo se usan para medir el resultado final.

Todo es sintético (fuentes libres DejaVu y Hershey, semillas fijas): no hay
fotos ni datos de personas. Limitación declarada: la tipografía Hershey no
tiene acentos, así que los «manuscritos» van sin tildes, y se parece a la letra
real menos que una foto; las métricas de manuscritos son optimistas.

    python -m herramientas.corpus_dificil ../bd/corpus-dificil   # imágenes + verdad.json
"""

import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from herramientas.corpus import FUENTE, FUENTE_NEGRITA, Muestra, _a_bgr, _lienzo, hoja_cuaderno

TEXTOS = {
    "desarrollo": {
        "impreso": ["La energía cinética depende", "de la masa y la velocidad.", "Unidades: julios (J)."],
        "pequeno": ["El átomo tiene protones y neutrones.", "Los electrones giran en orbitales.",
                    "La carga del protón es positiva.", "La masa del electrón es muy pequeña."],
        "manuscrito": ["Repasar el tema tres", "Entregar la practica", "Estudiar para el lunes"],
        "unidas": ["La fotosíntesis produce oxígeno.", "Las plantas necesitan luz solar."],
        "formulas": [("v = d / t", r"v = \frac{d}{t}"), ("F = m a", r"F = m a"),
                     ("x_1 + x_2 = 10", r"x_{1} + x_{2} = 10"), ("a^2 + b^2 = c^2", r"a^{2} + b^{2} = c^{2}")],
        "formulas_2d": [r"\frac{x + 1}{2}", r"\sqrt{a^{2} + b^{2}}", r"y = x_{1}^{2}"],
    },
    "evaluacion": {
        "impreso": ["La presión es fuerza por área.", "Se mide en pascales.", "Ejemplo: un émbolo hidráulico."],
        "pequeno": ["La célula es la unidad de la vida.", "El núcleo guarda el material genético.",
                    "La membrana regula lo que entra.", "Las mitocondrias producen energía."],
        "manuscrito": ["Leer el capitulo cinco", "Traer la calculadora", "Revisar las respuestas"],
        "unidas": ["La gravedad atrae los cuerpos.", "Newton describió sus leyes."],
        "formulas": [("p = F / A", r"p = \frac{F}{A}"), ("E = m g h", r"E = m g h"),
                     ("y_0 + y_1 = 5", r"y_{0} + y_{1} = 5"), ("r^2 = x^2 + y^2", r"r^{2} = x^{2} + y^{2}")],
        "formulas_2d": [r"\frac{a - b}{3}", r"\sqrt{x^{2} + 1}", r"z = y_{2}^{3}"],
    },
}


def _texto(img: Image.Image, lineas, x, y, tam, color, salto, negrita_primera=False):
    d = ImageDraw.Draw(img)
    for i, linea in enumerate(lineas):
        fuente = ImageFont.truetype(str(FUENTE_NEGRITA if negrita_primera and i == 0 else FUENTE), tam)
        d.text((x, y), linea, font=fuente, fill=color)
        y += salto
    return y


def _manuscrito(img: np.ndarray, lineas, rng, y0, escala=(1.2, 1.6), grosor=2, salto=150, color=(110, 50, 25),
                temblor=22.0):
    """Escritura «a mano» sintética: Hershey Script con tamaño, inclinación y trazo irregulares."""
    y = y0
    for linea in lineas:
        capa = np.zeros(img.shape[:2], np.uint8)
        x = 150
        for palabra in linea.split():
            e = float(rng.uniform(*escala))
            cv2.putText(capa, palabra, (x, y + int(rng.integers(-7, 8))), cv2.FONT_HERSHEY_SCRIPT_COMPLEX, e, 255,
                        grosor, cv2.LINE_AA)
            (tw, _), _ = cv2.getTextSize(palabra + " ", cv2.FONT_HERSHEY_SCRIPT_COMPLEX, e, grosor)
            x += tw + int(rng.integers(0, 18))
        m = cv2.getRotationMatrix2D((700, y), float(rng.uniform(-3.5, 3.5)), 1.0)
        capa = cv2.warpAffine(capa, m, (img.shape[1], img.shape[0]))
        dx = cv2.GaussianBlur(rng.normal(0, 1, capa.shape).astype(np.float32), (0, 0), 6) * temblor
        dy = cv2.GaussianBlur(rng.normal(0, 1, capa.shape).astype(np.float32), (0, 0), 6) * temblor
        gx, gy = np.meshgrid(np.arange(capa.shape[1], dtype=np.float32), np.arange(capa.shape[0], dtype=np.float32))
        capa = cv2.remap(capa, gx + dx, gy + dy, cv2.INTER_LINEAR)
        alfa = (capa.astype(np.float32) / 255)[:, :, None]
        img[:] = (img * (1 - alfa) + np.array(color, np.float32) * alfa).astype(np.uint8)
        y += salto
    return img


def _sombra(img: np.ndarray, minimo=0.3, diagonal=True) -> np.ndarray:
    h, w = img.shape[:2]
    gx, gy = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    t = (gx + gy) / 2 if diagonal else gx
    factor = (1 - (1 - minimo) * np.clip(t * 1.4 - 0.2, 0, 1)).astype(np.float32)[:, :, None]
    return np.clip(img.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def _cuadricula(ancho=1400, alto=1000, paso=36) -> Image.Image:
    img = _lienzo(ancho, alto, (252, 252, 248))
    d = ImageDraw.Draw(img)
    for x in range(0, ancho, paso):
        d.line([(x, 0), (x, alto)], fill=(175, 200, 220), width=1)
    for y in range(0, alto, paso):
        d.line([(0, y), (ancho, y)], fill=(175, 200, 220), width=1)
    return img


def _mathtext(latex: str, dpi=300) -> Image.Image:
    from matplotlib import mathtext
    from matplotlib.font_manager import FontProperties
    buf = io.BytesIO()
    mathtext.math_to_image(f"${latex}$", buf, dpi=dpi, format="png", prop=FontProperties(size=14))
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


# ------------------------------------------------------------------ casos

def tinta_tenue(p, t) -> Muestra:
    """Lápiz claro / marcador gastado: contraste muy bajo con el papel."""
    img = hoja_cuaderno()
    _texto(img, t["impreso"], 150, 120, 36, (165, 170, 185), 112)
    return Muestra(f"tinta_tenue_{p}", "cuaderno", "impreso", _a_bgr(img), t["impreso"])


def letra_pequena(p, t) -> Muestra:
    """Letra de ~16 px en una foto de 1000 px: Tesseract lee mejor ~30 px."""
    img = _lienzo(1000, 700, (250, 250, 247))
    _texto(img, t["pequeno"], 60, 80, 17, (30, 30, 40), 40)
    return Muestra(f"letra_pequena_{p}", "pizarron", "impreso", _a_bgr(img), t["pequeno"])


def sombra_cuadricula(p, t) -> Muestra:
    """Hoja cuadriculada con la sombra del brazo en diagonal."""
    img = _cuadricula()
    _texto(img, t["impreso"], 110, 120, 36, (25, 30, 60), 120)
    return Muestra(f"sombra_cuadricula_{p}", "cuaderno", "impreso", _sombra(_a_bgr(img), 0.28), t["impreso"])


def foto_girada(p, t, angulo) -> Muestra:
    """Hoja girada sin que se vea su borde (no hay perspectiva que corregir)."""
    img = _a_bgr(hoja_cuaderno())
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    _texto(pil, t["impreso"], 150, 140, 38, (25, 30, 60), 112)
    img = _a_bgr(pil)
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angulo, 1.0)
    img = cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REPLICATE)
    return Muestra(f"foto_girada_{p}", "cuaderno", "impreso", img, t["impreso"])


def palabras_unidas(p, t) -> Muestra:
    """Letra con el espacio entre palabras casi nulo y algo de desenfoque."""
    img = _lienzo(1300, 500, (248, 248, 245))
    d = ImageDraw.Draw(img)
    fuente = ImageFont.truetype(str(FUENTE), 40)
    y = 90
    for linea in t["unidas"]:
        x = 80
        for palabra in linea.split():
            d.text((x, y), palabra, font=fuente, fill=(25, 25, 35))
            x += int(d.textlength(palabra, font=fuente)) + 5
        y += 130
    return Muestra(f"palabras_unidas_{p}", "pizarron", "impreso", cv2.GaussianBlur(_a_bgr(img), (3, 3), 1.0),
                   t["unidas"])


def manuscrito_irregular(p, t, semilla) -> Muestra:
    """Caso A del issue: renglones, sombra y escritura irregular."""
    rng = np.random.default_rng(semilla)
    img = _a_bgr(hoja_cuaderno())
    img = _manuscrito(img, t["manuscrito"], rng, 2 * 56 + 30)
    return Muestra(f"manuscrito_irregular_{p}", "cuaderno", "manuscrito", _sombra(img, 0.5, diagonal=False),
                   t["manuscrito"])


def manuscrito_fino(p, t, semilla) -> Muestra:
    """Trazo fino y pequeño, tinta azul clara."""
    rng = np.random.default_rng(semilla)
    img = _a_bgr(hoja_cuaderno())
    img = _manuscrito(img, t["manuscrito"], rng, 2 * 56 + 30, escala=(1.0, 1.25), grosor=1, color=(170, 90, 40),
                      temblor=14.0)
    return Muestra(f"manuscrito_fino_{p}", "cuaderno", "manuscrito", img, t["manuscrito"])


def formulas_lineales(p, t) -> Muestra:
    """Caso B: fórmulas en texto lineal con subíndices y potencias escritos con _ y ^."""
    img = _lienzo(1300, 720, (245, 245, 242))
    _texto(img, [f for f, _ in t["formulas"]], 90, 70, 46, (20, 20, 20), 150)
    return Muestra(f"formulas_lineales_{p}", "pizarron", "formula", _a_bgr(img),
                   [f for f, _ in t["formulas"]], [l for _, l in t["formulas"]])


def formulas_2d(p, t) -> Muestra:
    """Caso B: fracciones, raíces y potencias en dos dimensiones."""
    img = _lienzo(1300, 820, (245, 245, 242))
    y = 70
    for latex in t["formulas_2d"]:
        f = _mathtext(latex)
        img.paste(f, (90, y), f)
        y += max(200, f.height + 50)
    return Muestra(f"formulas_2d_{p}", "pizarron", "formula", _a_bgr(img), [], list(t["formulas_2d"]))


def pagina_mixta(p, t) -> Muestra:
    """Caso C: explicación + fórmula + tabla + diagrama en una misma hoja."""
    img = _lienzo(1400, 1300, (250, 250, 247))
    d = ImageDraw.Draw(img)
    y = _texto(img, t["impreso"][:2], 80, 60, 38, (25, 30, 60), 80)
    formula, _ = t["formulas"][0]
    _texto(img, [formula], 80, y + 20, 44, (20, 20, 20), 0)
    x0, y0 = 80, y + 160
    celdas = [["Magnitud", "Unidad"], ["Masa", "kilogramo"], ["Tiempo", "segundo"]]
    fuente = ImageFont.truetype(str(FUENTE), 34)
    for i, fila in enumerate(celdas):
        for j, celda in enumerate(fila):
            d.text((x0 + 25 + j * 380, y0 + 30 + i * 100), celda, font=fuente, fill=(25, 30, 60))
    for i in range(len(celdas) + 1):
        d.line([(x0, y0 + i * 100), (x0 + 760, y0 + i * 100)], fill=(25, 30, 60), width=3)
    for j in range(3):
        d.line([(x0 + j * 380, y0), (x0 + j * 380, y0 + 300)], fill=(25, 30, 60), width=3)
    yd = y0 + 380
    d.ellipse([120, yd, 420, yd + 260], outline=(20, 20, 20), width=7)
    d.rectangle([800, yd, 1150, yd + 260], outline=(20, 20, 20), width=7)
    d.line([(430, yd + 130), (790, yd + 130)], fill=(20, 20, 20), width=7)
    lineas = t["impreso"][:2] + [formula] + [" ".join(f) for f in celdas]
    return Muestra(f"pagina_mixta_{p}", "cuaderno", "mixto", _a_bgr(img), lineas, [t["formulas"][0][1]])


def foto_borrosa(p, t) -> Muestra:
    """Caso D: foto movida y pequeña. Lo correcto es avisar, no transcribir de más."""
    img = _lienzo(1300, 600, (248, 248, 245))
    _texto(img, t["impreso"], 80, 90, 34, (30, 30, 40), 130)
    img = cv2.resize(_a_bgr(img), (520, 240), interpolation=cv2.INTER_AREA)
    img = cv2.GaussianBlur(img, (0, 0), 2.6)
    return Muestra(f"foto_borrosa_{p}", "pizarron", "borrosa", img, t["impreso"])


def corpus_dificil(particion: str) -> list[Muestra]:
    t = TEXTOS[particion]
    s = 0 if particion == "desarrollo" else 100
    angulo = 6.0 if particion == "desarrollo" else -7.0
    return [tinta_tenue(particion, t), letra_pequena(particion, t), sombra_cuadricula(particion, t),
            foto_girada(particion, t, angulo), palabras_unidas(particion, t),
            manuscrito_irregular(particion, t, 21 + s), manuscrito_fino(particion, t, 33 + s),
            formulas_lineales(particion, t), formulas_2d(particion, t), pagina_mixta(particion, t),
            foto_borrosa(particion, t)]


if __name__ == "__main__":
    destino = Path(sys.argv[1] if len(sys.argv) > 1 else "corpus-dificil")
    verdad = {}
    for particion in TEXTOS:
        (destino / particion).mkdir(parents=True, exist_ok=True)
        for m in corpus_dificil(particion):
            cv2.imwrite(str(destino / particion / f"{m.nombre}.png"), m.imagen)
            verdad[m.nombre] = {"particion": particion, "tipo_fuente": m.tipo_fuente, "escritura": m.escritura,
                                "lineas": m.lineas, "latex": m.latex}
            print("guardada", destino / particion / f"{m.nombre}.png")
    (destino / "verdad.json").write_text(json.dumps(verdad, ensure_ascii=False, indent=2), encoding="utf-8")
