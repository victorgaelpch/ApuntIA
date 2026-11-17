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


PAPEL_CON_LINEAS = 0.15  # fracción de la foto cubierta por líneas largas a partir de la que se atenúan


def lineas_en_gris(mapa: np.ndarray, tolerancia: int = 9) -> np.ndarray:
    """Intensidad de las líneas largas y casi rectas de un mapa de «cuánta tinta» (0-255).

    Hallazgo real (cuaderno de electrónica, 15/11/2026): en una foto de móvil la cuadrícula está
    algo ondulada e inclinada y, al umbralizar, se rompe en trocitos que ya no parecen líneas; la
    dilatación los une con el texto y TODO el apunte acaba en una sola región. En grises la línea
    sigue siendo continua: se ensancha `tolerancia` px en perpendicular (el máximo local tolera la
    ondulación) y una apertura larga deja solo lo que se mantiene a lo largo de la línea."""
    alto, ancho = mapa.shape
    banda_h = cv2.dilate(mapa, np.ones((tolerancia, 1), np.uint8))
    banda_v = cv2.dilate(mapa, np.ones((1, tolerancia), np.uint8))
    # Mismo largo mínimo que quitar_lineas_y_marco: un cable de circuito o una barra de fracción
    # son más cortos que un cuarto de la página y no se tocan.
    horiz = cv2.morphologyEx(banda_h, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, ancho // 4), 1)))
    vert = cv2.morphologyEx(banda_v, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, alto // 4))))
    return cv2.max(horiz, vert)


def mascara_tinta(imagen: np.ndarray, info: dict | None = None) -> np.ndarray:
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    lado = max(gris.shape)
    k = max(31, (lado // 25) | 1)                       # ventana del fondo ≫ altura de letra
    fondo = cv2.medianBlur(gris, k)
    oscuro = cv2.subtract(fondo, gris)                  # cuánto más oscuro que su fondo
    s = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)[:, :, 1]
    s_dif = cv2.subtract(s, cv2.medianBlur(s, k))
    # Papel cuadriculado o de renglones: las líneas cubren la mayor parte de la foto (medido: 60-83 %
    # en páginas de cuaderno sintéticas; 1,9 % en el pizarrón real). Solo entonces se restan, de la
    # oscuridad y de la saturación (la cuadrícula azul también es «color»): un trazo de bolígrafo
    # que las cruza es más intenso que ellas y sobrevive. En un pizarrón no se toca nada.
    lineas = lineas_en_gris(oscuro)
    papel = bool((lineas > 12).mean() > PAPEL_CON_LINEAS)
    if info is not None:
        info["papel_con_lineas"] = papel
    if papel:
        oscuro = cv2.subtract(oscuro, lineas)
        s_dif = cv2.subtract(s_dif, lineas_en_gris(s_dif))
    _, oscura = cv2.threshold(oscuro, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    oscura[oscuro < 18] = 0                             # Otsu en una pizarra casi vacía da umbrales absurdos
    saturada = (s_dif > 45).astype(np.uint8) * 255
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


def _es_raya(recorte: np.ndarray, h: float) -> bool:
    """Una raya horizontal (o casi): tinta solo en una franja de menos de media altura de letra y
    al menos 3 veces más ancha que alta. Una letra suelta, un signo «−» dentro de una fórmula o
    una palabra tienen tinta en más filas o no son tan alargados."""
    filas = np.flatnonzero(recorte.any(axis=1))
    cols = np.flatnonzero(recorte.any(axis=0))
    if not len(filas):
        return True
    alto_tinta, ancho_tinta = filas[-1] - filas[0] + 1, cols[-1] - cols[0] + 1
    return alto_tinta < 0.5 * h and ancho_tinta > 3 * alto_tinta


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


BANDA_BORDE = 0.07       # fracción del ancho (o alto) junto a cada borde donde viven espiral y perforaciones
ALTO_RENGLON = 3.5       # alturas de letra: lo más alto que mide un renglón (fracciones incluidas)
ALTO_MINIMO_LETRA = 0.015  # fracción del alto de la foto (solo para unir renglones)
MINIMO_BORDE = 4         # cajas en la misma banda a partir de las que es una fila de aros, no apuntes


def separar_bordes(cajas: list[list[int]], ancho: int, alto: int) -> tuple[list[list[int]], list[list[int]]]:
    """(cajas que se quedan, cajas del borde de la hoja).

    Hallazgo real (cuaderno de electrónica, 16/11/2026): los aros del espiral salían como 19 de las
    23 regiones; el modelo los describía como «un trombón» o «un martillo» y gastaban la mayor parte
    del tiempo de GPU. Un aro o una perforación cabe ENTERO en la franja del borde y aparecen en
    fila; lo escrito por el alumno casi nunca: una nota al margen suelta (1-3 cajas) se queda.
    También se aparta una tira larga y fina pegada a un lado (el borde perforado de la hoja)."""
    bandas = {
        "izquierda": lambda c: c[2] <= BANDA_BORDE * ancho,
        "derecha": lambda c: c[0] >= (1 - BANDA_BORDE) * ancho,
        "arriba": lambda c: c[3] <= BANDA_BORDE * alto,
        "abajo": lambda c: c[1] >= (1 - BANDA_BORDE) * alto,
    }
    fuera: set[int] = set()
    for dentro in bandas.values():
        indices = [i for i, c in enumerate(cajas) if dentro(c)]
        if len(indices) >= MINIMO_BORDE:
            fuera.update(indices)
    for i, (x0, y0, x1, y1) in enumerate(cajas):
        w, h = x1 - x0, y1 - y0
        pegada_lado = x0 <= 0.01 * ancho or x1 >= 0.99 * ancho
        pegada_tope = y0 <= 0.01 * alto or y1 >= 0.99 * alto
        if (pegada_lado and w <= 0.04 * ancho and h >= 0.25 * alto) or (pegada_tope and h <= 0.04 * alto and w >= 0.25 * ancho):
            fuera.add(i)
    return [c for i, c in enumerate(cajas) if i not in fuera], [c for i, c in enumerate(cajas) if i in fuera]


def _unir_renglon(cajas: list[list[int]], h: float, hueco: float, mitades_de_parrafo: bool = False) -> list[list[int]]:
    """Trozos del MISMO renglón (se solapan en vertical al menos la mitad de la altura del menor)
    separados menos de `hueco` alturas de letra. Hallazgo real: en el cuaderno, con la cuadrícula
    restada, una fórmula como «v = dx/dt î + dy/dt ĵ» salía en 6 regiones sueltas y el modelo leía
    cada pedazo sin contexto. Así cada renglón de fórmula llega entero."""
    cambiado = True
    while cambiado:
        cambiado = False
        cajas.sort(key=lambda b: (b[0], b[1]))
        for i in range(len(cajas)):
            for j in range(i + 1, len(cajas)):
                a, b = cajas[i], cajas[j]
                solape_v = min(a[3], b[3]) - max(a[1], b[1])
                hueco_h = max(a[0], b[0]) - min(a[2], b[2])
                # Solo trozos de UN renglón (una fracción mide ~2,5 letras): un párrafo o una gráfica no
                # participan, y la unión no debe crecer en vertical. Sin esto se encadena la página
                # (medido en el pizarrón real: 14 regiones → 1).
                alto_union = max(a[3], b[3]) - min(a[1], b[1])
                alto_min, alto_max = min(a[3] - a[1], b[3] - b[1]), max(a[3] - a[1], b[3] - b[1])
                renglon = solape_v >= 0.5 * alto_min and alto_union <= ALTO_RENGLON * h and alto_union <= 1.25 * alto_max
                # Un párrafo que la subdivisión partió en dos mitades de la MISMA altura (hallazgo real:
                # «Suponga que una partícula…» salía en tres trozos ilegibles). Casi el mismo alto y casi
                # el mismo arranque y final: no encadena columnas de alturas distintas.
                # Solo en papel con renglones o cuadrícula: en el pizarrón real unía columnas (14 → 10 regiones).
                mitades = (mitades_de_parrafo and solape_v >= 0.8 * alto_min and alto_union <= 1.1 * alto_max
                           and alto_min >= 0.6 * alto_max)
                if (renglon or mitades) and hueco_h < hueco * h:
                    cajas[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    del cajas[j]
                    cambiado = True
                    break
            if cambiado:
                break
    return cajas


def regiones_opencv(imagen: np.ndarray, union_h: float = 1.6, union_v: float = 1.1,
                    max_area: float = 0.06, hueco_lineas: float = 0.6, hueco_renglon: float = 0.0) -> list[Region]:
    """Solo las regiones (compatibilidad); `segmentar_pagina` devuelve además los bordes apartados."""
    return segmentar_pagina(imagen, union_h, union_v, max_area, hueco_lineas, hueco_renglon)[0]


def segmentar_pagina(imagen: np.ndarray, union_h: float = 1.6, union_v: float = 1.1, max_area: float = 0.06,
                     hueco_lineas: float = 0.6, hueco_renglon: float = 0.0) -> tuple[list[Region], list[dict]]:
    """`union_h`/`union_v`: cuánto se dilata (en alturas de letra) para unir letras en palabras,
    palabras en líneas y líneas en bloques. Un bloque = un párrafo, una fórmula o una tabla.
    Las regiones con más de `max_area` de la página se subdividen una vez sin líneas largas.
    `hueco_renglon` > 0 une los trozos de un mismo renglón separados menos de esas alturas de letra.
    Devuelve (regiones, descartes); los descartes son el espiral y el borde perforado de la hoja,
    con su caja y su motivo, para que la app avise en lugar de borrarlos en silencio."""
    alto, ancho = imagen.shape[:2]
    escala = min(1.0, LADO_TRABAJO / max(alto, ancho))
    pequena = cv2.resize(imagen, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA) if escala < 1 else imagen
    info: dict = {}
    tinta = quitar_lineas_y_marco(mascara_tinta(pequena, info))
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
    # rayas: separadores punteados, subrayados sueltos, restos de renglón. Toda su tinta cabe en una
    # franja más baja que media letra; el modelo las daba como «fragmento no transcrito» (hallazgo real).
    cajas = [c for c in cajas if not _es_raya(tinta[c[1]:c[3], c[0]:c[2]], h)]
    # antes de unir nada: un aro pegado a un renglón lo arrastraría consigo
    cajas, bordes = separar_bordes(cajas, pequena.shape[1], pequena.shape[0])
    cajas = _fusionar(cajas)
    if hueco_lineas > 0:  # 0 = no unir líneas (regiones más pequeñas)
        cajas = _unir_lineas(cajas, h, hueco_lineas)
    if hueco_renglon > 0:  # después: con los renglones ya anchos, unir líneas encadenaría la página
        # En el cuaderno, con la cuadrícula restada, la letra sale en trocitos y `h` se queda corta
        # (medido: 8 px frente a ~25 px reales): para los renglones se usa al menos 1,5 % del alto.
        cajas = _unir_renglon(cajas, max(h, ALTO_MINIMO_LETRA * pequena.shape[0]), hueco_renglon,
                              mitades_de_parrafo=info.get("papel_con_lineas", False))
    margen = int(h * 0.4)

    def original(c):
        x0, y0, x1, y1 = c
        return [max(0, int((x0 - margen) / escala)), max(0, int((y0 - margen) / escala)),
                min(ancho, int((x1 + margen) / escala)), min(alto, int((y1 + margen) / escala))]

    regiones = [Region(original(c)) for c in _orden_lectura(cajas)]
    descartes = [{"bbox": original(c), "motivo": "espiral o borde perforado de la hoja", "texto": ""} for c in bordes]
    return regiones, descartes


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
