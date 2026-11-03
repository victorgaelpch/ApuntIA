"""Compatibilidad: permite seguir usando ``uvicorn index:app --reload``.

La lógica se movió al paquete ``app``. Usar preferentemente ``main:app``.
"""

from app.main import app

__all__ = ["app"]
