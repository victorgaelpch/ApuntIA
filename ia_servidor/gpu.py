"""Información de la GPU NVIDIA mediante `nvidia-smi` (informativa; no bloquea el arranque).

Ollama también puede correr en CPU (mucho más lento), así que la falta de GPU es un aviso en
/listo, no un error. Se cachea 30 s para no lanzar un proceso por petición.
"""

from __future__ import annotations

import shutil
import subprocess
import threading
import time

_CACHE: tuple[float, dict] | None = None
_BLOQUEO = threading.Lock()
CONSULTA = "name,driver_version,memory.total,memory.used,memory.free"


def leer(ejecutar=subprocess.run, cache_s: float = 30.0) -> dict:
    global _CACHE
    with _BLOQUEO:
        if _CACHE and time.monotonic() - _CACHE[0] < cache_s:
            return _CACHE[1]
        _CACHE = (time.monotonic(), _leer(ejecutar))
        return _CACHE[1]


def _leer(ejecutar) -> dict:
    if shutil.which("nvidia-smi") is None and ejecutar is subprocess.run:
        return {"disponible": False, "detalle": "nvidia-smi no encontrado (sin GPU NVIDIA o sin controlador)"}
    try:
        r = ejecutar(["nvidia-smi", f"--query-gpu={CONSULTA}", "--format=csv,noheader,nounits"],
                     capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"disponible": False, "detalle": f"nvidia-smi falló ({type(e).__name__})"}
    if r.returncode != 0 or not r.stdout.strip():
        return {"disponible": False, "detalle": "nvidia-smi no devolvió datos"}
    gpus = []
    for linea in r.stdout.strip().splitlines():
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) != 5:
            continue
        try:
            gpus.append({"nombre": partes[0], "controlador": partes[1], "vram_total_mb": int(partes[2]),
                         "vram_usada_mb": int(partes[3]), "vram_libre_mb": int(partes[4])})
        except ValueError:
            continue
    if not gpus:
        return {"disponible": False, "detalle": "salida de nvidia-smi no reconocida"}
    return {"disponible": True, "gpus": gpus}
