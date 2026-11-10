"""App FastAPI real con la maquetación del PDF lenta (3 s), SOLO para pruebas de
integración (FRONT-16): permite probar cancelar y recargar con la exportación en curso.

No se importa nunca desde el código de producción.
"""

import time

from app.main import app  # noqa: F401  (la que se sirve)
from app.services import exportacion

_original = exportacion.generar_pdf


def _lento(*a, **k):
    time.sleep(3)
    return _original(*a, **k)


exportacion.generar_pdf = _lento
