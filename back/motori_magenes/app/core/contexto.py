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

logger = logging.getLogger("apuntia.contexto")


@dataclass
class Contexto:
    data_dir: Path
    bd: BaseDatos
    almacen: Almacen


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
        _ctx = Contexto(carpeta, bd, almacen)
        return _ctx


def obtener() -> Contexto:
    return _ctx if _ctx is not None else iniciar()


def reiniciar(data_dir: Path) -> Contexto:
    """Para pruebas: cambia de carpeta de datos."""
    global _ctx
    if _ctx is not None:
        _ctx.bd.cerrar()
        _ctx = None
    return iniciar(data_dir)
