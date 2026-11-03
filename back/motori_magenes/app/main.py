"""Punto de creación de la aplicación FastAPI."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errores import registrar_manejadores
from app.routers import general, imagenes

logging.basicConfig(level=logging.INFO)

CABECERAS_EXPUESTAS = [
    "Content-Disposition",
    "X-ApuntIA-Archivo",
    "X-ApuntIA-Perspectiva",
    "X-ApuntIA-Dimensiones",
    "X-ApuntIA-Tiempo-Ms",
    "X-ApuntIA-Error-Id",
]


def create_app() -> FastAPI:
    """Construye la aplicación, registra middleware y rutas."""
    app = FastAPI(title=settings.app_name, version=settings.version)
    registrar_manejadores(app)

    # CORS (FULL-04): el frontend se sirve desde otro origen (file://, :5500, la IP
    # del PC...). Hay que exponer las cabeceras del contrato para que el navegador
    # deje leerlas. No se usan credenciales ni cookies.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=CABECERAS_EXPUESTAS,
    )

    app.include_router(general.router)
    app.include_router(imagenes.router)
    return app


app = create_app()
