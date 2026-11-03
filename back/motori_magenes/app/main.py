"""Punto de creación de la aplicación FastAPI."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errores import ApiError, manejar_api_error
from app.routers import general, imagenes

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    """Construye la aplicación, registra middleware y rutas."""
    app = FastAPI(title=settings.app_name, version=settings.version)
    app.add_exception_handler(ApiError, manejar_api_error)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(general.router)
    app.include_router(imagenes.router)
    return app


app = create_app()
