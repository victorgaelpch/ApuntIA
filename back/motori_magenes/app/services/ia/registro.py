"""Registro de motores, perfiles de reconocimiento y diagnóstico del equipo (FULL-30, fase 2).

Perfiles (RECONOCIMIENTO_PERFIL):
  - rapido:      Tesseract con el flujo clásico. Solo CPU.
  - equilibrado: Tesseract con el reconocimiento adaptativo de BACK-28 (el flujo actual por
                 defecto). Los PR siguientes añadirán aquí el OCR documental y el matemático
                 cuando estén evaluados.
  - avanzado:    lo anterior + un VLM local (Ollama) como apoyo interpretativo.
  - automatico:  el más completo que el equipo pueda ejecutar ahora.

Estado en este PR: el registro, los perfiles y el diagnóstico existen y se consultan por la
API (`/api/v2/reconocimiento/...`), pero el análisis de apuntes TODAVÍA NO los usa: sigue el
flujo de BACK-28 en todos los casos. Conectarlo es la fase siguiente (docs/arquitectura-ia.md §6).
"""

import os
import platform
import shutil
import subprocess
import threading
from dataclasses import dataclass, field

from app.core.config import settings
from app.services.ia.motores import ErrorMotor, MotorReconocimiento, MotorTesseractAdaptador

PERFILES = ("rapido", "equilibrado", "avanzado", "automatico")

# Memoria aproximada para ejecutar cada VLM en CPU: tamaño del archivo del modelo en Ollama
# (ollama.com/library/qwen3-vl) más un margen para el contexto y la imagen. ESTIMACIÓN, no medida:
# en este proyecto aún no se ha medido (docs/arquitectura-ia.md §5).
MEMORIA_ESTIMADA_GB = {"qwen3-vl:2b": 4.0, "qwen3-vl:4b": 6.0, "qwen3-vl:8b": 10.0}


# ------------------------------------------------------------------ hardware

def _memoria_gb() -> tuple[float | None, float | None]:
    """(total, disponible) en GB, sin dependencias nuevas. None si no se puede saber."""
    try:
        if platform.system() == "Windows":
            import ctypes

            class Estado(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
            e = Estado()
            e.dwLength = ctypes.sizeof(Estado)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(e))
            return e.ullTotalPhys / 2**30, e.ullAvailPhys / 2**30
        valores = {}
        with open("/proc/meminfo", encoding="ascii") as f:
            for linea in f:
                clave, _, resto = linea.partition(":")
                valores[clave] = int(resto.split()[0]) / 2**20   # kB → GB
        return valores.get("MemTotal"), valores.get("MemAvailable")
    except Exception:  # noqa: BLE001  (macOS u otro: sin dato, no es un error)
        return None, None


def _gpus() -> list[dict]:
    """GPU NVIDIA visibles (nvidia-smi). Ollama también usa AMD/Apple; aquí solo se informa."""
    if not shutil.which("nvidia-smi"):
        return []
    try:
        salida = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.free",
                                 "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return []
    gpus = []
    for linea in salida.stdout.strip().splitlines():
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) == 3 and partes[1].isdigit():
            gpus.append({"nombre": partes[0], "vram_gb": round(int(partes[1]) / 1024, 1),
                         "vram_libre_gb": round(int(partes[2]) / 1024, 1) if partes[2].isdigit() else None})
    return gpus


def hardware() -> dict:
    total, disponible = _memoria_gb()
    return {"sistema": platform.system(), "cpus": os.cpu_count(),
            "ram_gb": round(total, 1) if total else None,
            "ram_disponible_gb": round(disponible, 1) if disponible else None,
            "gpus": _gpus()}


def memoria_suficiente(modelo: str, equipo: dict) -> tuple[bool | None, str]:
    """¿Cabe el modelo? None si no se sabe (modelo desconocido o sin dato de RAM)."""
    necesaria = MEMORIA_ESTIMADA_GB.get(modelo)
    libre = equipo.get("ram_disponible_gb")
    vram = max((g.get("vram_libre_gb") or 0 for g in equipo.get("gpus", [])), default=0)
    if necesaria is None or libre is None:
        return None, "sin estimación de memoria para este modelo o este equipo"
    if max(libre, vram) >= necesaria:
        return True, f"necesita ~{necesaria:g} GB (estimado); hay {max(libre, vram):g} GB libres"
    return False, (f"necesita ~{necesaria:g} GB (estimado) y hay {max(libre, vram):g} GB libres: "
                   "usa un modelo más pequeño o cierra programas")


