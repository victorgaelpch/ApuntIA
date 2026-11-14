"""Dobles de prueba: un Ollama falso (sin red ni GPU) y utilidades de imágenes."""

import json

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from ia_servidor.app import crear_app
from ia_servidor.config import Configuracion
from ia_servidor.ollama import ClienteOllama
from ia_servidor.servicio import Servicio

RESPUESTA_OK = {"ilegible": False, "texto": "Derivada de x^2", "latex": "\\frac{d}{dx}x^2 = 2x",
                "descripcion": None, "dudas": ["la última letra podría ser «z»"]}


class OllamaFalso:
    """Transporte que imita la API de Ollama. `chat` es una lista de respuestas por llamada:
    dict (contenido JSON), str (contenido literal), (estado, texto) o una excepción."""

    def __init__(self, chat=None, modelos=("qwen3-vl:8b",), version="0.12.10", capacidades=("completion", "vision")):
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
    def _armar(ollama=None, **config):
        ollama = ollama or OllamaFalso()
        cfg = Configuracion(**config)
        cfg.validar()
        servicio = Servicio(cfg, ClienteOllama(cfg.ollama_url, ollama), leer_gpu=gpu_falsa, carpeta_modelos=tmp_path)
        return TestClient(crear_app(cfg, servicio)), ollama, servicio
    return _armar
