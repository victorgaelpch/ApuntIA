"""Punto de entrada para uvicorn.

Ejecutar desde back/motori_magenes:

    uvicorn main:app --reload
"""

from app.main import app

__all__ = ["app"]
