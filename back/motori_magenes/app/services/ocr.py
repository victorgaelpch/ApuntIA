"""OCR de texto en fotos de pizarrón y cuaderno, por bloques (BACK-13, BACK-14).

Motor: Tesseract 5 (Apache-2.0) a través de pytesseract. Se eligió frente a
PaddleOCR, EasyOCR y TrOCR por: buen soporte de español (tildes, ñ), licencia
libre, sin GPU ni descargas de cientos de MB, y disponible en Windows, Linux y
Docker. La comparación está en PROCESAMIENTO.md. El motor no está «cableado»:
`motor_ocr()` lo elige con OCR_MOTOR y cualquier otro motor que implemente
`MotorOCR` puede sustituirlo.

La salida distingue tres situaciones distintas (criterio de BACK-13):
  - fallo técnico  → ErrorOCR (p. ej. OCR_NO_DISPONIBLE): nunca un texto vacío;
  - resultado vacío → lista de bloques vacía (la imagen no tiene texto legible);
  - confianza baja  → bloques con estado «incierto» o «no_reconocido».
"""

import logging
import os
import shutil
import statistics
import unicodedata
from dataclasses import dataclass, field

import numpy as np

from app.core.config import settings

logger = logging.getLogger("apuntia.ocr")

UMBRAL_RECONOCIDO = 0.80
UMBRAL_INCIERTO = 0.50


class ErrorOCR(Exception):
    def __init__(self, codigo: str, mensaje: str):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


@dataclass
class Palabra:
    texto: str
    confianza: float          # 0..1
    bbox: tuple[int, int, int, int]
    bloque: int
    parrafo: int
    linea: int


@dataclass
class BloqueOCR:
    texto: str
    confianza: float
    bbox: list[int]
    lineas: list[str] = field(default_factory=list)
    altura_linea: float = 0.0
    tipo: str = "texto"       # titulo | texto | manuscrito | formula | imagen
    dudosas: list[str] = field(default_factory=list)   # palabras con confianza < 0.80
    recortar: bool = False    # conservar el recorte de la imagen para revisión manual
    minima: float | None = None  # confianza de la palabra más dudosa

    @property
    def estado(self) -> str:
        # «no_reconocido» (el texto se descarta) exige que la MEDIA sea baja: una sola
        # palabra dudosa no puede borrar un párrafo bueno, solo volverlo «incierto».
        estado = estado_por_confianza(self.confianza)
        if estado == "reconocido" and self.minima is not None and self.minima < UMBRAL_RECONOCIDO:
            return "incierto"
        return estado


def estado_por_confianza(confianza: float) -> str:
    if confianza >= UMBRAL_RECONOCIDO:
        return "reconocido"
    if confianza >= UMBRAL_INCIERTO:
        return "incierto"
    return "no_reconocido"


class MotorOCR:
    nombre = "base"

    def disponible(self) -> bool:
        raise NotImplementedError

    def info(self) -> dict:
        raise NotImplementedError

    def palabras(self, imagen: np.ndarray, idiomas: str, psm: int) -> list[Palabra]:
        raise NotImplementedError


class MotorTesseract(MotorOCR):
    nombre = "tesseract"

    def __init__(self, ejecutable: str | None = None):
        import pytesseract
        # Tesseract usa OpenMP con todos los núcleos. Con varios análisis a la vez (hasta
        # TRABAJOS_SIMULTANEOS), sus hilos compiten y el conjunto se vuelve ~100 veces más lento
        # (medido en FULL-22: dos apuntes de 3 fotos, 209 s frente a 2 s). Un hilo por proceso es
        # lo que recomienda la documentación de Tesseract para instancias en paralelo; se puede
        # cambiar definiendo OMP_THREAD_LIMIT antes de arrancar.
        os.environ.setdefault("OMP_THREAD_LIMIT", "1")
        self.pt = pytesseract
        if ejecutable:
            pytesseract.pytesseract.tesseract_cmd = ejecutable

    def disponible(self) -> bool:
        try:
            self.pt.get_tesseract_version()
            return True
        except (self.pt.TesseractNotFoundError, OSError):
            return False

    def info(self) -> dict:
        if not self.disponible():
            return {"disponible": False, "motor": self.nombre, "idiomas": []}
        try:
            idiomas = sorted(set(self.pt.get_languages(config="")) - {"osd"})
        except Exception:  # noqa: BLE001
            idiomas = []
        return {"disponible": True, "motor": self.nombre, "version": str(self.pt.get_tesseract_version()),
                "idiomas": idiomas}

    def palabras(self, imagen: np.ndarray, idiomas: str, psm: int) -> list[Palabra]:
        try:
            datos = self.pt.image_to_data(imagen, lang=idiomas, config=f"--oem 1 --psm {psm}",
                                          output_type=self.pt.Output.DICT, timeout=120)
        except self.pt.TesseractNotFoundError:
            raise ErrorOCR("OCR_NO_DISPONIBLE",
                           "El reconocimiento de texto no está instalado en el servidor (Tesseract).") from None
        except RuntimeError as exc:  # tiempo agotado
            raise ErrorOCR("OCR_TIEMPO_AGOTADO", "El reconocimiento de texto tardó demasiado en esta página.") from exc
        except self.pt.TesseractError as exc:
            if "Failed loading language" in str(exc):
                raise ErrorOCR("OCR_IDIOMA_NO_DISPONIBLE",
                               f"Falta el idioma «{idiomas}» de Tesseract en el servidor.") from None
            raise ErrorOCR("OCR_FALLO", "El reconocimiento de texto falló en esta página.") from exc
        palabras = []
        for i, texto in enumerate(datos["text"]):
            texto = unicodedata.normalize("NFC", (texto or "").strip())
            conf = float(datos["conf"][i])
            if not texto or conf < 0:
                continue
            x, y, w, h = datos["left"][i], datos["top"][i], datos["width"][i], datos["height"][i]
            palabras.append(Palabra(texto, conf / 100, (x, y, x + w, y + h),
                                    datos["block_num"][i], datos["par_num"][i], datos["line_num"][i]))
        return palabras