# ------------------------------------------------------------------ registro

@dataclass
class Registro:
    motores: dict[str, MotorReconocimiento] = field(default_factory=dict)

    def registrar(self, motor: MotorReconocimiento) -> None:
        self.motores[motor.nombre] = motor

    def disponibles(self) -> list[MotorReconocimiento]:
        return [m for m in self.motores.values() if _seguro(m.disponible)]

    def para(self, tarea: str, perfil: str) -> list[MotorReconocimiento]:
        """Motores disponibles para una tarea, en orden de preferencia. El VLM solo entra en «avanzado»
        y nunca es el único: Tesseract queda siempre como respaldo si sabe hacer la tarea."""
        orden = ["tesseract"] if perfil in ("rapido", "equilibrado") else ["tesseract", "ollama_vlm"]
        return [self.motores[n] for n in orden
                if n in self.motores and tarea in self.motores[n].capacidades() and _seguro(self.motores[n].disponible)]

    def describir(self) -> list[dict]:
        salida = []
        for m in self.motores.values():
            info = m.info_modelo().a_dict()
            info.update({"disponible": _seguro(m.disponible), "capacidades": sorted(m.capacidades())})
            salida.append(info)
        return salida


def _seguro(funcion) -> bool:
    try:
        return bool(funcion())
    except ErrorMotor:
        return False


def perfiles(registro: Registro, equipo: dict | None = None) -> dict:
    """Cada perfil: si se puede usar ahora, con qué motores y por qué no."""
    equipo = equipo or hardware()
    tesseract = "tesseract" in registro.motores and _seguro(registro.motores["tesseract"].disponible)
    vlm = registro.motores.get("ollama_vlm")
    vlm_ok = bool(vlm and _seguro(vlm.disponible))
    cabe, motivo_memoria = memoria_suficiente(vlm.info_modelo().modelo if vlm else "", equipo)
    falta_tesseract = "Tesseract no está disponible"
    datos = {
        "rapido": {"disponible": tesseract, "motores": ["tesseract"], "flujo": "clasico",
                   "detalle": "" if tesseract else falta_tesseract},
        "equilibrado": {"disponible": tesseract, "motores": ["tesseract"], "flujo": "adaptativo",
                        "detalle": "" if tesseract else falta_tesseract},
        "avanzado": {"disponible": tesseract and vlm_ok and cabe is not False, "motores": ["tesseract", "ollama_vlm"],
                     "flujo": "adaptativo+vlm",
                     "detalle": ("" if tesseract and vlm_ok and cabe is not False else
                                 falta_tesseract if not tesseract else
                                 (vlm.info_modelo().detalle if vlm else "sin modelo visual") if not vlm_ok else
                                 motivo_memoria)},
    }
    elegido = next((p for p in ("avanzado", "equilibrado", "rapido") if datos[p]["disponible"]), None)
    datos["automatico"] = {"disponible": elegido is not None, "elige": elegido,
                           "motores": datos[elegido]["motores"] if elegido else [], "flujo": datos[elegido]["flujo"]
                           if elegido else None, "detalle": "" if elegido else "ningún motor de OCR disponible"}
    configurado = settings.reconocimiento_perfil if settings.reconocimiento_perfil in PERFILES else "automatico"
    return {"configurado": configurado, "aplicado_en_analisis": False, "perfiles": datos, "memoria_vlm": motivo_memoria}


_registro: Registro | None = None
_bloqueo = threading.Lock()


def registro() -> Registro:
    """Registro del proceso: se crea una vez; los motores comprueban su disponibilidad bajo demanda
    (el VLM con caché de 30 s), sin cargar ningún modelo."""
    global _registro
    with _bloqueo:
        if _registro is None:
            from app.services.ia.ollama import MotorOllamaVLM
            r = Registro()
            r.registrar(MotorTesseractAdaptador())
            r.registrar(MotorOllamaVLM())
            _registro = r
        return _registro


def reiniciar() -> None:
    """Para las pruebas y tras cambiar la configuración."""
    global _registro
    with _bloqueo:
        _registro = None
