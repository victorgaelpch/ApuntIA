"""Adaptador de la API HTTP de Ollama (BACK-35). Basado en el adaptador del PR #92.

- Solo habla con un Ollama en 127.0.0.1 (lo garantiza `config.validar`) y solo con rutas de
  lectura e inferencia: nunca `/api/pull`, `/api/delete` ni `/api/create`. Descargar el modelo
  es un paso explícito del instalador (FULL-30), no algo que haga una petición.
- Cada llamada tiene tiempo máximo; los fallos se convierten en `ErrorIA` con código del
  catálogo (NO_DISPONIBLE, MODELO_NO_INSTALADO, SIN_MEMORIA, TIEMPO_AGOTADO, RESPUESTA_INVALIDA).
- El transporte es inyectable: las pruebas usan un Ollama falso sin red ni GPU.

Referencias: https://docs.ollama.com/api/chat (images en base64, `format` con esquema JSON,
`keep_alive`, `options`), https://ollama.com/library/qwen3-vl (requiere Ollama 0.12.7).
"""

from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request
from typing import Callable

from ia_servidor.errores import ErrorIA

VERSION_MINIMA = (0, 12, 7)
RUTAS_PERMITIDAS = {"/api/version", "/api/tags", "/api/show", "/api/ps", "/api/chat"}
MAX_RESPUESTA = 5_000_000  # bytes leídos como máximo de Ollama

# (método, url, cuerpo JSON o None, timeout) → (estado HTTP, cuerpo)
Transporte = Callable[[str, str, dict | None, float], tuple[int, bytes]]


def transporte_urllib(metodo: str, url: str, cuerpo: dict | None, timeout: float) -> tuple[int, bytes]:
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(url, data=datos, method=metodo, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as r:  # noqa: S310 (URL loopback validada)
            return r.status, r.read(MAX_RESPUESTA)
    except urllib.error.HTTPError as e:
        return e.code, e.read(20_000) or b""


def version_tupla(texto: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", texto or "")[:3]) or (0,)


def _es_oom(texto: str) -> bool:
    t = texto.lower()
    return any(p in t for p in ("out of memory", "cuda error", "cudamalloc", "insufficient memory",
                                "requires more system memory", "oom"))


class ClienteOllama:
    def __init__(self, url: str, transporte: Transporte = transporte_urllib):
        self.url = url.rstrip("/")
        self.transporte = transporte

    def _pedir(self, ruta: str, cuerpo: dict | None = None, timeout: float = 5.0, modelo: str = "") -> dict:
        if ruta not in RUTAS_PERMITIDAS:  # defensa en profundidad: ninguna otra ruta se llama nunca
            raise ErrorIA("ERROR_INTERNO", f"ruta de Ollama no permitida: {ruta}")
        try:
            estado, datos = self.transporte("POST" if cuerpo is not None else "GET", self.url + ruta, cuerpo, timeout)
        except (TimeoutError, socket.timeout):
            raise ErrorIA("TIEMPO_AGOTADO", f"{ruta} superó {timeout:.0f} s") from None
        except urllib.error.URLError as e:
            if isinstance(e.reason, (TimeoutError, socket.timeout)):
                raise ErrorIA("TIEMPO_AGOTADO", f"{ruta} superó {timeout:.0f} s") from None
            raise ErrorIA("NO_DISPONIBLE", f"sin conexión con Ollama ({type(e.reason).__name__})") from None
        except OSError as e:
            raise ErrorIA("NO_DISPONIBLE", f"sin conexión con Ollama ({type(e).__name__})") from None
        texto = datos.decode("utf-8", "replace")
        if estado != 200:
            if _es_oom(texto):
                raise ErrorIA("SIN_MEMORIA", f"{ruta} HTTP {estado}: memoria insuficiente")
            if estado == 404 or "not found" in texto.lower():
                raise ErrorIA("MODELO_NO_INSTALADO", f"{ruta} HTTP {estado}: modelo «{modelo}» no encontrado")
            raise ErrorIA("NO_DISPONIBLE", f"{ruta} HTTP {estado}")
        try:
            resultado = json.loads(texto)
        except json.JSONDecodeError:
            raise ErrorIA("RESPUESTA_INVALIDA", f"{ruta}: Ollama no devolvió JSON") from None
        if not isinstance(resultado, dict):
            raise ErrorIA("RESPUESTA_INVALIDA", f"{ruta}: respuesta que no es un objeto")
        return resultado

    # ------------------------------------------------------------------ consulta
    def version(self) -> str:
        return str(self._pedir("/api/version").get("version", ""))

    def modelos(self) -> dict[str, dict]:
        """Modelos instalados: nombre → {tamaño en bytes, cuantización}."""
        salida = {}
        for m in self._pedir("/api/tags").get("models") or []:
            nombre = m.get("name") or m.get("model")
            if nombre:
                salida[nombre] = {"bytes": m.get("size"),
                                  "cuantizacion": (m.get("details") or {}).get("quantization_level")}
        return salida

    def capacidades(self, modelo: str) -> list[str]:
        return list(self._pedir("/api/show", {"model": modelo}, modelo=modelo).get("capabilities") or [])

    def cargados(self) -> list[dict]:
        """Modelos en memoria ahora mismo, con su VRAM (bytes) según /api/ps."""
        return [{"nombre": m.get("name") or m.get("model"), "vram_bytes": m.get("size_vram"), "bytes": m.get("size")}
                for m in self._pedir("/api/ps").get("models") or []]

    # ------------------------------------------------------------------ inferencia
    def chat(self, modelo: str, mensajes: list[dict], esquema: dict, keep_alive: str, timeout: float,
             num_ctx: int = 8192, max_tokens: int = 2048) -> dict:
        # think=False lo ignoran las variantes «thinking» (medido: siguen razonando); por eso el
        # tope de tokens es obligatorio y el modelo recomendado es la variante -instruct.
        cuerpo = {
            "model": modelo, "stream": False, "format": esquema, "keep_alive": keep_alive, "think": False,
            "options": {"temperature": 0, "seed": 0, "num_ctx": num_ctx, "num_predict": max_tokens},
            "messages": mensajes,
        }
        respuesta = self._pedir("/api/chat", cuerpo, timeout=timeout, modelo=modelo)
        contenido = (respuesta.get("message") or {}).get("content")
        if not isinstance(contenido, str):
            raise ErrorIA("RESPUESTA_INVALIDA", "/api/chat sin message.content")
        if respuesta.get("done_reason") == "length":
            raise ErrorIA("RESPUESTA_INVALIDA", "la respuesta del modelo se cortó por longitud")
        return {"contenido": contenido, "tokens_salida": respuesta.get("eval_count"),
                "segundos_modelo": round((respuesta.get("total_duration") or 0) / 1e9, 2),
                "segundos_carga": round((respuesta.get("load_duration") or 0) / 1e9, 2)}
