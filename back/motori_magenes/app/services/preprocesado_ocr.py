"""Preprocesado de páginas para OCR, por perfil de fuente (BACK-12).

Reutiliza las etapas existentes (perspectiva, normalización de iluminación) pero
con perfiles distintos, porque la tinta fina de un cuaderno no se trata igual
que el marcador de un pizarrón:

  pizarron: perspectiva → gris → invertir si es de tiza (fondo oscuro) →
            [normalizar iluminación si es desigual] → [mediana 3x3 si hay ruido]
  cuaderno: perspectiva → canal ROJO (los renglones azules y el margen rojo casi
            desaparecen; la tinta negra o azul oscuro se mantiene) →
            [normalizar iluminación si es desigual] → quitar solo los renglones
            (líneas largas y equiespaciadas), conservando tablas y fracciones

En los dos perfiles, la copia para el OCR (no la vista) pierde además la cuadrícula de
las tablas (rectas largas horizontales y verticales): Tesseract las confundía con texto o descartaba
las filas enteras (FULL-24: de 8 celdas de una tabla fotografiada leía 0).

La perspectiva solo se corrige si el cuadrilátero detectado es de verdad el borde del
pizarrón o de la hoja: si fuera de él queda el mismo papel con tinta, es una tabla o un
recuadro DENTRO de la hoja y recortar perdería lo de alrededor (FULL-24: se perdía el título).

Las etapas entre corchetes son ADAPTATIVAS: se midió que en una foto limpia
empeoran el OCR (la mediana borraba tildes; la normalización adelgazaba trazos),
así que solo se aplican cuando la imagen lo necesita.

Ninguna etapa usa erosiones ni umbrales duros: los trazos finos, subíndices y
signos matemáticos se conservan. El original nunca se modifica (se guarda
aparte). Las advertencias de calidad avisan cuando no se puede garantizar la
lectura.
"""

from dataclasses import dataclass, field

import cv2
import numpy as np

from app.services.mejora import normalizar_iluminacion
from app.services.perspectiva import detectar_pizarron, rectificar
from app.services.procesamiento import a_bgr, redimensionar

LADO_MAX_OCR = 2400       # más resolución que la vista: el OCR la aprovecha
LADO_MIN_OCR = 1400       # por debajo se amplía (Tesseract lee mejor letras de ~30 px)
UMBRAL_BORROSA = 40.0     # varianza del laplaciano a 1000 px
UMBRAL_OSCURA = 60        # luminancia media


@dataclass
class Preprocesado:
    imagen_ocr: np.ndarray            # gris, lista para el OCR
    imagen_vista: np.ndarray          # BGR enderezada, mismas coordenadas que imagen_ocr
    psm: int                          # modo de segmentación de Tesseract
    perspectiva: str
    advertencias: list[str] = field(default_factory=list)
    inclinacion: float = 0.0          # grados corregidos al enderezar (BACK-28)


def advertencias_calidad(img: np.ndarray) -> list[str]:
    avisos = []
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if min(gris.shape) < 600:
        avisos.append("BAJA_RESOLUCION")
    escala = 1000 / max(gris.shape)
    pequena = cv2.resize(gris, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA) if escala < 1 else gris
    if cv2.Laplacian(pequena, cv2.CV_64F).var() < UMBRAL_BORROSA:
        avisos.append("IMAGEN_BORROSA")
    return avisos


UMBRAL_ILUMINACION = 45   # diferencia entre las zonas más claras y oscuras del fondo
UMBRAL_RUIDO = 6.0        # desviación estimada del ruido del sensor


