"""Diagnóstico automático de la calidad de una foto antes del OCR (BACK-28).

Mide, sobre la foto original y sin modificarla:

  - resolución (lado menor, en px);
  - nitidez (varianza del laplaciano a 1000 px de lado);
  - brillo medio y contraste (diferencia entre papel y tinta);
  - iluminación desigual (BACK-12);
  - altura típica de la letra (mediana de los componentes de tinta, en px);
  - inclinación del texto (la estima `preprocesado_ocr.estimar_inclinacion`).

Con eso decide un nivel:
  - «buena»: sin avisos;
  - «aceptable»: con avisos concretos, se procesa;
  - «insuficiente»: tan deteriorada que no se puede garantizar ninguna lectura. Se procesa
    igual (algo puede rescatarse), pero NINGÚN bloque se da por «reconocido»: todo queda para
    revisar, y se pide repetir la foto (aviso REPETIR_FOTO).

Las métricas son números, nunca contenido de la foto: se pueden registrar en el log
sin exponer datos privados.
"""

from dataclasses import asdict, dataclass, field

import cv2
import numpy as np

UMBRAL_BORROSA = 40.0         # varianza del laplaciano a 1000 px (el mismo que BACK-12)
UMBRAL_MUY_BORROSA = 12.0
UMBRAL_RESOLUCION = 600       # lado menor
UMBRAL_RESOLUCION_MINIMA = 300
UMBRAL_OSCURA = 60            # brillo medio
UMBRAL_CONTRASTE = 90         # diferencia entre el papel y la tinta (medianas)
UMBRAL_TEXTO_PEQUENO = 11     # px de altura de letra en la foto original
INCLINACION_AVISO = 3.0       # grados


@dataclass
class Calidad:
    nivel: str                               # buena | aceptable | insuficiente
    avisos: list[str] = field(default_factory=list)
    metricas: dict = field(default_factory=dict)

    def a_dict(self) -> dict:
        return asdict(self)


def _gris(img: np.ndarray) -> np.ndarray:
    return img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def nitidez(gris: np.ndarray) -> float:
    escala = 1000 / max(gris.shape)
    pequena = cv2.resize(gris, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA) if escala < 1 else gris
    return float(cv2.Laplacian(pequena, cv2.CV_64F).var())


def contraste(gris: np.ndarray) -> float | None:
    """Diferencia entre la mediana del papel y la de la tinta (detectada con un umbral local).
    Con lápiz claro, tinta gastada o una foto lavada, las dos se acercan. None si no hay tinta.
    Espera texto oscuro sobre fondo claro (`diagnosticar` invierte los pizarrones de tiza)."""
    tinta = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 25, 12) > 0
    if tinta.mean() < 0.002:
        return None
    papel = float(np.median(gris[~tinta]))
    # El trazo más oscuro (percentil 10 de la tinta), no la mediana: los renglones y la
    # cuadrícula del cuaderno también son «tinta» y aclararían la medida.
    trazo = float(np.percentile(gris[tinta], 10))
    return abs(papel - trazo)


def altura_texto(gris: np.ndarray) -> float | None:
    """Mediana de la altura de los componentes de tinta con forma de letra, en px."""
    tinta = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 25, 12)
    n, _, stats, _ = cv2.connectedComponentsWithStats(tinta, connectivity=8)
    if n <= 1:
        return None
    w, h, area = stats[1:, cv2.CC_STAT_WIDTH], stats[1:, cv2.CC_STAT_HEIGHT], stats[1:, cv2.CC_STAT_AREA]
    # letras: ni motas ni ruido del sensor (área < 30 px) ni rayas largas (renglones, cuadrícula, bordes)
    letras = (area >= 30) & (h >= 7) & (w <= 6 * h) & (h <= 0.2 * gris.shape[0])
    if letras.sum() < 15:
        return None
    return float(np.median(h[letras]))


def diagnosticar(imagen: np.ndarray, inclinacion: float = 0.0, vista: np.ndarray | None = None) -> Calidad:
    """`imagen`: la foto original (resolución, nitidez y tamaño de letra se miden en ella).
    `vista`: la hoja o el pizarrón ya enderezado y recortado; brillo, contraste e iluminación se
    miden ahí para no contar la pared o la mesa de alrededor."""
    from app.services.preprocesado_ocr import iluminacion_desigual
    gris = _gris(imagen)
    zona = _gris(vista) if vista is not None else gris
    if zona.mean() < 110:   # pizarrón de tiza: se mide como texto oscuro sobre fondo claro
        zona = 255 - zona
    m = {
        "lado_menor": int(min(gris.shape[:2])),
        "nitidez": round(nitidez(gris), 1),
        "brillo": round(float(zona.mean()), 1),
        "contraste": None,
        "altura_texto": None,
        "inclinacion": round(float(inclinacion), 1),
        "iluminacion_desigual": bool(iluminacion_desigual(zona)),
    }
    c = contraste(zona)
    if c is not None:
        m["contraste"] = round(c, 1)
    altura = altura_texto(gris)
    if altura is not None:
        m["altura_texto"] = round(altura, 1)

    avisos = []
    if m["lado_menor"] < UMBRAL_RESOLUCION:
        avisos.append("BAJA_RESOLUCION")
    if m["nitidez"] < UMBRAL_BORROSA:
        avisos.append("IMAGEN_BORROSA")
    if m["brillo"] < UMBRAL_OSCURA:
        avisos.append("IMAGEN_OSCURA")
    if m["contraste"] is not None and m["contraste"] < UMBRAL_CONTRASTE:
        avisos.append("BAJO_CONTRASTE")
    if m["iluminacion_desigual"]:
        avisos.append("ILUMINACION_DESIGUAL")
    if altura is not None and altura < UMBRAL_TEXTO_PEQUENO:
        avisos.append("TEXTO_PEQUENO")
    if abs(inclinacion) >= INCLINACION_AVISO:
        avisos.append("IMAGEN_GIRADA")

    insuficiente = (m["nitidez"] < UMBRAL_MUY_BORROSA
                    or m["lado_menor"] < UMBRAL_RESOLUCION_MINIMA
                    or (m["nitidez"] < UMBRAL_BORROSA and m["lado_menor"] < UMBRAL_RESOLUCION))
    if insuficiente:
        avisos.append("REPETIR_FOTO")
        nivel = "insuficiente"
    else:
        # La sombra y la inclinación se corrigen solas: informan, pero no bajan el nivel.
        graves = [a for a in avisos if a not in ("ILUMINACION_DESIGUAL", "IMAGEN_GIRADA")]
        nivel = "aceptable" if graves else "buena"
    return Calidad(nivel, avisos, m)


MENSAJES = {
    "BAJA_RESOLUCION": "La foto tiene poca resolución: acércate o usa la cámara principal.",
    "IMAGEN_BORROSA": "La foto está desenfocada: sostén el teléfono firme y toca la pantalla para enfocar.",
    "IMAGEN_OSCURA": "La foto está oscura: busca más luz o enciende la del aula.",
    "BAJO_CONTRASTE": "La tinta se distingue poco del fondo (lápiz claro o reflejo).",
    "ILUMINACION_DESIGUAL": "Hay sombras o reflejos; se corrigieron, pero revisa las zonas oscuras.",
    "TEXTO_PEQUENO": "La letra se ve muy pequeña en la foto: acércate a la hoja o al pizarrón.",
    "IMAGEN_GIRADA": "La foto estaba girada; se enderezó automáticamente.",
    "REPETIR_FOTO": "La foto no tiene calidad suficiente para una transcripción confiable: vuelve a tomarla.",
}
