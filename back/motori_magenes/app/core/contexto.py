"""Recursos compartidos de la aplicación: base de datos y almacén privado.

Se inicializan al arrancar (lifespan) o, si no, en el primer uso. Las pruebas
llaman a `reiniciar(carpeta)` para trabajar con una carpeta temporal.
"""

import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.datos.almacen import Almacen
from app.datos.bd import BaseDatos
from app.services.trabajos import GestorTrabajos

logger = logging.getLogger("apuntia.contexto")


@dataclass
class Contexto:
    data_dir: Path
    bd: BaseDatos
    almacen: Almacen
    trabajos: GestorTrabajos


_ctx: Contexto | None = None
_bloqueo = threading.Lock()


def iniciar(data_dir: Path | None = None) -> Contexto:
    global _ctx
    with _bloqueo:
        carpeta = Path(data_dir or settings.data_dir)
        carpeta.mkdir(parents=True, exist_ok=True)
        bd = BaseDatos(carpeta / "apuntia.sqlite3")
        aplicadas = bd.migrar()
        if aplicadas:
            logger.info("Base de datos lista (%s); migraciones nuevas: %s", carpeta.name, aplicadas)
        almacen = Almacen(carpeta, bd)
        almacen.limpiar_temporales()
        trabajos = GestorTrabajos(bd)
        _ctx = Contexto(carpeta, bd, almacen, trabajos)
        for registrar in _REGISTRADORES:
            registrar(_ctx)
        return _ctx


# Funciones que registran manejadores de trabajos (las añaden los servicios).
_REGISTRADORES: list = []


def al_iniciar(funcion):
    _REGISTRADORES.append(funcion)
    if _ctx is not None:
        funcion(_ctx)
    return funcion


def obtener() -> Contexto:
    return _ctx if _ctx is not None else iniciar()


def reiniciar(data_dir: Path) -> Contexto:
    """Para pruebas: cambia de carpeta de datos."""
    global _ctx
    if _ctx is not None:
        _ctx.trabajos.detener(esperar=True)
        _ctx.bd.cerrar()
        _ctx = None
    return iniciar(data_dir)


def detener() -> None:
    if _ctx is not None:
        _ctx.trabajos.detener(esperar=False)