def iluminacion_desigual(gris: np.ndarray) -> bool:
    pequena = cv2.resize(gris, (64, 64), interpolation=cv2.INTER_AREA)
    fondo = cv2.morphologyEx(pequena, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return float(np.percentile(fondo, 95) - np.percentile(fondo, 5)) > UMBRAL_ILUMINACION


def ruido_estimado(gris: np.ndarray) -> float:
    """Estimación robusta (MAD) del ruido a partir del laplaciano."""
    lap = cv2.Laplacian(gris, cv2.CV_64F)
    return float(np.median(np.abs(lap - np.median(lap))) / 0.6745)


def _escalar_para_ocr(img: np.ndarray) -> np.ndarray:
    lado = max(img.shape[:2])
    if lado > LADO_MAX_OCR:
        return redimensionar(img, LADO_MAX_OCR)
    if lado < LADO_MIN_OCR:
        f = min(2.0, LADO_MIN_OCR / lado)
        return cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    return img


def quitar_renglones(gris: np.ndarray) -> np.ndarray:
    """Elimina el rayado del cuaderno: líneas horizontales que cruzan casi toda
    la hoja y aparecen a intervalos regulares (al menos 4). Una línea de tabla o
    una barra de fracción no cumple ambas condiciones y se conserva."""
    alto, ancho = gris.shape
    tinta = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 10)
    horizontales = cv2.morphologyEx(tinta, cv2.MORPH_OPEN,
                                    cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, ancho // 3), 1)))
    perfil = (horizontales > 0).sum(axis=1)
    filas = np.where(perfil > 0.6 * ancho)[0]
    if len(filas) == 0:
        return gris
    # Agrupar filas contiguas en líneas y comprobar el espaciado regular
    grupos, actual = [], [filas[0]]
    for f in filas[1:]:
        if f - actual[-1] <= 2:
            actual.append(f)
        else:
            grupos.append(actual)
            actual = [f]
    grupos.append(actual)
    centros = np.array([np.mean(g) for g in grupos])
    if len(centros) < 4:
        return gris
    pasos = np.diff(centros)
    mediana = np.median(pasos)
    if mediana < 15 or np.mean(np.abs(pasos - mediana) < 0.2 * mediana) < 0.7:
        return gris  # no es un rayado regular
    mascara = np.zeros_like(gris)
    for g in grupos:
        y0, y1 = max(0, g[0] - 1), min(alto, g[-1] + 2)
        mascara[y0:y1] = horizontales[y0:y1]
    mascara = cv2.dilate(mascara, np.ones((3, 1), np.uint8))
    # Solo se rellena la línea; donde un trazo la cruza, inpaint recupera la tinta.
    return cv2.inpaint(gris, mascara, 2, cv2.INPAINT_TELEA)


def _contenido_fuera(gris: np.ndarray, esquinas: np.ndarray) -> bool:
    """¿Hay papel con tinta FUERA del cuadrilátero? Entonces es una figura dentro de la hoja
    (tabla, recuadro), no su borde: un pizarrón o una hoja sobre la mesa tienen alrededor
    otro fondo (pared, mesa), no el mismo papel escrito."""
    dentro = np.zeros(gris.shape, np.uint8)
    cv2.fillConvexPoly(dentro, esquinas.astype(np.int32), 255)
    fuera = dentro == 0
    if fuera.mean() < 0.05:
        return False
    papel_dentro, papel_fuera = np.percentile(gris[~fuera], 75), np.percentile(gris[fuera], 75)
    if abs(float(papel_dentro) - float(papel_fuera)) > 30:
        return False  # otro fondo alrededor: es el borde de verdad
    tinta = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 15)
    tinta = cv2.morphologyEx(tinta, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return float((tinta[fuera] > 0).mean()) > 0.003


def corregir_perspectiva_hoja(original: np.ndarray) -> tuple[np.ndarray, str]:
    deteccion = detectar_pizarron(original)
    if deteccion.esquinas is None:
        return original, "no_detectada"
    if _contenido_fuera(cv2.cvtColor(original, cv2.COLOR_BGR2GRAY), deteccion.esquinas):
        return original, "figura_interior"
    return rectificar(original, deteccion.esquinas), "corregida"


def quitar_lineas_largas(gris: np.ndarray) -> np.ndarray:
    """Borra de la copia para el OCR la cuadrícula de una tabla (rectas horizontales y verticales
    largas). Las barras de fracción y los trazos de letra son mucho más cortos."""
    alto, ancho = gris.shape
    tinta = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 10)
    horizontales = cv2.morphologyEx(tinta, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, ancho // 4), 1)))
    verticales = cv2.morphologyEx(tinta, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, alto // 6))))
    # Solo una CUADRÍCULA (≥ 3 rectas horizontales y ≥ 2 verticales): un recuadro suelto o las
    # figuras de un diagrama se dejan, porque sin sus lados Tesseract lee los trozos como letras.
    n_h = cv2.connectedComponents(horizontales)[0] - 1
    n_v = cv2.connectedComponents(verticales)[0] - 1
    if n_h < 3 or n_v < 2:
        return gris
    mascara = cv2.dilate(cv2.bitwise_or(horizontales, verticales), np.ones((3, 3), np.uint8))
    return cv2.inpaint(gris, mascara, 2, cv2.INPAINT_TELEA)


INCLINACION_MAX = 15.0    # grados que se buscan al enderezar
INCLINACION_MIN = 0.7     # por debajo no se gira (Tesseract lo tolera y girar suaviza la letra)


def estimar_inclinacion(img: np.ndarray) -> float:
    """Ángulo (grados, antihorario) que endereza las líneas de texto de la foto (BACK-28).

    Perfil de proyección: al girar la tinta al ángulo correcto, las filas con texto y las
    vacías se alternan con nitidez y la varianza del perfil horizontal es máxima. Se busca
    primero cada 1° y después cada 0,1°. Devuelve 0 si no hay un máximo claro (página casi
    vacía, un dibujo, o texto ya derecho)."""
    gris = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    escala = 800 / max(gris.shape)
    if escala < 1:
        gris = cv2.resize(gris, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)
    tinta = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 25, 15)
    if tinta.mean() < 0.5:  # casi sin tinta: nada que alinear
        return 0.0
    alto, ancho = tinta.shape
    centro = (ancho / 2, alto / 2)

    def puntuacion(angulo: float) -> float:
        m = cv2.getRotationMatrix2D(centro, angulo, 1.0)
        girada = cv2.warpAffine(tinta, m, (ancho, alto), flags=cv2.INTER_NEAREST)
        return float(np.var(girada.sum(axis=1, dtype=np.float64)))

    gruesos = np.arange(-INCLINACION_MAX, INCLINACION_MAX + 0.01, 1.0)
    puntos = [puntuacion(a) for a in gruesos]
    mejor = float(gruesos[int(np.argmax(puntos))])
    finos = np.arange(mejor - 1.0, mejor + 1.01, 0.1)
    puntos_finos = [puntuacion(a) for a in finos]
    angulo = float(finos[int(np.argmax(puntos_finos))])
    base = puntuacion(0.0)
    # Solo si alinear mejora el perfil de forma clara (no por ruido) y no está en el límite
    # de la búsqueda (un ángulo de 15° suele ser un diagrama, no texto girado).
    if abs(angulo) < INCLINACION_MIN or abs(angulo) > INCLINACION_MAX - 0.5 or max(puntos_finos) < 1.15 * base:
        return 0.0
    return round(angulo, 1)


def enderezar(img: np.ndarray, angulo: float) -> np.ndarray:
    alto, ancho = img.shape[:2]
    m = cv2.getRotationMatrix2D((ancho / 2, alto / 2), angulo, 1.0)
    return cv2.warpAffine(img, m, (ancho, alto), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def preprocesar_para_ocr(imagen: np.ndarray, tipo_fuente: str, enderezar_texto: bool = False) -> Preprocesado:
    original = a_bgr(imagen)
    avisos = advertencias_calidad(original)
    vista, estado = corregir_perspectiva_hoja(original)
    inclinacion = 0.0
    if enderezar_texto and estado != "corregida":  # con la perspectiva corregida ya está alineado
        inclinacion = estimar_inclinacion(vista)
        if inclinacion:
            vista = enderezar(vista, inclinacion)
    vista = _escalar_para_ocr(vista)

    if tipo_fuente == "cuaderno":
        gris = vista[:, :, 2]  # rojo (BGR): el rayado azul y el margen rojo son claros aquí
        if iluminacion_desigual(gris):
            gris = normalizar_iluminacion(gris)
        gris = quitar_renglones(gris)
        psm = 4
    else:
        gris = cv2.cvtColor(vista, cv2.COLOR_BGR2GRAY)
        if gris.mean() < 110:          # pizarrón de tiza: texto claro sobre fondo oscuro
            gris = 255 - gris
        elif gris.mean() < UMBRAL_OSCURA:
            avisos.append("IMAGEN_OSCURA")
        if iluminacion_desigual(gris):
            gris = normalizar_iluminacion(gris)
        if ruido_estimado(gris) > UMBRAL_RUIDO:
            gris = cv2.medianBlur(gris, 3)
        psm = 3
    return Preprocesado(quitar_lineas_largas(gris), vista, psm, estado, avisos, inclinacion)
