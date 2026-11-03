"""Rutas generales del servicio."""

from fastapi import APIRouter

router = APIRouter(tags=["general"])


@router.get("/")
def holamundo():
    """Comprobación rápida de que el servidor está activo."""
    return {"message": "Hola Mundo"}
