"""Dobles de prueba: un Ollama falso (sin red ni GPU) y utilidades de imágenes."""

import json

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from ia_servidor.app import crear_app
from ia_servidor.config import Configuracion
from ia_servidor.dispositivos import Registro
from ia_servidor.ollama import ClienteOllama
from ia_servidor.servicio import Servicio

# Respuesta en texto plano, como la pide el servidor desde la versión 1.1 del pipeline.
RESPUESTA_OK = "\\frac{d}{dx}x^2 = 2x\nE = m[?]^2"


class OllamaFalso:
    """Transporte que imita la API de Ollama. `chat` es una lista de respuestas por llamada:
    str (contenido literal), (estado, texto) o una excepción."""

    def __init__(self, chat=None, modelos=("qwen3-vl:8b-instruct",), version="0.12.10", capacidades=("completion", "vision")):
        self.chat = list(chat if chat is not None else [RESPUESTA_OK])
        self.modelos = list(modelos)
        self.version = version
        self.capacidades = list(capacidades)
        self.peticiones = []

    def __call__(self, metodo, url, cuerpo, timeout):
        ruta = url.split("11434", 1)[1]
        self.peticiones.append((metodo, ruta, cuerpo))
        if ruta == "/api/version":
            return 200, json.dumps({"version": self.version}).encode()
        if ruta == "/api/tags":
            return 200, json.dumps({"models": [{"name": m, "size": 6_200_000_000,
                                                "details": {"quantization_level": "Q4_K_M"}} for m in self.modelos]}).encode()
        if ruta == "/api/show":
            if cuerpo["model"] not in self.modelos:
                return 404, b'{"error":"model not found"}'
            return 200, json.dumps({"capabilities": self.capacidades}).encode()
        if ruta == "/api/ps":
            return 200, b'{"models": []}'
        if ruta == "/api/chat":
            r = self.chat.pop(0) if self.chat else RESPUESTA_OK
            if isinstance(r, Exception):
                raise r
            if isinstance(r, tuple):
                return r[0], r[1].encode()
            contenido = r if isinstance(r, str) else json.dumps(r)
            return 200, json.dumps({"message": {"role": "assistant", "content": contenido}, "done": True,
                                    "done_reason": "stop", "eval_count": 42, "total_duration": 3_500_000_000,
                                    "load_duration": 1_000_000_000}).encode()
        return 404, b"{}"

    def chats(self):
        return [c for m, r, c in self.peticiones if r == "/api/chat"]


def gpu_falsa():
    return {"disponible": True, "gpus": [{"nombre": "NVIDIA GeForce RTX 3060", "vram_total_mb": 12288,
                                          "vram_usada_mb": 500, "vram_libre_mb": 11788, "controlador": "560.94"}]}


def png(ancho=640, alto=480) -> bytes:
    img = np.full((alto, ancho, 3), 255, np.uint8)
    cv2.putText(img, "x^2 + y = 3", (40, alto // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
    return cv2.imencode(".png", img)[1].tobytes()


@pytest.fixture
def armar(tmp_path):
    def _armar(ollama=None, autenticado=True, **config):
        ollama = ollama or OllamaFalso()
        cfg = Configuracion(**config)
        cfg.validar()
        servicio = Servicio(cfg, ClienteOllama(cfg.ollama_url, ollama), leer_gpu=gpu_falsa, carpeta_modelos=tmp_path)
        registro = Registro(tmp_path / "datos")
        cliente = TestClient(crear_app(cfg, servicio, registro))
        cliente.registro = registro
        if autenticado:  # vinculación real: solicitar → aprobar en «consola» → recibir el token
            cliente.headers["Authorization"] = "Bearer " + vincular(cliente, registro)
        return cliente, ollama, servicio
    return _armar


def vincular(cliente, registro, dispositivo_id="laptop-profesor-0001", nombre="Laptop del profesor") -> str:
    s = cliente.post("/api/v1/vinculacion/solicitudes", json={"dispositivo_id": dispositivo_id, "nombre": nombre}).json()
    registro.resolver(s["codigo"], aprobar=True)
    r = cliente.post(f"/api/v1/vinculacion/solicitudes/{s['solicitud_id']}/estado", json={"secreto": s["secreto"]}).json()
    return r["token"]
