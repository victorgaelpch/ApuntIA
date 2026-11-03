"""App FastAPI real con fallos inyectados, SOLO para pruebas de integración (FULL-07).

    APUNTIA_FALLO=procesamiento  -> cv2.error dentro del pipeline (ProcesamientoError, 500)
    APUNTIA_FALLO=inesperado     -> RuntimeError al codificar (excepción no prevista, 500)
    APUNTIA_FALLO=lento          -> el procesamiento tarda 3 s más

No se importa nunca desde el código de producción.
"""

import os
import time

import cv2

from app.main import app  # noqa: F401  (la que se sirve)
from app.routers import imagenes
from app.services import procesamiento

MODO = os.environ.get("APUNTIA_FALLO", "")

if MODO == "procesamiento":
    def _fallo_ruido(*_a, **_k):
        raise cv2.error("fallo simulado en el filtro de ruido")
    procesamiento.eliminar_ruido = _fallo_ruido
elif MODO == "inesperado":
    def _fallo_png(*_a, **_k):
        raise RuntimeError("fallo inesperado simulado /ruta/interna")
    imagenes.codificar_png = _fallo_png
elif MODO == "lento":
    _original = imagenes.procesar
    def _lento(*a, **k):
        time.sleep(3)
        return _original(*a, **k)
    imagenes.procesar = _lento
