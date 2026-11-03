"""Configuración central del backend.

Todos los valores se leen desde variables de entorno (o desde un archivo
``.env`` ubicado en ``back/motori_magenes``) para evitar rutas o datos
sensibles escritos directamente en el código.
"""

import os
from pathlib import Path

# Carpeta raíz del servicio: back/motori_magenes
BASE_DIR = Path(__file__).resolve().parents[2]


def _cargar_env(ruta: Path) -> None:
    """Carga un archivo .env sencillo (CLAVE=valor) sin dependencias extra.

    Las variables ya definidas en el entorno tienen prioridad.
    """
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env(BASE_DIR / ".env")


class Settings:
    """Valores de configuración de la aplicación."""

    app_name: str = os.getenv("APP_NAME", "ApuntIA - Motor de imágenes")

    version: str = "1.0.0"

    # Límites de las imágenes recibidas (ver docs/api.md).
    max_upload_mb: float = float(os.getenv("MAX_UPLOAD_MB", "10"))
    max_megapixeles: float = float(os.getenv("MAX_MEGAPIXELES", "50"))

    # Orígenes permitidos por CORS, separados por comas. "*" permite todos.
    cors_origins: list[str] = [
        origen.strip()
        for origen in os.getenv("CORS_ORIGINS", "*").split(",")
        if origen.strip()
    ]


settings = Settings()
