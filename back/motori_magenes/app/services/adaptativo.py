"""Reconocimiento adaptativo por región (BACK-28).

Sustituye al respaldo único de BACK-14 (un solo segundo intento) por una lectura
que se ADAPTA a cada región y se decide por evidencia:

1. Variantes por región. Cada bloque dudoso se vuelve a leer sobre recortes
   preparados de forma distinta (ampliado, ampliado y binarizado, contraste local
   CLAHE, sombra compensada). La foto y el recorte original no se modifican. Se
   queda la lectura con mejor confianza; como todas las da el MISMO motor, sus
   confianzas sí son comparables (no se comparan confianzas de motores distintos).
2. Consenso. Un bloque que el OCR dio por «reconocido» se relee una vez con otra
   variante: si las dos lecturas no coinciden, el bloque pasa a revisión con la otra
   lectura como alternativa. Así se detectan errores con confianza alta, que es lo
   que la confianza sola no avisa (medido en BACK-28: «eltema» con 0,91).
3. Fórmulas. Las regiones con aspecto matemático se releen como una sola línea con
   la lista de caracteres matemáticos de Tesseract, y se aceptan solo si el texto se
   convierte en LaTeX válido. Una fórmula queda «reconocida» únicamente si dos
   lecturas independientes dan el MISMO LaTeX con buena confianza; si no, queda para
   revisar con su recorte y las alternativas.
4. Nada se inventa. Las alternativas son lecturas reales del motor, como mucho
   tres; lo ilegible queda vacío con su recorte (como en BACK-14). Nunca se
   corrige un número ni se «completa» una palabra.
5. Límites. Variantes por bloque, bloques revisados y segundos por página son
   configurables (RECONOCIMIENTO_MAX_*): no hay bucles ni costes sin control.

Cada bloque guarda su procedencia: motor, versión, variante, modo de
segmentación y cuántas lecturas se compararon.
"""

import re
import time
import unicodedata
from dataclasses import dataclass

import cv2
import numpy as np

from app.core.config import settings
from app.services import formulas
from app.services.manuscrito import MARGEN, zonas_sin_texto
from app.services.ocr import UMBRAL_INCIERTO, BloqueOCR, MotorOCR, agrupar

VERSION = "adaptativo/1"
MAX_ALTERNATIVAS = 3
SIMBOLOS_MAT = set("=+-*/^√∫∑Σ²³<>≤≥≠≈πΔθ_")
LISTA_FORMULAS = ("-c tessedit_char_whitelist="
                  "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-=*/^_().,<>")  # sin comillas (shlex)


@dataclass
class Lectura:
    texto: str
    confianza: float
    minima: float
    dudosas: list[str]
    variante: str
    psm: int
    latex: str | None = None
    latex_valido: bool = False

    @property
    def fuerza(self) -> float:
        """Para comparar lecturas del mismo motor: la media y la palabra más dudosa."""
        return min(self.confianza, self.minima)


# ------------------------------------------------------------------ variantes de un recorte

def _ampliar(gris: np.ndarray, factor: float = 2.0) -> np.ndarray:
    return cv2.resize(gris, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC)


def _otsu(gris: np.ndarray) -> np.ndarray:
    return cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def _clahe(gris: np.ndarray) -> np.ndarray:
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gris)


