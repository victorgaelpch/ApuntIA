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


def _si(nombre: str, defecto: str = "0") -> bool:
    """Booleano de una variable de entorno: 1, true, si/sí, yes u on (sin distinguir mayúsculas)."""
    return os.getenv(nombre, defecto).strip().lower() in ("1", "true", "si", "sí", "yes", "on")


class Settings:
    """Valores de configuración de la aplicación."""

    app_name: str = os.getenv("APP_NAME", "ApuntIA - Motor de imágenes")

    version: str = "2.0.0"  # ver CHANGELOG.md

    # Límites de las imágenes recibidas (ver docs/api.md).
    max_upload_mb: float = float(os.getenv("MAX_UPLOAD_MB", "10"))
    max_megapixeles: float = float(os.getenv("MAX_MEGAPIXELES", "50"))

    # OCR (BACK-13): motor (tesseract | ninguno), idiomas de Tesseract y ruta
    # opcional al ejecutable (en Windows, si no está en el PATH).
    ocr_motor: str = os.getenv("OCR_MOTOR", "tesseract").strip().lower()
    ocr_idiomas: str = os.getenv("OCR_IDIOMAS", "spa+eng")
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "")

    # Reconocimiento adaptativo (BACK-28): «adaptativo» o «clasico» (el flujo anterior).
    reconocimiento_modo: str = os.getenv("RECONOCIMIENTO_MODO", "adaptativo").strip().lower()
    # Límites por página: variantes por bloque dudoso, bloques que se releen y segundos en total.
    reconocimiento_max_variantes: int = int(os.getenv("RECONOCIMIENTO_MAX_VARIANTES", "4"))
    reconocimiento_max_bloques: int = int(os.getenv("RECONOCIMIENTO_MAX_BLOQUES", "60"))
    reconocimiento_max_segundos: float = float(os.getenv("RECONOCIMIENTO_MAX_SEGUNDOS", "30"))

    # IA local opcional (FULL-30). Desactivada por defecto: el modo básico (OpenCV + Tesseract)
    # no la necesita. Guía: docs/ia-local.md. Nombres del issue → aquí: APUNTIA_AI_ENABLED=IA_ACTIVADA,
    # APUNTIA_OLLAMA_HOST=OLLAMA_HOST, APUNTIA_VLM_MODEL=VLM_MODELO, APUNTIA_RECOGNITION_MODE=RECONOCIMIENTO_PERFIL…
    ia_activada: bool = os.getenv("IA_ACTIVADA", "false").strip().lower() in ("1", "true", "si", "sí", "yes")
    ia_proveedor: str = os.getenv("IA_PROVEEDOR", "ollama").strip().lower()
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip().rstrip("/")
    vlm_modelo: str = os.getenv("VLM_MODELO", "qwen3-vl:4b").strip()
    ia_timeout_s: float = float(os.getenv("IA_TIMEOUT_S", "180"))
    ia_max_inferencias: int = max(1, int(os.getenv("IA_MAX_INFERENCIAS", "1")))
    ia_max_lado_px: int = int(os.getenv("IA_MAX_LADO_PX", "1600"))       # la imagen se reduce antes de enviarla
    # Solo con «true» se permite un servidor fuera del equipo o de la red privada, o un modelo «-cloud»
    # (Ollama Cloud procesa las imágenes en servidores ajenos). Nunca por defecto.
    ia_permitir_externa: bool = os.getenv("IA_PERMITIR_EXTERNA", "false").strip().lower() in ("1", "true", "si", "sí", "yes")
    # rapido | equilibrado | avanzado | automatico (elige según los motores y el equipo disponibles)
    reconocimiento_perfil: str = os.getenv("RECONOCIMIENTO_PERFIL", "automatico").strip().lower()

    # Trabajos largos ejecutados a la vez (BACK-27).
    max_trabajos_simultaneos: int = int(os.getenv("MAX_TRABAJOS_SIMULTANEOS", "2"))

    # Páginas por apunte en la API v2 (BACK-11).
    max_paginas: int = int(os.getenv("MAX_PAGINAS", "20"))

    # Investigación opcional (BACK-18): "wikipedia" o "ninguno" (sin Internet).
    investigacion_proveedor: str = os.getenv("INVESTIGACION_PROVEEDOR", "wikipedia").strip().lower()
    investigacion_timeout_s: float = float(os.getenv("INVESTIGACION_TIMEOUT_S", "6"))

    # Interfaz servida por el propio backend (FRONT-11): misma origen que la API,
    # necesario para la cookie de sesión. Vacío = no se sirve.
    front_dir: str = os.getenv("FRONT_DIR", str(BASE_DIR.parents[1] / "front"))
    pagina_inicio: str = os.getenv("PAGINA_INICIO", str(BASE_DIR.parents[1] / "index.html"))

    # URL pública del servidor (p. ej. https://apuntia.ejemplo.edu) para los enlaces
    # de recuperación de contraseña. Recomendado en producción.
    url_publica: str = os.getenv("URL_PUBLICA", "").strip()

    # Diagnóstico (FULL-21): alertas en el log y espacio mínimo para declararse «listo».
    alerta_peticion_ms: int = int(os.getenv("ALERTA_PETICION_MS", "10000"))
    alerta_trabajo_s: int = int(os.getenv("ALERTA_TRABAJO_S", "120"))
    minimo_disco_mb: int = int(os.getenv("MINIMO_DISCO_MB", "200"))

    # Endurecimiento (BACK-24): cuerpo JSON máximo y espacio por usuario.
    max_json_kb: int = int(os.getenv("MAX_JSON_KB", "4096"))
    cuota_mb_usuario: int = int(os.getenv("CUOTA_MB_USUARIO", "500"))
    # Cuentas nuevas por IP y hora (en un aula detrás de un mismo router puede hacer falta subirlo).
    max_registros_hora: int = int(os.getenv("MAX_REGISTROS_HORA", "10"))

    # Lado mayor con el que se procesa la imagen (BACK-09). 0 = sin límite.
    max_lado_procesamiento: int = int(os.getenv("MAX_LADO_PROCESAMIENTO", "2000"))

    # Datos privados (BACK-22): base de datos SQLite y archivos de los usuarios.
    # Las rutas relativas se resuelven respecto a back/motori_magenes.
    data_dir: Path = (BASE_DIR / os.getenv("DATA_DIR", "datos")).resolve()

    # Cookie de sesión con el atributo Secure (actívalo detrás de HTTPS).
    cookie_segura: bool = _si("COOKIE_SEGURA")

    # Orígenes permitidos por CORS, separados por comas. "*" permite todos.
    cors_origins: list[str] = [
        origen.strip()
        for origen in os.getenv("CORS_ORIGINS", "*").split(",")
        if origen.strip()
    ]


settings = Settings()
