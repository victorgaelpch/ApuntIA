"""Interfaz común de los motores de reconocimiento (FULL-30, fase 2).

Cada motor —Tesseract hoy; un VLM local por Ollama, y en PR posteriores OCR documental,
HTR u OCR matemático— se usa a través de la misma interfaz, con entradas y salidas
tipadas y estables:

    disponible()  -> bool           ¿se puede usar ahora? (rápido, sin cargar modelos)
    capacidades() -> set[str]       qué sabe hacer (ver CAPACIDADES)
    info_modelo() -> InfoMotor      nombre, modelo, versión, licencia, local o no
    reconocer(imagen, opciones) -> ResultadoMotor

Reglas de todos los adaptadores:
  - nunca modifican la imagen recibida;
  - un fallo (no instalado, tiempo agotado, memoria, respuesta inválida) es un
    `ErrorMotor` con código, nunca un texto vacío presentado como resultado;
  - lo que devuelven es una PROPUESTA con su procedencia: el que decide qué se
    muestra como reconocido es el flujo de validación, no el motor.
"""

from dataclasses import dataclass, field

import numpy as np

# Qué puede hacer un motor. Un VLM puede declarar varias, pero sus salidas siempre
# quedan para revisar (ver ollama.py): no hay confianza calibrada.
CAPACIDADES = {
    "texto_impreso",       # OCR de texto impreso
    "texto_manuscrito",    # HTR
    "formula",             # imagen → LaTeX
    "diagrama",            # descripción de diagramas, gráficas o circuitos
    "tabla",               # estructura de tablas
    "layout",              # regiones y orden de lectura
}


class ErrorMotor(Exception):
    """Fallo controlado de un motor. `codigo`: NO_DISPONIBLE, TIEMPO_AGOTADO, SIN_MEMORIA,
    RESPUESTA_INVALIDA, NO_PERMITIDO u OCUPADO."""

    def __init__(self, codigo: str, mensaje: str):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


@dataclass
class InfoMotor:
    nombre: str                      # identificador estable del adaptador: "tesseract", "ollama_vlm"
    modelo: str = ""                 # p. ej. "qwen3-vl:4b"
    version: str = ""                # versión del motor o del runtime
    licencia: str = ""
    local: bool = True               # False si el procesamiento sale del equipo
    detalle: str = ""                # motivo de no disponibilidad, si aplica

    def a_dict(self) -> dict:
        return {"nombre": self.nombre, "modelo": self.modelo, "version": self.version, "licencia": self.licencia,
                "local": self.local, "detalle": self.detalle}


@dataclass
class OpcionesReconocimiento:
    tarea: str = "texto_impreso"     # una de CAPACIDADES
    idiomas: str = "spa+eng"
    timeout_s: float | None = None   # None = el del motor


@dataclass
class ResultadoMotor:
    """Propuesta de un motor para UNA imagen o recorte."""
    motor: InfoMotor
    tarea: str
    texto: str = ""
    latex: str | None = None
    descripcion: str | None = None
    # Confianza solo si el motor la da calibrada (Tesseract por palabra). Un VLM no la da: None.
    confianza: float | None = None
    ilegible: bool = False           # el motor declara que no puede leerlo
    segundos: float = 0.0
    extra: dict = field(default_factory=dict)


class MotorReconocimiento:
    nombre = "base"

    def disponible(self) -> bool:
        raise NotImplementedError

    def capacidades(self) -> set[str]:
        raise NotImplementedError

    def info_modelo(self) -> InfoMotor:
        raise NotImplementedError

    def reconocer(self, imagen: np.ndarray, opciones: OpcionesReconocimiento) -> ResultadoMotor:
        raise NotImplementedError


class MotorTesseractAdaptador(MotorReconocimiento):
    """Tesseract (el motor actual) detrás de la interfaz común. Sin cambiar su uso en el
    flujo de análisis (services/reconocimiento.py), que sigue llamándolo directamente."""

    nombre = "tesseract"

    def __init__(self, motor=None):
        from app.services.ocr import motor_ocr
        self._motor = motor or motor_ocr()

    def disponible(self) -> bool:
        return self._motor.disponible()

    def capacidades(self) -> set[str]:
        # Texto impreso y, con calidad limitada y medida (BACK-14/28), manuscrito y fórmulas en línea.
        return {"texto_impreso", "texto_manuscrito", "formula", "layout"}

    def info_modelo(self) -> InfoMotor:
        from app.core.config import settings
        info = self._motor.info() if self.disponible() else {}
        return InfoMotor("tesseract", f"LSTM ({settings.ocr_idiomas})" if info else "",
                         str(info.get("version", "")), "Apache-2.0", True,
                         "" if info else "Tesseract no responde: instálalo o define TESSERACT_CMD")

    def reconocer(self, imagen: np.ndarray, opciones: OpcionesReconocimiento) -> ResultadoMotor:
        import time
        from app.services.ocr import ErrorOCR, reconocer
        if not self.disponible():
            raise ErrorMotor("NO_DISPONIBLE", "Tesseract no está disponible.")
        inicio = time.perf_counter()
        try:
            bloques = reconocer(imagen, idiomas=opciones.idiomas, psm=6, motor=self._motor)
        except ErrorOCR as exc:
            raise ErrorMotor("NO_DISPONIBLE", exc.mensaje) from exc
        total = sum(len(b.texto) for b in bloques)
        conf = sum(b.confianza * len(b.texto) for b in bloques) / total if total else None
        return ResultadoMotor(self.info_modelo(), opciones.tarea, "\n".join(b.texto for b in bloques),
                              confianza=round(conf, 3) if conf is not None else None, ilegible=not total,
                              segundos=round(time.perf_counter() - inicio, 3))