def _sin_sombra(gris: np.ndarray) -> np.ndarray:
    """Divide entre el fondo estimado (mediana grande): aplana sombras dentro del recorte
    sin umbralizar, así que conserva los trazos finos, los puntos y las tildes."""
    k = max(15, (min(gris.shape[:2]) // 4) | 1)
    fondo = cv2.medianBlur(gris, min(k, 99))
    return cv2.normalize(cv2.divide(gris, fondo, scale=255), None, 0, 255, cv2.NORM_MINMAX)


# Orden: de la más parecida a la foto a la más transformada. Sin erosiones ni aperturas:
# borrarían puntos, tildes, signos menos, barras de fracción y subíndices.
VARIANTES = {
    "ampliada_otsu": lambda g: _otsu(_ampliar(g)),          # el segundo intento de BACK-14
    "ampliada": lambda g: _ampliar(g),
    "clahe": lambda g: _ampliar(_clahe(g)),
    "sin_sombra": lambda g: _ampliar(_sin_sombra(g)),
}
VARIANTE_CONSENSO = "ampliada"


def recorte(gris: np.ndarray, bbox: list[int]) -> np.ndarray:
    alto, ancho = gris.shape[:2]
    x0, y0, x1, y1 = bbox
    return gris[max(0, y0 - MARGEN):min(alto, y1 + MARGEN), max(0, x0 - MARGEN):min(ancho, x1 + MARGEN)]


def normalizar(texto: str) -> str:
    """Comparación de lecturas: Unicode NFC y espacios. No toca letras, cifras ni símbolos."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", texto or "")).strip()


def _sin_espacios(texto: str) -> str:
    return re.sub(r"\s+", "", normalizar(texto))


def aspecto_matematico(texto: str) -> bool:
    t = normalizar(texto)
    return len(t) >= 3 and (formulas.es_formula(t) or sum(c in SIMBOLOS_MAT for c in t) >= 2)


# ------------------------------------------------------------------ lectura

class Lector:
    """Lee recortes de UNA página con un presupuesto de tiempo y de lecturas."""

    def __init__(self, gris: np.ndarray, idiomas: str, motor: MotorOCR):
        self.gris = gris
        self.idiomas = idiomas
        self.motor = motor
        self.limite = time.monotonic() + settings.reconocimiento_max_segundos
        self.bloques_revisados = 0
        self.lecturas = 0

    def con_tiempo(self) -> bool:
        return time.monotonic() < self.limite

    def leer(self, bbox: list[int], variante: str, psm: int, config: str = "") -> Lectura | None:
        trozo = recorte(self.gris, bbox)
        if trozo.size == 0 or min(trozo.shape[:2]) < 4:
            return None
        imagen = VARIANTES[variante](trozo)
        self.lecturas += 1
        nuevos = agrupar(self.motor.palabras_config(imagen, self.idiomas, psm, config) if config
                         else self.motor.palabras(imagen, self.idiomas, psm))
        if not nuevos:
            return None
        total = sum(len(b.texto) for b in nuevos)
        conf = sum(b.confianza * len(b.texto) for b in nuevos) / total if total else 0.0
        minima = min((b.minima if b.minima is not None else b.confianza) for b in nuevos)
        return Lectura("\n".join(b.texto for b in nuevos), round(conf, 3), round(minima, 3),
                       [d for b in nuevos for d in b.dudosas], variante, psm)

    def leer_formula(self, bbox: list[int], variante: str) -> Lectura | None:
        """Una línea (psm 7) con solo caracteres matemáticos; vale si da LaTeX válido."""
        lectura = self.leer(bbox, variante, 7, LISTA_FORMULAS)
        if lectura is None or "\n" in lectura.texto:
            return None
        latex, valido = formulas.convertir(lectura.texto)
        lectura.latex, lectura.latex_valido = latex, valido
        lectura.variante += "+formula"
        return lectura if valido else None


def _psm(bloque: BloqueOCR) -> int:
    return 7 if len(bloque.lineas) <= 1 else 6


def _alternativas(elegida: Lectura, lecturas: list[Lectura], latex: bool = False) -> list[dict]:
    """Otras lecturas reales y distintas de la elegida, de la más a la menos confiable."""
    clave = (lambda l: _sin_espacios(l.latex or "")) if latex else (lambda l: normalizar(l.texto))
    vistas, salida = {clave(elegida)}, []
    for l in sorted(lecturas, key=lambda l: -l.fuerza):
        k = clave(l)
        if not k or k in vistas:
            continue
        vistas.add(k)
        alt = {"texto": l.texto, "confianza": l.confianza, "variante": l.variante}
        if latex:
            alt["latex"] = l.latex
        salida.append(alt)
        if len(salida) == MAX_ALTERNATIVAS:
            break
    return salida


def _procedencia(base: dict, lectura: Lectura | None, lecturas: int) -> dict:
    p = dict(base)
    p.update({"variante": lectura.variante if lectura else "pagina", "psm": lectura.psm if lectura else base.get("psm"),
              "lecturas": lecturas})
    return p


def _como_bloque(original: BloqueOCR, l: Lectura) -> BloqueOCR:
    return BloqueOCR(l.texto, l.confianza, original.bbox, l.texto.split("\n"), original.altura_linea,
                     original.tipo, l.dudosas, minima=l.minima)


def revisar_bloque(lector: Lector, b: BloqueOCR, base: dict) -> BloqueOCR:
    psm = _psm(b)
    actual = Lectura(b.texto, b.confianza, b.minima if b.minima is not None else b.confianza, list(b.dudosas),
                     "pagina", base.get("psm", 3))
    lecturas = [actual]
    max_var = max(1, settings.reconocimiento_max_variantes)

    if b.estado == "reconocido":
        # Consenso: una relectura independiente. Si no coincide, se pide revisión.
        otra = lector.leer(b.bbox, VARIANTE_CONSENSO, psm) if lector.con_tiempo() else None
        if otra is not None:
            lecturas.append(otra)
            if normalizar(otra.texto) != normalizar(b.texto):
                # El texto de la página se conserva (ver `elegir`); la otra lectura queda como alternativa.
                b.revision = "lecturas_distintas"
                b.alternativas = _alternativas(actual, lecturas)
                b.procedencia = _procedencia(base, actual, len(lecturas))
                return b
        b.procedencia = _procedencia(base, actual, len(lecturas))
        return b

    # Bloque dudoso: variantes en orden, hasta que dos lecturas coincidan con buena confianza
    # o se agote el presupuesto.
    for nombre in list(VARIANTES)[:max_var]:
        if not lector.con_tiempo():
            break
        l = lector.leer(b.bbox, nombre, psm)
        if l is not None:
            lecturas.append(l)
            if l.fuerza >= 0.85 and normalizar(l.texto) == normalizar(actual.texto):
                break  # confirma la lectura de la página: no hace falta seguir
    elegida, confirmada = elegir(actual, lecturas)
    nuevo = _como_bloque(b, elegida) if elegida is not actual else b
    nuevo.tipo = b.tipo
    if not confirmada:
        nuevo.revision = "sin_confirmar"
    nuevo.alternativas = _alternativas(elegida, lecturas)
    nuevo.procedencia = _procedencia(base, elegida, len(lecturas))
    return nuevo


def elegir(actual: Lectura, lecturas: list[Lectura]) -> tuple[Lectura, bool]:
    """Elige entre lecturas del mismo bloque. Devuelve (lectura elegida, confirmada).

    Lo medido en BACK-28 manda:
      - las variantes ampliadas o binarizadas INFLAN la confianza de Tesseract
        («Lasplantasnecesitanluzsolar.» con 0,90 frente a «Las plantas necesitan luzsolar.» con
        0,69), así que la confianza de preprocesados distintos no sirve para elegir;
      - las variantes de un mismo recorte NO son independientes: comparten la segmentación
        de una sola línea y se equivocan juntas (dos variantes votaron el mismo texto erróneo).
    Por eso la lectura de la página (otra segmentación, sobre la página entera) se conserva
    como principal, salvo la regla de BACK-14 (abajo) o que sea ilegible, y un bloque solo queda
    «confirmado» si una lectura del recorte coincide con la de la página. Las demás se ofrecen como
    alternativas."""
    if actual.fuerza >= UMBRAL_INCIERTO:
        # La regla de BACK-14, que el banco FULL-19 avala: el recorte ampliado y binarizado sustituye a
        # la página si es claramente mejor (+0,05)... y además (BACK-28) si no junta ni separa palabras:
        # perder los espacios es justo el error en que la confianza de las variantes engaña.
        otsu = next((l for l in lecturas if l.variante == "ampliada_otsu"), None)
        if (otsu is not None and otsu.fuerza > actual.fuerza + 0.05
                and abs(len(otsu.texto.split()) - len(actual.texto.split())) <= 1):
            # Sustituye, pero sin confirmar: las otras variantes del recorte no cuentan como
            # confirmación independiente, y la página leyó otra cosa.
            return otsu, False
        confirmada = any(l is not actual and normalizar(l.texto) == normalizar(actual.texto) for l in lecturas)
        return actual, confirmada
    # La página no pudo leerlo: gana el texto que más variantes leen (desempate: confianza),
    # pero sin confirmar, porque las variantes no se confirman entre sí.
    grupos: dict[str, list[Lectura]] = {}
    for l in lecturas:
        if l is not actual:
            grupos.setdefault(normalizar(l.texto), []).append(l)
    if not grupos:
        return actual, False
    mayor = max(grupos.values(), key=lambda g: (len(g), max(x.fuerza for x in g)))
    mejor = max(mayor, key=lambda l: l.fuerza)
    if mejor.fuerza >= actual.fuerza + 0.15:
        return mejor, False
    return actual, False


def intentar_formula(lector: Lector, b: BloqueOCR, base: dict, texto_crudo: str) -> BloqueOCR | None:
    """Relee como fórmula una región con aspecto matemático. None si ninguna lectura es LaTeX válido."""
    if not lector.con_tiempo() or not aspecto_matematico(texto_crudo):
        return None
    lecturas = []
    for variante in ("ampliada", "ampliada_otsu"):
        if not lector.con_tiempo():
            break
        l = lector.leer_formula(b.bbox, variante)
        if l is not None:
            lecturas.append(l)
    # La lectura normal (sin lista de caracteres) también cuenta si se convierte bien.
    latex, valido = formulas.convertir(texto_crudo) if formulas.es_formula(texto_crudo) else (None, False)
    if valido:
        lecturas.append(Lectura(texto_crudo, b.confianza, b.minima if b.minima is not None else b.confianza,
                                list(b.dudosas), "pagina", base.get("psm", 3), latex, True))
    # Que el texto se convierta en LaTeX no basta: con una lectura muy dudosa sería inventar.
    lecturas = [l for l in lecturas if l.fuerza >= UMBRAL_INCIERTO]
    if not lecturas:
        return None
    elegida = max(lecturas, key=lambda l: l.fuerza)
    iguales = sum(1 for l in lecturas if _sin_espacios(l.latex) == _sin_espacios(elegida.latex))
    nuevo = BloqueOCR(elegida.texto, elegida.confianza, b.bbox, [elegida.texto], b.altura_linea, "formula",
                      elegida.dudosas, recortar=True, minima=elegida.minima)
    nuevo.latex, nuevo.latex_valido = elegida.latex, True
    # «Reconocida» solo con dos lecturas independientes iguales y buena confianza (estado por confianza).
    if iguales < 2 or elegida.fuerza < 0.85:
        nuevo.confianza = min(nuevo.confianza, 0.79)
        nuevo.revision = "formula_sin_confirmar"
    nuevo.alternativas = _alternativas(elegida, lecturas, latex=True)
    nuevo.procedencia = _procedencia(base, elegida, len(lecturas))
    return nuevo


def leer_adaptativo(gris: np.ndarray, bloques: list[BloqueOCR], idiomas: str, motor: MotorOCR,
                    base: dict) -> list[BloqueOCR]:
    """Equivalente adaptativo de `manuscrito.leer_con_respaldo` (BACK-14)."""
    lector = Lector(gris, idiomas, motor)
    resultado = []
    for b in bloques:
        if lector.bloques_revisados >= settings.reconocimiento_max_bloques or not lector.con_tiempo():
            b.procedencia = _procedencia(base, None, 1)
            if b.estado == "no_reconocido":
                b = BloqueOCR("", b.confianza, b.bbox, [], b.altura_linea, "manuscrito", b.dudosas, recortar=True,
                              minima=b.minima, procedencia=b.procedencia)
            elif b.estado == "incierto":
                b.recortar = True
            resultado.append(b)
            continue
        lector.bloques_revisados += 1
        crudo = b.texto
        b = revisar_bloque(lector, b, base)
        if b.estado != "reconocido":
            formula = intentar_formula(lector, b, base, crudo if not aspecto_matematico(b.texto) else b.texto)
            if formula is not None and (b.estado == "no_reconocido" or formula.confianza >= b.confianza - 0.05):
                resultado.append(formula)
                continue
        if b.estado == "no_reconocido":
            # No se inventa texto: queda vacío con su recorte (y las lecturas descartadas no se muestran
            # como alternativas: su confianza es demasiado baja para proponerlas).
            b = BloqueOCR("", b.confianza, b.bbox, [], b.altura_linea, "manuscrito", b.dudosas, recortar=True,
                          minima=b.minima, procedencia=b.procedencia)
        elif b.estado == "incierto":
            b.recortar = True
        resultado.append(b)
    for z in zonas_sin_texto(gris, resultado):
        z.procedencia = {**base, "variante": "zona_sin_texto", "lecturas": 0}
        resultado.append(z)
    resultado.sort(key=lambda b: (b.bbox[1], b.bbox[0]))
    return resultado


def refinar_formulas(gris: np.ndarray, bloques: list[BloqueOCR], idiomas: str, motor: MotorOCR,
                     base: dict) -> list[BloqueOCR]:
    """Relee las fórmulas que `separar_formulas` dejó sin confirmar (LaTeX inválido o dudoso)."""
    lector = Lector(gris, idiomas, motor)
    salida = []
    for b in bloques:
        ya_releida = str(b.procedencia.get("variante", "")).endswith("+formula")
        if b.tipo == "formula" and b.texto and not ya_releida and (b.estado != "reconocido" or not getattr(b, "latex_valido", False)):
            nueva = intentar_formula(lector, b, base, b.texto)
            if nueva is not None:
                salida.append(nueva)
                continue
            if not b.procedencia:
                b.procedencia = _procedencia(base, None, 1)
        salida.append(b)
    return salida