class MotorNinguno(MotorOCR):
    """OCR desactivado (OCR_MOTOR=ninguno): el análisis falla con un código claro."""
    nombre = "ninguno"

    def disponible(self) -> bool:
        return False

    def info(self) -> dict:
        return {"disponible": False, "motor": self.nombre, "idiomas": []}

    def palabras(self, imagen, idiomas, psm):
        raise ErrorOCR("OCR_NO_DISPONIBLE", "El reconocimiento de texto está desactivado en este servidor.")


_motor: MotorOCR | None = None


def motor_ocr() -> MotorOCR:
    global _motor
    if _motor is None:
        if settings.ocr_motor == "tesseract":
            _motor = MotorTesseract(settings.tesseract_cmd or shutil.which("tesseract"))
        else:
            _motor = MotorNinguno()
    return _motor


def agrupar(palabras: list[Palabra]) -> list[BloqueOCR]:
    """Palabras → líneas → bloques (párrafos de Tesseract), en orden de lectura."""
    grupos: dict[tuple[int, int], list[Palabra]] = {}
    for p in palabras:
        grupos.setdefault((p.bloque, p.parrafo), []).append(p)
    bloques = []
    for _, ps in sorted(grupos.items(), key=lambda kv: (min(p.bbox[1] for p in kv[1]), min(p.bbox[0] for p in kv[1]))):
        lineas: dict[int, list[Palabra]] = {}
        for p in ps:
            lineas.setdefault(p.linea, []).append(p)
        textos, alturas = [], []
        for _, lps in sorted(lineas.items(), key=lambda kv: min(p.bbox[1] for p in kv[1])):
            lps.sort(key=lambda p: p.bbox[0])
            textos.append(" ".join(p.texto for p in lps))
            alturas.append(statistics.median(p.bbox[3] - p.bbox[1] for p in lps))
        # Confianza del bloque: media ponderada por longitud. Además se guarda la
        # de su palabra más dudosa: se midió (BACK-14) que en escritura irregular
        # Tesseract da medias altas (0.85) a bloques con palabras mal leídas (0.70),
        # así que una palabra dudosa basta para que el bloque sea «incierto».
        total = sum(len(p.texto) for p in ps)
        media = sum(p.confianza * len(p.texto) for p in ps) / total if total else 0.0
        significativas = [p.confianza for p in ps if sum(c.isalnum() for c in p.texto) >= 2] or [media]
        conf = media
        dudosas = [p.texto for p in ps if p.confianza < UMBRAL_RECONOCIDO]
        bbox = [min(p.bbox[0] for p in ps), min(p.bbox[1] for p in ps),
                max(p.bbox[2] for p in ps), max(p.bbox[3] for p in ps)]
        bloques.append(BloqueOCR("\n".join(textos), round(conf, 3), bbox, textos, statistics.median(alturas),
                                 dudosas=dudosas, minima=round(min(significativas), 3)))
    marcar_titulos(bloques)
    return bloques


def marcar_titulos(bloques: list[BloqueOCR]) -> None:
    """Un bloque de una línea corta y letra claramente mayor que la mediana es un título."""
    if len(bloques) < 2:
        return
    mediana = statistics.median(b.altura_linea for b in bloques)
    for b in bloques:
        if len(b.lineas) == 1 and len(b.texto) <= 80 and b.altura_linea >= 1.25 * mediana:
            b.tipo = "titulo"


def reconocer(imagen: np.ndarray, idiomas: str | None = None, psm: int = 3,
              motor: MotorOCR | None = None) -> list[BloqueOCR]:
    """OCR de una página ya preprocesada. Lista vacía = no hay texto legible."""
    motor = motor or motor_ocr()
    return agrupar(motor.palabras(imagen, idiomas or settings.ocr_idiomas, psm))
