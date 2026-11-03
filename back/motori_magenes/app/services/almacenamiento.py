"""Servicio de almacenamiento de archivos en disco."""

from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


def asegurar_directorio() -> Path:
    """Crea la carpeta de imágenes si no existe y la devuelve."""
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    return settings.images_dir


def nombre_seguro(nombre: str | None) -> str:
    """Elimina componentes de ruta para evitar escrituras fuera de la carpeta."""
    limpio = Path(nombre or "").name
    return limpio or "imagen.png"


def guardar_archivo(file: UploadFile) -> Path:
    """Guarda el archivo subido en la carpeta configurada y devuelve su ruta."""
    destino = asegurar_directorio() / nombre_seguro(file.filename)
    with open(destino, "wb") as f:
        f.write(file.file.read())
    return destino
