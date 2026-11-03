import io
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app.main import app  # noqa: E402
from herramientas.muestras import foto_inclinada  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app, raise_server_exceptions=False)


def codificar(img: np.ndarray, ext: str = ".png") -> bytes:
    ok, buf = cv2.imencode(ext, img)
    assert ok
    return buf.tobytes()


def imagen_pil(fmt: str, tam=(64, 48)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", tam, (200, 30, 30)).save(buf, fmt)
    return buf.getvalue()


@pytest.fixture(scope="session")
def pizarron_inclinado():
    foto, esquinas = foto_inclinada()
    return foto, esquinas


@pytest.fixture
def subir(client):
    def _subir(datos: bytes, nombre="pizarron.png", tipo="image/png", query=""):
        return client.post(f"/analisis{query}", files={"file": (nombre, datos, tipo)})
    return _subir


def decodificar_respuesta(resp) -> np.ndarray:
    img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_UNCHANGED)
    assert img is not None, "la respuesta no es una imagen válida"
    return img
