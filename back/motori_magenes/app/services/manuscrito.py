"""Escritura a mano con alternativa segura (BACK-14).

Estrategia híbrida sobre Tesseract, sin transcribir «por imaginación»:

1. Segundo intento: cada bloque que no quedó «reconocido» se vuelve a leer
   sobre un recorte ampliado ×2 y binarizado (Otsu), con segmentación de bloque
   uniforme (psm 6). Se queda la lectura con mayor confianza.
2. Lo que sigue sin leerse bien NO se rellena: un bloque «no_reconocido» queda
   con texto vacío y se marca `recortar` para conservar su imagen, con su
   ubicación, y que el usuario lo transcriba. Los «inciertos» conservan el texto
   y también el recorte, para comparar.
3. Las zonas con tinta que el OCR ni siquiera detectó se conservan como
   bloques «manuscrito» (trazos de tamaño de texto) o «imagen» (dibujos,
   esquemas), siempre como recorte y sin texto.

Los bloques «reconocidos» no se tocan: el respaldo nunca empeora lo que ya se
leyó bien. Las fórmulas se clasifican después (BACK-15) y también conservan su
recorte.

Motores de manuscritos evaluados y no adoptados (PROCESAMIENTO.md): TrOCR
(modelos públicos en inglés, 1.3 GB + PyTorch) y PaddleOCR (~500 MB); se pueden
añadir como otro `MotorOCR` sin cambiar este flujo.
"""

import statistics

import cv2
import numpy as np

from app.services.ocr import BloqueOCR, MotorOCR, agrupar, estado_por_confianza, motor_ocr

MARGEN = 12
AREA_MIN = 0.0015          # fracción de la página para considerar una zona con tinta
SOLAPE_CUBIERTO = 0.3      # si una zona se solapa así con un bloque OCR, ya está cubierta


def _recorte(gris: np.ndarray, bbox: list[int]) -> np.ndarray:
    alto, ancho = gris.shape[:2]
    x0, y0, x1, y1 = bbox
    return gris[max(0, y0 - MARGEN):min(alto, y1 + MARGEN), max(0, x0 - MARGEN):min(ancho, x1 + MARGEN)]


def segundo_intento(gris: np.ndarray, bloque: BloqueOCR, idiomas: str, motor: MotorOCR) -> BloqueOCR:
    recorte = _recorte(gris, bloque.bbox)
    if recorte.size == 0:
        return bloque
    grande = cv2.resize(recorte, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, binaria = cv2.threshold(grande, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    nuevos = agrupar(motor.palabras(binaria, idiomas, 6))
    if not nuevos:
        return bloque
    total = sum(len(b.texto) for b in nuevos)
    conf = sum(b.confianza * len(b.texto) for b in nuevos) / total if total else 0.0
    minima = min((b.minima if b.minima is not None else b.confianza) for b in nuevos)
    actual = min(bloque.confianza, bloque.minima if bloque.minima is not None else bloque.confianza)
    if min(conf, minima) <= actual + 0.05:
        return bloque
    texto = "\n".join(b.texto for b in nuevos)
    dudosas = [d for b in nuevos for d in b.dudosas]
    return BloqueOCR(texto, round(conf, 3), bloque.bbox, texto.split("\n"), bloque.altura_linea,
                     bloque.tipo, dudosas, minima=round(minima, 3))


def _solape(a: list[int], b: list[int]) -> float:
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    return (x1 - x0) * (y1 - y0) / max(1, area_a)


def zonas_sin_texto(gris: np.ndarray, bloques: list[BloqueOCR]) -> list[BloqueOCR]:
    """Tinta que el OCR no cubrió: manuscritos ilegibles, dibujos y esquemas."""
    alto, ancho = gris.shape[:2]
    tinta = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15)
    tinta = cv2.morphologyEx(tinta, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))  # quita motas
    alturas = [b.altura_linea for b in bloques if b.altura_linea] or [max(12.0, alto / 40)]
    h_linea = statistics.median(alturas)
    unir = cv2.getStructuringElement(cv2.MORPH_RECT, (max(15, int(h_linea * 1.5)), max(5, int(h_linea * 0.6))))
    zonas = cv2.dilate(tinta, unir)
    n, _, stats, _ = cv2.connectedComponentsWithStats(zonas, connectivity=8)
    nuevas = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < AREA_MIN * alto * ancho or w > 0.97 * ancho or h > 0.97 * alto:
            continue  # ruido, o el borde de la hoja
        bbox = [int(x), int(y), int(x + w), int(y + h)]
        if any(_solape(bbox, b.bbox) > SOLAPE_CUBIERTO for b in bloques):
            continue
        densidad = tinta[y:y + h, x:x + w].mean() / 255
        tipo = "imagen" if h > 3 * h_linea and densidad < 0.12 else "manuscrito"
        nuevas.append(BloqueOCR("", 0.0, bbox, [], h_linea if tipo == "manuscrito" else 0.0, tipo, recortar=True))
    return nuevas


def leer_con_respaldo(gris: np.ndarray, bloques: list[BloqueOCR], idiomas: str,
                      motor: MotorOCR | None = None) -> list[BloqueOCR]:
    motor = motor or motor_ocr()
    resultado = []
    for b in bloques:
        if b.estado != "reconocido":
            b = segundo_intento(gris, b, idiomas, motor)
        if b.estado == "no_reconocido":
            # No se inventa texto: se conserva la imagen para transcribirla a mano.
            b = BloqueOCR("", b.confianza, b.bbox, [], b.altura_linea, "manuscrito", b.dudosas, recortar=True,
                          minima=b.minima)
        elif b.estado == "incierto":
            b.recortar = True
        resultado.append(b)
    resultado += zonas_sin_texto(gris, resultado)
    resultado.sort(key=lambda b: (b.bbox[1], b.bbox[0]))
    return resultado


def resumen_estados(bloques: list[BloqueOCR]) -> dict[str, int]:
    estados = [estado_por_confianza(b.confianza) if b.texto else "no_reconocido" for b in bloques]
    return {e: estados.count(e) for e in ("reconocido", "incierto", "no_reconocido")}
