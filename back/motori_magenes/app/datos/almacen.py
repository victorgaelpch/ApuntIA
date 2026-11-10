"""Almacenamiento privado de archivos (BACK-22).

Los archivos se guardan en DATA_DIR/archivos/<usuario>/<id> sin extensión ni
nombre original, y SOLO se entregan a través de rutas de la API que comprueban
que el usuario autenticado es el propietario. La carpeta nunca se monta como
estática. La escritura es atómica (archivo temporal + rename): un corte a mitad
no deja archivos truncados.
"""

import errno
import logging
import shutil
import hashlib
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.errores import ApiError
from app.datos.bd import BaseDatos, ahora

TIPOS = {"original", "procesada", "recorte", "pdf"}


class ArchivoNoEncontrado(LookupError):
    """No existe o no pertenece al usuario."""


@dataclass
class Archivo:
    id: str
    usuario_id: str
    apunte_id: str | None
    tipo: str
    mime: str
    tamano: int
    ruta: Path


def nuevo_id() -> str:
    return secrets.token_hex(16)


class Almacen:
    def __init__(self, base: Path, bd: BaseDatos):
        self.base = Path(base) / "archivos"
        self.tmp = Path(base) / "tmp"
        self.base.mkdir(parents=True, exist_ok=True)
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.bd = bd

    def guardar(self, usuario_id: str, datos: bytes, tipo: str, mime: str,
                apunte_id: str | None = None, con=None) -> str:
        if tipo not in TIPOS:
            raise ValueError(f"tipo de archivo no válido: {tipo}")
        archivo_id = nuevo_id()
        relativa = Path(usuario_id) / archivo_id
        destino = self.base / relativa
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.tmp / f"{archivo_id}.parcial"
        try:
            with open(temporal, "wb") as f:
                f.write(datos)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporal, destino)
        except OSError as exc:
            temporal.unlink(missing_ok=True)
            if exc.errno in (errno.ENOSPC, errno.EDQUOT):
                raise ApiError(507, "ALMACENAMIENTO_LLENO",
                               "El servidor no tiene espacio para guardar más archivos. Avisa al administrador.") from None
            raise
        try:  # alerta temprana de disco (FULL-21)
            libre_mb = shutil.disk_usage(self.base).free // (1024 * 1024)
            if libre_mb < settings.minimo_disco_mb:
                logging.getLogger("apuntia.almacen").warning("ALERTA quedan %d MB libres en DATA_DIR", libre_mb)
        except OSError:
            pass
        params = (archivo_id, usuario_id, apunte_id, tipo, mime, len(datos),
                  hashlib.sha256(datos).hexdigest(), str(relativa), ahora())
        sql = "INSERT INTO archivos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        try:
            if con is not None:
                con.execute(sql, params)
            else:
                self.bd.ejecutar(sql, params)
        except Exception:
            destino.unlink(missing_ok=True)
            raise
        return archivo_id

    def obtener(self, usuario_id: str, archivo_id: str) -> Archivo:
        """Devuelve el archivo solo si pertenece al usuario."""
        fila = self.bd.uno("SELECT * FROM archivos WHERE id = ? AND usuario_id = ?", (archivo_id, usuario_id))
        if fila is None:
            raise ArchivoNoEncontrado(archivo_id)
        ruta = (self.base / fila["ruta"]).resolve()
        if self.base.resolve() not in ruta.parents or not ruta.is_file():
            raise ArchivoNoEncontrado(archivo_id)
        return Archivo(fila["id"], fila["usuario_id"], fila["apunte_id"], fila["tipo"],
                       fila["mime"], fila["tamano"], ruta)

    def leer(self, usuario_id: str, archivo_id: str) -> bytes:
        return self.obtener(usuario_id, archivo_id).ruta.read_bytes()

    def borrar_de_apunte(self, apunte_id: str) -> int:
        filas = self.bd.todos("SELECT ruta FROM archivos WHERE apunte_id = ?", (apunte_id,))
        for fila in filas:
            (self.base / fila["ruta"]).unlink(missing_ok=True)
        return len(filas)

    def borrar_de_usuario(self, usuario_id: str) -> None:
        carpeta = self.base / usuario_id
        if carpeta.is_dir():
            for archivo in carpeta.iterdir():
                archivo.unlink(missing_ok=True)
            carpeta.rmdir()

    def limpiar_temporales(self, antiguedad_s: int = 3600) -> int:
        """Borra escrituras a medias (de un apagado brusco)."""
        limite = time.time() - antiguedad_s
        borrados = 0
        for parcial in self.tmp.glob("*.parcial"):
            if parcial.stat().st_mtime < limite:
                parcial.unlink(missing_ok=True)
                borrados += 1
        return borrados
