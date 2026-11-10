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
from app.services.perspectiva import corregir_perspectiva
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


def preprocesar_para_ocr(imagen: np.ndarray, tipo_fuente: str) -> Preprocesado:
    original = a_bgr(imagen)
    avisos = advertencias_calidad(original)
    vista, estado = corregir_perspectiva(original)
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
    return Preprocesado(gris, vista, psm, estado, avisos)
