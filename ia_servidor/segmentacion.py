"""Segmentación de una página en regiones de lectura (BACK-36).

Medido con una foto real (fullstack/docs/evaluacion-multimodal.md §5.1): enviar la página entera
al modelo hace que «corrija» lo escrito; enviar cada región por separado conserva la fidelidad.
Este módulo propone las regiones automáticamente:

- `regiones_opencv`: sin GPU. Tinta = píxeles más oscuros que el fondo local O con color
  saturado (el marcador amarillo es claro pero saturado). Se quitan el marco y las líneas largas,
  se unen los trazos con una dilatación proporcional a la altura de letra estimada en la propia
  foto y cada componente conexa es una región. Orden de lectura: por columnas, de izquierda a
  derecha y de arriba abajo.
- `regiones_vlm` (en servicio.py): el modelo propone las cajas («grounding»).

Las coordenadas siempre son píxeles de la imagen ORIGINAL: [x0, y0, x1, y1].
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

LADO_TRABAJO = 1000  # px del lado mayor con el que se segmenta (rápido y estable)


@dataclass
class Region:
    bbox: list[int]          # [x0, y0, x1, y1] en la imagen original
    origen: str = "opencv"   # opencv | vlm
    tipo: str | None = None  # sugerencia (vlm); None = desconocido


def mascara_tinta(imagen: np.ndarray) -> np.ndarray:
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    lado = max(gris.shape)
    k = max(31, (lado // 25) | 1)                       # ventana del fondo ≫ altura de letra
    fondo = cv2.medianBlur(gris, k)
    oscuro = cv2.subtract(fondo, gris)                  # cuánto más oscuro que su fondo
    _, oscura = cv2.threshold(oscuro, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    oscura[oscuro < 18] = 0                             # Otsu en una pizarra casi vacía da umbrales absurdos
    s = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)[:, :, 1]
    s_fondo = cv2.medianBlur(s, k)
    saturada = (cv2.subtract(s, s_fondo) > 45).astype(np.uint8) * 255
    tinta = cv2.bitwise_or(oscura, saturada)
    return cv2.morphologyEx(tinta, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))  # motas sueltas fuera


def quitar_lineas_y_marco(tinta: np.ndarray) -> np.ndarray:
    alto, ancho = tinta.shape
    horiz = cv2.morphologyEx(tinta, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, ancho // 4), 1)))
    vert = cv2.morphologyEx(tinta, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, alto // 4))))
    limpia = cv2.subtract(tinta, cv2.dilate(cv2.bitwise_or(horiz, vert), np.ones((5, 5), np.uint8)))
    # componentes pegadas al borde de la foto: marco, pared, mesa
    n, etiquetas, stats, _ = cv2.connectedComponentsWithStats(limpia, 8)
    margen = 3
    for i in range(1, n):
        x, y, w, h, _ = stats[i]
        if x <= margen or y <= margen or x + w >= ancho - margen or y + h >= alto - margen:
            if w > ancho * 0.25 or h > alto * 0.25:
                limpia[etiquetas == i] = 0
    return limpia


def altura_letra(tinta: np.ndarray) -> float:
    n, _, stats, _ = cv2.connectedComponentsWithStats(tinta, 8)
    alturas = [stats[i, 3] for i in range(1, n) if 4 <= stats[i, 3] <= tinta.shape[0] * 0.2 and stats[i, 4] >= 8]
    return float(np.median(alturas)) if alturas else 12.0


def _orden_lectura(cajas: list[list[int]]) -> list[list[int]]:
    """Columnas por solapamiento horizontal; dentro de cada una, de arriba abajo."""
    columnas: list[list[list[int]]] = []
    for c in sorted(cajas, key=lambda b: b[0]):
        for col in columnas:
            x0, x1 = min(b[0] for b in col), max(b[2] for b in col)
            solape = min(x1, c[2]) - max(x0, c[0])
            if solape > 0.5 * min(c[2] - c[0], x1 - x0):
                col.append(c)
                break
        else:
            columnas.append([c])
    columnas.sort(key=lambda col: min(b[0] for b in col))
    return [b for col in columnas for b in sorted(col, key=lambda b: b[1])]


def _fusionar(cajas: list[list[int]], minimo: float = 0.5) -> list[list[int]]:
    """Une dos cajas solo si la menor queda al menos `minimo` dentro de la mayor (p. ej. un
    exponente o una barra de fracción suelta). Unir con solo tocarse encadena todo el pizarrón."""
    def interseccion(a, b):
        return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))

    def area(a):
        return max(1, (a[2] - a[0]) * (a[3] - a[1]))

    cambiado = True
    while cambiado:
        cambiado = False
        for i in range(len(cajas)):
            for j in range(i + 1, len(cajas)):
                a, b = cajas[i], cajas[j]
                if interseccion(a, b) >= minimo * min(area(a), area(b)):
                    cajas[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    del cajas[j]
                    cambiado = True
                    break
            if cambiado:
                break
    return cajas


def _componentes(tinta: np.ndarray, h: float, union_h: float, union_v: float, desplazamiento=(0, 0)) -> list[list[int]]:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, int(h * union_h)), max(3, int(h * union_v))))
    n, _, stats, _ = cv2.connectedComponentsWithStats(cv2.dilate(tinta, kernel), 8)
    dx, dy = desplazamiento
    return [[int(x + dx), int(y + dy), int(x + w + dx), int(y + hh + dy)]
            for x, y, w, hh, area in (stats[i] for i in range(1, n)) if area >= h * h * 3]


def _sin_lineas_largas(tinta: np.ndarray, h: float) -> np.ndarray:
    """Quita trazos rectos mucho más largos que una fracción normal: marcos de recuadros, ejes de
    gráficas. Solo se aplica dentro de regiones demasiado grandes (fuera partiría las fracciones)."""
    horiz = cv2.morphologyEx(tinta, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(10, int(h * 9)), 1)))
    vert = cv2.morphologyEx(tinta, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(10, int(h * 5)))))
    return cv2.subtract(tinta, cv2.dilate(cv2.bitwise_or(horiz, vert), np.ones((3, 3), np.uint8)))


def _unir_lineas(cajas: list[list[int]], h: float, hueco: float = 0.6, solape: float = 0.5) -> list[list[int]]:
    """Líneas consecutivas del mismo párrafo: separadas verticalmente menos de `hueco` alturas de
    letra y que se solapan en horizontal más de `solape` del ancho de la más estrecha."""
    cambiado = True
    while cambiado:
        cambiado = False
        cajas.sort(key=lambda b: (b[1], b[0]))
        for i in range(len(cajas)):
            for j in range(i + 1, len(cajas)):
                a, b = cajas[i], cajas[j]
                distancia = max(a[1], b[1]) - min(a[3], b[3])           # <0 si se solapan
                x = min(a[2], b[2]) - max(a[0], b[0])
                if distancia < hueco * h and x > solape * min(a[2] - a[0], b[2] - b[0]):
                    cajas[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    del cajas[j]
                    cambiado = True
                    break
            if cambiado:
                break
    return cajas


def regiones_opencv(imagen: np.ndarray, union_h: float = 1.6, union_v: float = 1.1,
                    max_area: float = 0.06, hueco_lineas: float = 0.6) -> list[Region]:
    """`union_h`/`union_v`: cuánto se dilata (en alturas de letra) para unir letras en palabras,
    palabras en líneas y líneas en bloques. Un bloque = un párrafo, una fórmula o una tabla.
    Las regiones con más de `max_area` de la página se subdividen una vez sin líneas largas."""
    alto, ancho = imagen.shape[:2]
    escala = min(1.0, LADO_TRABAJO / max(alto, ancho))
    pequena = cv2.resize(imagen, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA) if escala < 1 else imagen
    tinta = quitar_lineas_y_marco(mascara_tinta(pequena))
    h = altura_letra(tinta)
    area_total = pequena.shape[0] * pequena.shape[1]

    def segmentar(mascara, uh, uv, desplazamiento, nivel):
        resultado = []
        for c in _componentes(mascara, h, uh, uv, desplazamiento):
            grande = (c[2] - c[0]) * (c[3] - c[1]) > area_total * max_area
            if grande and nivel < 3:  # subdividir: sin líneas largas y con menos unión
                x0, y0 = c[0] - desplazamiento[0], c[1] - desplazamiento[1]
                recorte = _sin_lineas_largas(mascara[y0:y0 + c[3] - c[1], x0:x0 + c[2] - c[0]], h)
                resultado += segmentar(recorte, uh * 0.75, uv * 0.8, (c[0], c[1]), nivel + 1)
            else:
                resultado.append(c)
        return resultado

    cajas = segmentar(tinta, union_h, union_v, (0, 0), 0)
    # tiras finas y alargadas = reflejos del marco o restos de líneas, no texto
    cajas = [c for c in cajas if not ((c[3] - c[1]) < 1.6 * h and (c[2] - c[0]) > 12 * (c[3] - c[1]))]
    # casi sin tinta (reflejos, bordes): menos del 3 % de la caja
    cajas = [c for c in cajas if tinta[c[1]:c[3], c[0]:c[2]].mean() / 255 >= 0.03]
    cajas = _fusionar(cajas)
    if hueco_lineas > 0:  # 0 = no unir líneas (regiones más pequeñas)
        cajas = _unir_lineas(cajas, h, hueco_lineas)
    margen = int(h * 0.4)
    regiones = []
    for x0, y0, x1, y1 in _orden_lectura(cajas):
        regiones.append(Region([max(0, int((x0 - margen) / escala)), max(0, int((y0 - margen) / escala)),
                                min(ancho, int((x1 + margen) / escala)), min(alto, int((y1 + margen) / escala))]))
    return regiones


def contencion(manual: list[int], auto: list[int]) -> float:
    """Fracción de la caja manual que cae dentro de la automática."""
    ix = max(0, min(manual[2], auto[2]) - max(manual[0], auto[0]))
    iy = max(0, min(manual[3], auto[3]) - max(manual[1], auto[1]))
    area = max(1, (manual[2] - manual[0]) * (manual[3] - manual[1]))
    return ix * iy / area


def evaluar_segmentacion(manuales: dict[str, list[int]], automaticas: list[list[int]]) -> dict:
    """Para cada región manual: ¿queda ENTERA (≥ 85 %) dentro de una sola región automática, y
    cuánto más grande es esa región (1 = igual; >3 = mezcló varias cosas)?"""
    detalle = {}
    for nombre, m in manuales.items():
        mejor = max(automaticas, key=lambda a: contencion(m, a), default=None)
        c = contencion(m, mejor) if mejor else 0.0
        area_m = (m[2] - m[0]) * (m[3] - m[1])
        tam = ((mejor[2] - mejor[0]) * (mejor[3] - mejor[1]) / area_m) if mejor else None
        detalle[nombre] = {"contencion": round(c, 2), "tamano_relativo": round(tam, 2) if tam else None,
                           "entera": c >= 0.85}
    enteras = sum(d["entera"] for d in detalle.values())
    return {"regiones_manuales": len(manuales), "automaticas": len(automaticas),
            "enteras": enteras, "detalle": detalle}
