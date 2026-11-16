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
from herramientas.claves_prueba import clave_de_prueba  # noqa: E402


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


# ---------------------------------------------------------------- API v2 (BACK-22 en adelante)

@pytest.fixture
def datos_tmp(tmp_path):
    """Carpeta de datos temporal y limpia para cada prueba."""
    from app.core import contexto
    ctx = contexto.reiniciar(tmp_path / "datos")
    yield ctx
    # Primero los hilos de trabajos: cerrar la BD con una transacción en curso en otro hilo
    # puede tumbar el proceso (Segmentation fault en sqlite3, visto en CI).
    ctx.trabajos.detener(esperar=True)
    ctx.bd.cerrar()


class ClienteV2:
    """TestClient con cookie de sesión propia y la cabecera CSRF de la última sesión."""

    def __init__(self):
        self.http = TestClient(app, raise_server_exceptions=False)
        self.csrf = ""

    def _cab(self, extra=None):
        cab = {"X-CSRF-Token": self.csrf} if self.csrf else {}
        cab.update(extra or {})
        return cab

    def get(self, url, **kw):
        return self.http.get(url, headers=self._cab(kw.pop("headers", None)), **kw)

    def post(self, url, **kw):
        return self.http.post(url, headers=self._cab(kw.pop("headers", None)), **kw)

    def put(self, url, **kw):
        return self.http.put(url, headers=self._cab(kw.pop("headers", None)), **kw)

    def patch(self, url, **kw):
        return self.http.patch(url, headers=self._cab(kw.pop("headers", None)), **kw)

    def delete(self, url, **kw):
        return self.http.request("DELETE", url, headers=self._cab(kw.pop("headers", None)), **kw)

    def registrar(self, email="ana@example.com", nombre="Ana", password=clave_de_prueba("c1")):
        r = self.http.post("/api/v2/auth/registro", json={"email": email, "nombre": nombre, "password": password})
        assert r.status_code == 201, r.text
        self.csrf = r.json()["csrf"]
        return r.json()["usuario"]


@pytest.fixture
def nuevo_cliente(datos_tmp):
    return ClienteV2
