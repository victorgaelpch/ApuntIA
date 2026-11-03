"""Corrección de perspectiva del pizarrón (BACK-04).

Estrategia:
  1. Trabajar sobre una copia reducida (lado mayor <= 800 px) para que la
     detección sea rápida; las esquinas se reescalan a la imagen original.
  2. Buscar candidatos a cuadrilátero con dos métodos complementarios:
     a) bordes de Canny dilatados (pizarrón con marco o borde marcado);
     b) umbral de Otsu sobre la luminancia (pizarrón claro sobre pared oscura).
  3. Aceptar solo un cuadrilátero fiable: 4 vértices, convexo, entre el 10 %
     y el 98 % del área de la imagen, con ángulos interiores de 45° a 135° y
     una proporción de lados razonable. Además, como mucho una esquina puede
     estar pegada al borde de la foto: si hay más, lo detectado suele ser el
     recorte del encuadre (pizarrón que se sale de la foto) o la pared.
  4. Ordenar las esquinas (sup-izq, sup-der, inf-der, inf-izq) y aplicar
     warpPerspective. El tamaño de salida se calcula con la longitud media
     de los lados opuestos, para conservar proporciones legibles.

Si no hay un cuadrilátero fiable se devuelve la imagen sin cambios y el
estado "no_detectada": nunca se bloquea el servicio.
"""

from dataclasses import dataclass

import cv2
import numpy as np

LADO_DETECCION = 800
AREA_MIN = 0.10
AREA_MAX = 0.98
ANGULO_MIN, ANGULO_MAX = 45.0, 135.0
PROPORCION_MAX = 6.0
MARGEN_BORDE = 0.02  # fracción del lado: esquinas más cerca del borde se consideran "en el borde"


@dataclass
class Deteccion:
    esquinas: np.ndarray | None  # (4, 2) float32 en coordenadas de la imagen original
    metodo: str | None = None


def ordenar_esquinas(puntos: np.ndarray) -> np.ndarray:
    """Ordena 4 puntos como sup-izq, sup-der, inf-der, inf-izq."""
    p = np.asarray(puntos, dtype=np.float32).reshape(4, 2)
    suma = p.sum(axis=1)
    resta = np.diff(p, axis=1).ravel()  # y - x
    return np.float32([p[np.argmin(suma)], p[np.argmin(resta)],
                       p[np.argmax(suma)], p[np.argmax(resta)]])


def _angulos(esquinas: np.ndarray) -> list[float]:
    angulos = []
    for i in range(4):
        a, b, c = esquinas[i - 1], esquinas[i], esquinas[(i + 1) % 4]
        v1, v2 = a - b, c - b
        cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
        angulos.append(float(np.degrees(np.arccos(np.clip(cos, -1, 1)))))
    return angulos


def _esquinas_en_borde(esquinas: np.ndarray, forma: tuple[int, int]) -> int:
    alto, ancho = forma
    mx, my = MARGEN_BORDE * ancho, MARGEN_BORDE * alto
    x, y = esquinas[:, 0], esquinas[:, 1]
    return int(np.sum((x <= mx) | (x >= ancho - 1 - mx) | (y <= my) | (y >= alto - 1 - my)))


def _es_fiable(esquinas: np.ndarray, forma: tuple[int, int]) -> bool:
    area_imagen = float(forma[0] * forma[1])
    if len(np.unique(esquinas.round(), axis=0)) < 4:
        return False
    if _esquinas_en_borde(esquinas, forma) > 1:
        return False
    area = cv2.contourArea(esquinas)
    if not (AREA_MIN * area_imagen <= area <= AREA_MAX * area_imagen):
        return False
    if not cv2.isContourConvex(esquinas.reshape(-1, 1, 2)):
        return False
    if not all(ANGULO_MIN <= a <= ANGULO_MAX for a in _angulos(esquinas)):
        return False
    ancho, alto = _tamano_salida(esquinas)
    return min(ancho, alto) > 0 and max(ancho, alto) / min(ancho, alto) <= PROPORCION_MAX


def _cuadrilateros(mascara: np.ndarray):
    contornos, _ = cv2.findContours(mascara, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for contorno in sorted(contornos, key=cv2.contourArea, reverse=True)[:8]:
        perimetro = cv2.arcLength(contorno, True)
        for epsilon in (0.02, 0.035, 0.05):
            aprox = cv2.approxPolyDP(contorno, epsilon * perimetro, True)
            if len(aprox) == 4:
                yield ordenar_esquinas(aprox)
                break


def detectar_pizarron(imagen: np.ndarray) -> Deteccion:
    alto, ancho = imagen.shape[:2]
    escala = min(1.0, LADO_DETECCION / max(alto, ancho))
    reducida = cv2.resize(imagen, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA) if escala < 1 else imagen
    gris = cv2.cvtColor(reducida, cv2.COLOR_BGR2GRAY) if reducida.ndim == 3 else reducida
    gris = cv2.GaussianBlur(gris, (5, 5), 0)
    nucleo = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    bordes = cv2.dilate(cv2.Canny(gris, 50, 150), nucleo, iterations=2)
    _, claro = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    claro = cv2.morphologyEx(claro, cv2.MORPH_CLOSE, nucleo, iterations=3)

    for metodo, mascara in (("bordes", bordes), ("umbral", claro)):
        for esquinas in _cuadrilateros(mascara):
            if _es_fiable(esquinas, gris.shape[:2]):
                return Deteccion(esquinas / escala, metodo)
    return Deteccion(None)


def _tamano_salida(esquinas: np.ndarray) -> tuple[int, int]:
    si, sd, idr, ii = esquinas
    ancho = (np.linalg.norm(sd - si) + np.linalg.norm(idr - ii)) / 2
    alto = (np.linalg.norm(ii - si) + np.linalg.norm(idr - sd)) / 2
    return int(round(ancho)), int(round(alto))


def rectificar(imagen: np.ndarray, esquinas: np.ndarray) -> np.ndarray:
    ancho, alto = _tamano_salida(esquinas)
    destino = np.float32([[0, 0], [ancho - 1, 0], [ancho - 1, alto - 1], [0, alto - 1]])
    matriz = cv2.getPerspectiveTransform(esquinas.astype(np.float32), destino)
    return cv2.warpPerspective(imagen, matriz, (ancho, alto), flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_REPLICATE)


def corregir_perspectiva(imagen: np.ndarray) -> tuple[np.ndarray, str]:
    """Devuelve (imagen, estado) con estado "corregida" o "no_detectada"."""
    deteccion = detectar_pizarron(imagen)
    if deteccion.esquinas is None:
        return imagen, "no_detectada"
    return rectificar(imagen, deteccion.esquinas), "corregida"
