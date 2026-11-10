"""Punto de creación de la aplicación FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import contexto
from app.core.config import settings
from app.core.diagnostico import IdPeticion, configurar_logs
from app.core.endurecimiento import CabecerasSeguridad, LimiteCuerpo
from app.core.errores import CapturarErroresInesperados, registrar_manejadores
from app.routers import frontend, general, v2_diagnostico, imagenes, v2_apuntes, v2_cuentas, v2_exportaciones, v2_formulas, v2_investigacion, v2_trabajos

logging.basicConfig(level=logging.INFO)
configurar_logs()  # id de petición y datos sensibles enmascarados en cada línea (FULL-21)

CABECERAS_EXPUESTAS = [
    "Content-Disposition",
    "X-ApuntIA-Archivo",
    "X-ApuntIA-Perspectiva",
    "X-ApuntIA-Dimensiones",
    "X-ApuntIA-Tiempo-Ms",
    "X-ApuntIA-Error-Id",
    "X-ApuntIA-Sha256",
    "X-ApuntIA-Peticion-Id",
]


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    # Aplica las migraciones pendientes y limpia temporales antes de atender peticiones.
    ctx = contexto.iniciar()
    ctx.trabajos.iniciar()  # recupera los trabajos interrumpidos y empieza a procesar
    yield
    contexto.detener()


def create_app() -> FastAPI:
    """Construye la aplicación, registra middleware y rutas."""
    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=ciclo_de_vida)
    registrar_manejadores(app)

    # Orden (el último añadido es el más externo): LimiteCuerpo queda dentro de
    # CapturarErroresInesperados para que su 413 no se convierta en un 500.
    app.add_middleware(LimiteCuerpo)
    # Debe registrarse ANTES que CORS para quedar dentro de él (FULL-08, defecto D1).
    app.add_middleware(CapturarErroresInesperados)
    app.add_middleware(CabecerasSeguridad)  # BACK-24: también en errores y 413
    app.add_middleware(IdPeticion)  # FULL-21: id de petición en la respuesta y en los logs

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
    app.include_router(v2_cuentas.router)
    app.include_router(v2_apuntes.router)
    app.include_router(v2_trabajos.router)
    app.include_router(v2_formulas.router)
    app.include_router(v2_investigacion.router)
    app.include_router(v2_exportaciones.router)
    app.include_router(v2_diagnostico.router)
    frontend.registrar(app)
    return app


app = create_app()
