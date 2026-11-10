"""Reconocimiento de una página: el flujo completo de una foto a bloques (BACK-28).

Reúne en un solo lugar las etapas que antes encadenaba `analisis.py`:

    preprocesado por perfil (BACK-12) → OCR por bloques (BACK-13)
    → respaldo de manuscritos (BACK-14) → fórmulas a LaTeX (BACK-15)

Modos (variable RECONOCIMIENTO_MODO):
  - «adaptativo» (por defecto): diagnóstico de calidad (services/calidad.py), texto
    enderezado, lectura por región con variantes, consenso y fórmulas
    (services/adaptativo.py), y procedencia en cada bloque;
  - «clasico»: el flujo anterior a BACK-28, sin cambios. Se conserva para comparar
    y como vuelta atrás si el adaptativo diera problemas en algún equipo.
"""

from dataclasses import dataclass, field

import numpy as np

from app.core.config import settings
import logging

from app.services import adaptativo
from app.services.calidad import Calidad, diagnosticar
from app.services.formulas import separar_formulas
from app.services.manuscrito import leer_con_respaldo
from app.services.ocr import BloqueOCR, MotorOCR, motor_ocr, reconocer
from app.services.preprocesado_ocr import Preprocesado, preprocesar_para_ocr

logger = logging.getLogger("apuntia.reconocimiento")

MODOS = ("adaptativo", "clasico")


@dataclass
class ResultadoPagina:
    pre: Preprocesado
    bloques: list[BloqueOCR]
    modo: str
    advertencias: list[str] = field(default_factory=list)
    calidad: Calidad | None = None


def reconocer_pagina(imagen: np.ndarray, tipo_fuente: str, idiomas: str | None = None,
                     modo: str | None = None, motor: MotorOCR | None = None) -> ResultadoPagina:
    """Foto (BGR) → bloques en orden de lectura. La imagen recibida no se modifica."""
    modo = modo or settings.reconocimiento_modo
    if modo not in MODOS:
        modo = "adaptativo"
    idiomas = idiomas or settings.ocr_idiomas
    motor = motor or motor_ocr()
    if modo == "clasico":
        pre = preprocesar_para_ocr(imagen, tipo_fuente)
        bloques = reconocer(pre.imagen_ocr, idiomas=idiomas, psm=pre.psm, motor=motor)
        bloques = leer_con_respaldo(pre.imagen_ocr, bloques, idiomas, motor=motor)
        bloques = separar_formulas(bloques)
        return ResultadoPagina(pre, bloques, modo, list(pre.advertencias))

    pre = preprocesar_para_ocr(imagen, tipo_fuente, enderezar_texto=True)
    calidad = diagnosticar(imagen, pre.inclinacion, pre.imagen_vista)
    # Solo métricas numéricas en el log: nunca texto ni imágenes del usuario.
    logger.info("calidad de página: nivel=%s avisos=%s metricas=%s", calidad.nivel, calidad.avisos, calidad.metricas)
    base = {"motor": motor.nombre, "version": _version(motor), "reconocimiento": adaptativo.VERSION, "psm": pre.psm}
    bloques = reconocer(pre.imagen_ocr, idiomas=idiomas, psm=pre.psm, motor=motor)
    bloques = adaptativo.leer_adaptativo(pre.imagen_ocr, bloques, idiomas, motor, base)
    bloques = separar_formulas(bloques)
    bloques = adaptativo.refinar_formulas(pre.imagen_ocr, bloques, idiomas, motor, base)
    if calidad.nivel == "insuficiente":
        # Con una foto así nada se puede dar por seguro: todo queda para revisar.
        for b in bloques:
            if b.texto:
                b.revision = b.revision or "calidad_insuficiente"
                b.recortar = True
    return ResultadoPagina(pre, bloques, modo, list(calidad.avisos), calidad)


_versiones: dict[str, str] = {}


def _version(motor: MotorOCR) -> str:
    """Versión del motor (una consulta por proceso: es un subproceso en Tesseract)."""
    if motor.nombre not in _versiones:
        try:
            _versiones[motor.nombre] = str(motor.info().get("version", "")) or "desconocida"
        except Exception:  # noqa: BLE001
            _versiones[motor.nombre] = "desconocida"
    return _versiones[motor.nombre]
