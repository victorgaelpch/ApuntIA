"""Acceso al OpenCV del backend SIN copiarlo (BACK-35).

`back/motori_magenes/app/services/calidad.py` y `perspectiva.py` son funciones puras de OpenCV
y numpy. Se importan desde su ubicación real para que exista una sola versión; la prueba
`test_no_importa_bd_ni_config_del_cliente` garantiza que esto no arrastra la base de datos, las
cuentas ni la configuración del cliente.

Si el backend no está junto a este servicio (copia parcial del repositorio), el diagnóstico de
calidad se omite y la respuesta lo indica; la inferencia sigue funcionando.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parents[1] / "back" / "motori_magenes"


def _cargar():
    if BACKEND.is_dir() and str(BACKEND) not in sys.path:
        sys.path.append(str(BACKEND))  # al final: no oculta paquetes instalados
    try:
        from app.services import calidad, perspectiva
        return calidad, perspectiva
    except ImportError:
        return None, None


calidad, perspectiva = _cargar()


def diagnosticar(imagen: np.ndarray) -> dict:
    """Calidad de la foto (nitidez, contraste, resolución, tamaño de letra) y si se detectó la hoja
    o el pizarrón. Nunca modifica la imagen."""
    if calidad is None or perspectiva is None:
        return {"disponible": False, "detalle": "módulos de calidad del backend no encontrados"}
    try:
        deteccion = perspectiva.detectar_pizarron(imagen)
        vista = None
        if deteccion.esquinas is not None:
            vista = perspectiva.rectificar(imagen, deteccion.esquinas)
        resultado = calidad.diagnosticar(imagen, vista=vista).a_dict()
        resultado["hoja_detectada"] = deteccion.esquinas is not None
        resultado["disponible"] = True
        return resultado
    except Exception as exc:  # el diagnóstico es informativo: nunca tumba la inferencia
        return {"disponible": False, "detalle": f"fallo del diagnóstico: {type(exc).__name__}"}
