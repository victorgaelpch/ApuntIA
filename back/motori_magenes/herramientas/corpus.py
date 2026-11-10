"""Corpus sintético etiquetado para evaluar OCR, fórmulas y PDF (BACK-12/13/14/15, FULL-19).

Cada muestra trae la imagen y el TEXTO REAL que contiene, para medir errores
sin usar fotos privadas de alumnos. Es reproducible (semilla fija) y legal (solo
fuentes libres: DejaVu, incluida en matplotlib, y las tipografías Hershey de
OpenCV).

Limitación declarada: la «letra manuscrita» usa la tipografía Hershey Script de
OpenCV con temblor aleatorio. Se parece a la escritura a mano mucho menos que
una foto real, así que sus métricas son optimistas; las fotos reales deben
evaluarse aparte con permiso de sus autores (ver docs/evaluacion.md).

    python -m herramientas.corpus ../bd/corpus      # guarda imágenes + verdad.json
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FUENTE = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
FUENTE_NEGRITA = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans-Bold.ttf"

TEXTO_CLASE = [
    "Derivadas",
    "La derivada mide la razón de cambio.",
    "Si f(x) = x², entonces f'(x) = 2x.",
    "Ejemplo: la función crece más rápido",
    "cuando aumenta la pendiente.",
]

TEXTO_MANUSCRITO = [
    "Tarea para el martes",
    "Leer el capitulo dos",
    "Resolver los ejercicios",
]

FORMULAS = [
    ("x^2 + 2x + 1 = 0", r"x^{2} + 2 x + 1 = 0"),
    ("a/b + c/d", r"\frac{a}{b} + \frac{c}{d}"),
    ("sqrt(x + 1)", r"\sqrt{x + 1}"),
    ("E = m c^2", r"E = m c^{2}"),
]


@dataclass
class Muestra:
    nombre: str
    tipo_fuente: str               # pizarron | cuaderno
    escritura: str                 # impreso | manuscrito | formula
    imagen: np.ndarray             # BGR
    lineas: list[str]              # texto real, en orden de lectura
    latex: list[str] = field(default_factory=list)


def _lienzo(ancho, alto, color=(250, 250, 248)):
    return Image.new("RGB", (ancho, alto), color)


def _a_bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def hoja_cuaderno(ancho=1400, alto=1000, interlineado=56, margen=120) -> Image.Image:
    """Hoja rayada: renglones azules claros y margen rojo."""
    img = _lienzo(ancho, alto, (252, 251, 245))
    d = ImageDraw.Draw(img)
    for y in range(interlineado * 2, alto, interlineado):
        d.line([(0, y), (ancho, y)], fill=(170, 200, 235), width=2)
    d.line([(margen, 0), (margen, alto)], fill=(230, 150, 150), width=2)
    return img


def impreso_cuaderno() -> Muestra:
    img = hoja_cuaderno()
    d = ImageDraw.Draw(img)
    y = 2 * 56 - 44
    for i, linea in enumerate(TEXTO_CLASE):
        fuente = ImageFont.truetype(str(FUENTE_NEGRITA if i == 0 else FUENTE), 46 if i == 0 else 34)
        d.text((150, y), linea, font=fuente, fill=(25, 30, 60))
        y += 112 if i == 0 else 112
    return Muestra("impreso_cuaderno", "cuaderno", "impreso", _a_bgr(img), TEXTO_CLASE)


def impreso_pizarron() -> Muestra:
    """Pizarrón blanco inclinado sobre una pared, con marcador negro y azul."""
    plano = _lienzo(1300, 820, (244, 244, 240))
    d = ImageDraw.Draw(plano)
    d.rectangle([0, 0, 1299, 819], outline=(120, 120, 120), width=10)
    y = 70
    for i, linea in enumerate(TEXTO_CLASE):
        fuente = ImageFont.truetype(str(FUENTE_NEGRITA if i == 0 else FUENTE), 52 if i == 0 else 40)
        d.text((70, y), linea, font=fuente, fill=(20, 20, 20) if i % 2 == 0 else (20, 50, 160))
        y += 140
    plano = _a_bgr(plano)
    h, w = plano.shape[:2]
    foto = np.empty((1200, 1600, 3), np.uint8)
    foto[:] = (75, 88, 96)
    origen = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    destino = np.float32([[160, 140], [1450, 210], [1410, 1060], [120, 990]])
    cv2.warpPerspective(plano, cv2.getPerspectiveTransform(origen, destino), (1600, 1200),
                        dst=foto, borderMode=cv2.BORDER_TRANSPARENT)
    return Muestra("impreso_pizarron", "pizarron", "impreso", foto, TEXTO_CLASE)


def manuscrito_cuaderno(semilla=3) -> Muestra:
    """Escritura «a mano» sintética (Hershey Script) sobre hoja rayada."""
    rng = np.random.default_rng(semilla)
    img = _a_bgr(hoja_cuaderno())
    y = 2 * 56 - 10
    for linea in TEXTO_MANUSCRITO:
        x = 150
        for palabra in linea.split():
            dy = int(rng.integers(-4, 5))
            cv2.putText(img, palabra, (x, y + dy), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1.6,
                        (90, 40, 20), 3, cv2.LINE_AA)
            (tw, _), _ = cv2.getTextSize(palabra + " ", cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1.6, 3)
            x += tw + int(rng.integers(0, 12))
        y += 112
    return Muestra("manuscrito_cuaderno", "cuaderno", "manuscrito", img, TEXTO_MANUSCRITO)


TEXTO_MANUSCRITO_DIFICIL = [
    "Repasar integrales",
    "Examen el viernes",
]


def manuscrito_dificil(semilla=5) -> Muestra:
    """Escritura «a mano» más irregular: inclinación, tamaño variable, trazo
    tembloroso y algo de desenfoque. Sigue siendo sintética."""
    rng = np.random.default_rng(semilla)
    img = _a_bgr(hoja_cuaderno())
    y = 2 * 56 + 20
    for linea in TEXTO_MANUSCRITO_DIFICIL:
        capa = np.zeros_like(img)
        x = 160
        for palabra in linea.split():
            escala = float(rng.uniform(1.1, 1.6))
            cv2.putText(capa, palabra, (x, y + int(rng.integers(-8, 9))), cv2.FONT_HERSHEY_SCRIPT_COMPLEX,
                        escala, (255, 255, 255), 2, cv2.LINE_AA)
            (tw, _), _ = cv2.getTextSize(palabra + " ", cv2.FONT_HERSHEY_SCRIPT_COMPLEX, escala, 2)
            x += tw + int(rng.integers(5, 25))
        angulo = float(rng.uniform(-4, 4))
        m = cv2.getRotationMatrix2D((700, y), angulo, 1.0)
        capa = cv2.warpAffine(capa, m, (img.shape[1], img.shape[0]))
        # trazo tembloroso: desplazamiento suave aleatorio
        dx = cv2.GaussianBlur(rng.normal(0, 1, capa.shape[:2]).astype(np.float32), (0, 0), 6) * 25
        dy = cv2.GaussianBlur(rng.normal(0, 1, capa.shape[:2]).astype(np.float32), (0, 0), 6) * 25
        gx, gy = np.meshgrid(np.arange(capa.shape[1], dtype=np.float32), np.arange(capa.shape[0], dtype=np.float32))
        capa = cv2.remap(capa, gx + dx, gy + dy, cv2.INTER_LINEAR)
        tinta = capa[:, :, 0] > 60
        img[tinta] = (100, 45, 25)
        y += 168
    img = cv2.GaussianBlur(img, (3, 3), 0.8)
    return Muestra("manuscrito_dificil", "cuaderno", "manuscrito", img, TEXTO_MANUSCRITO_DIFICIL)


def formulas_pizarron() -> Muestra:
    img = _lienzo(1300, 700, (245, 245, 242))
    d = ImageDraw.Draw(img)
    fuente = ImageFont.truetype(str(FUENTE), 46)
    for i, (texto, _) in enumerate(FORMULAS):
        d.text((90, 70 + i * 150), texto, font=fuente, fill=(20, 20, 20))
    return Muestra("formulas_pizarron", "pizarron", "formula", _a_bgr(img),
                   [t for t, _ in FORMULAS], [l for _, l in FORMULAS])


FORMULAS_2D = [r"x^{2} + 2 x + 1 = 0", r"\frac{a}{b} + \frac{c}{d}", r"\sqrt{x + 1}", r"E = m c^{2}"]


def formulas_2d() -> Muestra:
    """Fórmulas dibujadas como en un libro (superíndices, barras de fracción,
    radicales), con mathtext de matplotlib. Más realistas que formulas_pizarron."""
    from matplotlib import mathtext
    from matplotlib.font_manager import FontProperties
    import io
    img = _lienzo(1300, 900, (245, 245, 242))
    y = 60
    for latex in FORMULAS_2D:
        buf = io.BytesIO()
        mathtext.math_to_image(f"${latex}$", buf, dpi=300, format="png", prop=FontProperties(size=14))
        buf.seek(0)
        f = Image.open(buf).convert("RGBA")
        img.paste(f, (90, y), f)
        y += max(170, f.height + 40)
    return Muestra("formulas_2d", "pizarron", "formula", _a_bgr(img),
                   ["x2 + 2x + 1 = 0", "a/b + c/d", "√(x + 1)", "E = mc2"], FORMULAS_2D)


def pizarron_oscuro() -> Muestra:
    """Pizarrón verde de tiza: texto claro sobre fondo oscuro."""
    img = _lienzo(1300, 760, (30, 70, 55))
    d = ImageDraw.Draw(img)
    y = 60
    for i, linea in enumerate(TEXTO_CLASE):
        fuente = ImageFont.truetype(str(FUENTE_NEGRITA if i == 0 else FUENTE), 48 if i == 0 else 38)
        d.text((70, y), linea, font=fuente, fill=(235, 238, 230))
        y += 135
    return Muestra("pizarron_oscuro", "pizarron", "impreso", _a_bgr(img), TEXTO_CLASE)


def cuaderno_con_sombra() -> Muestra:
    """Hoja fotografiada con la sombra del brazo: el lado derecho queda oscuro."""
    m = impreso_cuaderno()
    h, w = m.imagen.shape[:2]
    grad = np.linspace(1.0, 0.35, w, dtype=np.float32)[None, :, None]
    img = np.clip(m.imagen.astype(np.float32) * grad, 0, 255).astype(np.uint8)
    return Muestra("cuaderno_con_sombra", "cuaderno", "impreso", img, m.lineas)


def pizarron_con_ruido(semilla=11) -> Muestra:
    """Foto con poca luz: ruido gaussiano de sensor."""
    m = impreso_pizarron()
    rng = np.random.default_rng(semilla)
    img = np.clip(m.imagen.astype(np.float32) + rng.normal(0, 22, m.imagen.shape), 0, 255).astype(np.uint8)
    return Muestra("pizarron_con_ruido", "pizarron", "impreso", img, m.lineas)


def corpus() -> list[Muestra]:
    return [impreso_cuaderno(), cuaderno_con_sombra(), impreso_pizarron(), pizarron_con_ruido(), pizarron_oscuro(),
            manuscrito_cuaderno(), manuscrito_dificil(), formulas_pizarron(), formulas_2d()]


if __name__ == "__main__":
    destino = Path(sys.argv[1] if len(sys.argv) > 1 else "corpus")
    destino.mkdir(parents=True, exist_ok=True)
    verdad = {}
    for m in corpus():
        cv2.imwrite(str(destino / f"{m.nombre}.png"), m.imagen)
        verdad[m.nombre] = {"tipo_fuente": m.tipo_fuente, "escritura": m.escritura, "lineas": m.lineas,
                            "latex": m.latex}
        print("guardada", destino / f"{m.nombre}.png")
    (destino / "verdad.json").write_text(json.dumps(verdad, ensure_ascii=False, indent=2), encoding="utf-8")
