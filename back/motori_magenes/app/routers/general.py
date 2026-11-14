"""Rutas generales del servicio."""

from fastapi import APIRouter

from app.core.config import settings
from app.services import investigacion
from app.services.ocr import motor_ocr
from app.services.validacion import FORMATOS_PERMITIDOS

router = APIRouter(tags=["general"])


@router.get("/")
def holamundo():
    """Comprobación rápida de que el servidor está activo."""
    return {"message": "Hola Mundo"}


@router.get("/salud")
def salud():
    """Estado del servicio y límites vigentes (ver fullstack/docs/api.md)."""
    return {
        "estado": "ok",
        "version": settings.version,
        "formatos": list(FORMATOS_PERMITIDOS.values()),
        "max_mb": settings.max_upload_mb,
        "max_megapixeles": settings.max_megapixeles,
        # Campos añadidos en la v2 (el contrato v1 se conserva):
        "ocr": motor_ocr().info(),
        "max_paginas": settings.max_paginas,
        "investigacion": {"proveedor": investigacion.proveedor().nombre,
                          "disponible": investigacion.proveedor().disponible()},
        "base_datos": {"disponible": _base_datos_disponible()},
    }


def _base_datos_disponible() -> bool:
    from app.core import contexto
    try:
        contexto.obtener().bd.uno("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False
