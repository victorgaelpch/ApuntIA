"""Configuración del servidor IA, solo desde variables de entorno (plantilla: .env.example).

No hay secretos aquí: la autenticación de dispositivos llega con FULL-31. Mientras tanto el
servicio se niega a escuchar fuera de 127.0.0.1 (ver `validar`).
"""

from __future__ import annotations

import ipaddress
import os
import re
import urllib.parse
from dataclasses import dataclass, field

MODELO_VALIDO = re.compile(r"^[a-z0-9][a-z0-9._\-/]{0,120}(:[A-Za-z0-9._\-]{1,80})?$")


def carpeta_datos(valor: str = ""):
    from pathlib import Path
    return Path(valor) if valor else Path(__file__).resolve().parent / ".datos"


class ConfiguracionInvalida(ValueError):
    """La configuración no permite arrancar con seguridad."""


def _entero(nombre: str, defecto: int, minimo: int, maximo: int) -> int:
    crudo = os.environ.get(nombre, "").strip()
    if not crudo:
        return defecto
    try:
        valor = int(crudo)
    except ValueError:
        raise ConfiguracionInvalida(f"{nombre} debe ser un número entero") from None
    if not minimo <= valor <= maximo:
        raise ConfiguracionInvalida(f"{nombre} debe estar entre {minimo} y {maximo}")
    return valor


TAILSCALE = ipaddress.ip_network("100.64.0.0/10")  # direcciones de Tailscale (CGNAT)


def es_tailscale(host: str) -> bool:
    try:
        return ipaddress.ip_address(host) in TAILSCALE
    except ValueError:
        return False


def _decimal(nombre: str, defecto: float, minimo: float, maximo: float) -> float:
    crudo = os.environ.get(nombre, "").strip()
    if not crudo:
        return defecto
    try:
        valor = float(crudo)
    except ValueError:
        raise ConfiguracionInvalida(f"{nombre} debe ser un número") from None
    if not minimo <= valor <= maximo:
        raise ConfiguracionInvalida(f"{nombre} debe estar entre {minimo} y {maximo}")
    return valor


def es_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


@dataclass(frozen=True)
class Configuracion:
    host: str = "127.0.0.1"                     # dónde escucha ESTE servicio
    puerto: int = 8100
    ollama_url: str = "http://127.0.0.1:11434"  # Ollama: solo loopback
    modelo: str = "qwen3-vl:8b-instruct"        # 6,2 GB Q4_K_M, sin «thinking» (servidor-ia.md §8)
    modelo_respaldo: str = "qwen3-vl:4b-instruct"  # 3,3 GB: perfil de menor consumo, opcional
    max_mb: int = 10
    max_megapixeles: int = 40
    max_lado_modelo: int = 1600                 # px del lado mayor que se envían al modelo
    max_inferencias: int = 1                    # 12 GB de VRAM: un modelo pesado a la vez
    espera_cola_s: int = 20                     # cuánto espera una petición su turno antes de 429
    timeout_s: int = 180                        # tiempo máximo de una inferencia
    keep_alive: str = "10m"                     # cuánto queda el modelo en VRAM tras usarse
    num_ctx: int = 8192                         # contexto: imagen (~1-2 K tokens) + respuesta; 4096 (defecto de Ollama) se queda corto
    max_tokens: int = 2048                      # tope de tokens generados (incluido el «razonamiento» de modelos thinking)
    min_disco_mb: int = 2048                    # espacio libre mínimo para considerar el equipo listo
    datos: str = ""                             # registro de dispositivos; vacío = ia_servidor/.datos
    max_analisis_min: int = 30                  # análisis por minuto y dispositivo (429 al pasarse)
    max_regiones: int = 40                      # tarea «documento»: regiones como máximo por página
    seg_hueco_lineas: float = 0.2               # unir líneas del mismo párrafo (alturas de letra; 0 = no unir). Medido: §5.2
    formatos: tuple[str, ...] = field(default=("jpeg", "png", "webp"))

    @classmethod
    def desde_entorno(cls) -> "Configuracion":
        c = cls(
            host=os.environ.get("IA_HOST", "127.0.0.1").strip(),
            puerto=_entero("IA_PUERTO", 8100, 1024, 65535),
            ollama_url=os.environ.get("IA_OLLAMA_URL", "http://127.0.0.1:11434").strip().rstrip("/"),
            modelo=os.environ.get("IA_MODELO", "qwen3-vl:8b-instruct").strip(),
            modelo_respaldo=os.environ.get("IA_MODELO_RESPALDO", "qwen3-vl:4b-instruct").strip(),
            max_mb=_entero("IA_MAX_MB", 10, 1, 50),
            max_megapixeles=_entero("IA_MAX_MEGAPIXELES", 40, 1, 100),
            max_lado_modelo=_entero("IA_MAX_LADO_MODELO", 1600, 448, 4096),
            max_inferencias=_entero("IA_MAX_INFERENCIAS", 1, 1, 4),
            espera_cola_s=_entero("IA_ESPERA_COLA_S", 20, 0, 600),
            timeout_s=_entero("IA_TIMEOUT_S", 180, 10, 1800),
            keep_alive=os.environ.get("IA_KEEP_ALIVE", "10m").strip(),
            num_ctx=_entero("IA_NUM_CTX", 8192, 2048, 32768),
            max_tokens=_entero("IA_MAX_TOKENS", 2048, 256, 16384),
            min_disco_mb=_entero("IA_MIN_DISCO_MB", 2048, 0, 10_000_000),
            datos=os.environ.get("IA_DATOS", "").strip(),
            max_analisis_min=_entero("IA_MAX_ANALISIS_MIN", 30, 1, 600),
            max_regiones=_entero("IA_MAX_REGIONES", 40, 1, 200),
            seg_hueco_lineas=_decimal("IA_SEG_HUECO_LINEAS", 0.2, 0.0, 3.0),
        )
        c.validar()
        return c

    def validar(self) -> None:
        if not (es_loopback(self.host) or es_tailscale(self.host)):
            raise ConfiguracionInvalida(
                f"IA_HOST={self.host}: el servidor IA solo escucha en 127.0.0.1 (para el túnel de Cloudflare, "
                "que se conecta ahí) o en la dirección 100.x de Tailscale. Nunca en 0.0.0.0 ni en la red "
                "local: así solo se llega por un canal cifrado y con vinculación (FULL-31).")
        partes = urllib.parse.urlsplit(self.ollama_url)
        if partes.scheme != "http" or not partes.hostname or not es_loopback(partes.hostname):
            raise ConfiguracionInvalida("IA_OLLAMA_URL debe ser http://127.0.0.1:<puerto>: Ollama nunca se usa "
                                        "a través de la red")
        if partes.username or partes.password or partes.path not in ("", "/") or partes.query:
            raise ConfiguracionInvalida("IA_OLLAMA_URL no admite credenciales, rutas ni parámetros")
        for nombre, modelo in (("IA_MODELO", self.modelo), ("IA_MODELO_RESPALDO", self.modelo_respaldo)):
            if modelo and not MODELO_VALIDO.match(modelo):
                raise ConfiguracionInvalida(f"{nombre} no tiene el formato nombre:etiqueta")
            if "cloud" in modelo.split(":")[-1] or modelo.endswith("-cloud"):
                raise ConfiguracionInvalida(f"{nombre}={modelo}: los modelos «cloud» procesan las fotos fuera "
                                            "del equipo")
        if not re.fullmatch(r"-?\d+[smh]?", self.keep_alive):
            raise ConfiguracionInvalida("IA_KEEP_ALIVE debe ser como 10m, 300s, 1h o 0")
