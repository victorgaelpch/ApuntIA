"""Pruebas de los endpoints según el contrato de fullstack/docs/api.md (BACK-08)."""

from urllib.parse import unquote

import numpy as np
import pytest

from app.core.config import settings
from tests.conftest import codificar, decodificar_respuesta, imagen_pil


def assert_error(resp, status, codigo):
    assert resp.status_code == status, resp.text
    assert resp.headers["content-type"].startswith("application/json")
    cuerpo = resp.json()
    assert set(cuerpo) == {"error"}
    assert cuerpo["error"]["codigo"] == codigo
    assert isinstance(cuerpo["error"]["mensaje"], str) and cuerpo["error"]["mensaje"]
    return cuerpo


# ---------------------------------------------------------------- rutas generales

def test_raiz_hola_mundo(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Hola Mundo"}


def test_salud_informa_limites(client):
    r = client.get("/salud")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["formatos"] == ["image/jpeg", "image/png", "image/webp"]
    assert cuerpo["max_mb"] == settings.max_upload_mb
    assert cuerpo["max_megapixeles"] == settings.max_megapixeles


def test_imagen_memoria_devuelve_png(client):
    r = client.post("/imagen-memoria")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_documentacion_disponible(client):
    assert client.get("/docs").status_code == 200
    esquema = client.get("/openapi.json").json()
    assert "/analisis" in esquema["paths"]


# ---------------------------------------------------------------- casos exitosos

@pytest.mark.parametrize("fmt,tipo,nombre", [
    ("PNG", "image/png", "a.png"),
    ("JPEG", "image/jpeg", "a.jpg"),
    ("WEBP", "image/webp", "a.webp"),
])
def test_formatos_permitidos(subir, fmt, tipo, nombre):
    r = subir(imagen_pil(fmt), nombre=nombre, tipo=tipo)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    assert decodificar_respuesta(r).shape[:2] == (48, 64)


def test_cabeceras_de_metadatos(subir):
    r = subir(imagen_pil("PNG"), nombre="pizarrón día 1.png")
    assert r.status_code == 200
    assert unquote(r.headers["x-apuntia-archivo"]) == "pizarrón día 1.png"
    assert r.headers["x-apuntia-dimensiones"] == "64x48"
    assert r.headers["x-apuntia-perspectiva"] in {"corregida", "no_detectada", "desactivada"}
    assert int(r.headers["x-apuntia-tiempo-ms"]) >= 0
    assert "pizarr%C3%B3n%20d%C3%ADa%201_apuntia.png" in r.headers["content-disposition"]


def test_procesamiento_completo_corrige_perspectiva(subir, pizarron_inclinado):
    foto, _ = pizarron_inclinado
    r = subir(codificar(foto, ".jpg"), nombre="inclinada.jpg", tipo="image/jpeg")
    assert r.status_code == 200
    assert r.headers["x-apuntia-perspectiva"] == "corregida"
    salida = decodificar_respuesta(r)
    ancho, alto = map(int, r.headers["x-apuntia-dimensiones"].split("x"))
    assert salida.shape[:2] == (alto, ancho)
    # El pizarrón sintético es 3:2; la rectificación debe conservar la proporción.
    assert abs(ancho / alto - 1.5) < 0.08


def test_parametros_desactivan_etapas(subir, pizarron_inclinado):
    foto, _ = pizarron_inclinado
    r = subir(codificar(foto), query="?perspectiva=false&ruido=ninguno&mejorar=false")
    assert r.headers["x-apuntia-perspectiva"] == "desactivada"
    assert np.array_equal(decodificar_respuesta(r), foto)


def test_parametro_grises(subir):
    r = subir(imagen_pil("PNG"), query="?grises=true")
    assert decodificar_respuesta(r).ndim == 2


@pytest.mark.parametrize("metodo", ["ninguno", "mediana", "gaussiano", "bilateral", "combinado"])
def test_todos_los_filtros_de_ruido(subir, metodo):
    assert subir(imagen_pil("PNG"), query=f"?ruido={metodo}").status_code == 200


def test_imagen_grande_se_redimensiona(subir):
    grande = np.full((3000, 4000, 3), 230, np.uint8)
    r = subir(codificar(grande, ".jpg"), tipo="image/jpeg", query="?perspectiva=false")
    assert r.status_code == 200
    ancho, alto = map(int, r.headers["x-apuntia-dimensiones"].split("x"))
    assert max(ancho, alto) == settings.max_lado_procesamiento


# ---------------------------------------------------------------- errores del cliente

def test_sin_archivo(client):
    assert_error(client.post("/analisis"), 400, "ARCHIVO_AUSENTE")


def test_campo_con_otro_nombre(client):
    r = client.post("/analisis", files={"imagen": ("a.png", imagen_pil("PNG"), "image/png")})
    assert_error(r, 400, "ARCHIVO_AUSENTE")


def test_archivo_vacio(subir):
    assert_error(subir(b""), 400, "ARCHIVO_VACIO")


@pytest.mark.parametrize("datos", [b"%PDF-1.7 ...", b"GIF89a....", b"hola mundo", b"\x00" * 100])
def test_tipo_no_permitido_aunque_diga_png(subir, datos):
    assert_error(subir(datos, nombre="falso.png", tipo="image/png"), 415, "TIPO_NO_PERMITIDO")


def test_imagen_corrupta(subir):
    assert_error(subir(imagen_pil("PNG")[:40]), 400, "IMAGEN_CORRUPTA")


def test_archivo_demasiado_grande(subir):
    datos = b"\x89PNG\r\n\x1a\n" + b"0" * int(settings.max_upload_mb * 1024 * 1024)
    cuerpo = assert_error(subir(datos), 413, "ARCHIVO_DEMASIADO_GRANDE")
    assert "10 MB" in cuerpo["error"]["mensaje"]


def test_demasiados_megapixeles(subir, monkeypatch):
    monkeypatch.setattr(settings, "max_megapixeles", 0.001)
    assert_error(subir(imagen_pil("PNG")), 413, "IMAGEN_DEMASIADO_GRANDE")


@pytest.mark.parametrize("query", ["?ruido=xyz", "?perspectiva=quizas", "?grises=2"])
def test_parametro_invalido(subir, query):
    assert_error(subir(imagen_pil("PNG"), query=query), 422, "PARAMETRO_INVALIDO")


def test_ruta_inexistente(client):
    assert_error(client.get("/no-existe"), 404, "RUTA_NO_ENCONTRADA")


def test_metodo_no_permitido(client):
    assert_error(client.get("/analisis"), 405, "METODO_NO_PERMITIDO")


def test_nombre_malicioso_no_se_refleja(subir):
    r = subir(imagen_pil("PNG"), nombre='../../etc/pass"wd\r\n.png')
    assert r.status_code == 200
    nombre = unquote(r.headers["x-apuntia-archivo"])
    # El cliente (como los navegadores) ya escapa " y CRLF en el multipart;
    # lo importante es que no lleguen rutas, comillas ni saltos de línea.
    assert nombre.startswith("pass") and nombre.endswith(".png")
    assert not set('/\\"\r\n') & set(nombre)
    assert "\n" not in r.headers["content-disposition"]


# ---------------------------------------------------------------- errores del servidor

def test_error_de_procesamiento_sin_trazas(subir, monkeypatch):
    import cv2
    from app.services import procesamiento

    def falla(*_a, **_k):
        raise cv2.error("detalle interno /ruta/secreta")

    monkeypatch.setattr(procesamiento, "eliminar_ruido", falla)
    r = subir(imagen_pil("PNG"))
    cuerpo = assert_error(r, 500, "ERROR_PROCESAMIENTO")
    assert "secreta" not in r.text and "Traceback" not in r.text
    assert r.headers["x-apuntia-error-id"]
    assert "Inténtalo" in cuerpo["error"]["mensaje"]


def test_error_inesperado_sin_trazas(subir, monkeypatch):
    from app.routers import imagenes

    def falla(*_a, **_k):
        raise RuntimeError("contraseña=1234")

    monkeypatch.setattr(imagenes, "codificar_png", falla)
    r = subir(imagen_pil("PNG"))
    assert_error(r, 500, "ERROR_INTERNO")
    assert "1234" not in r.text


# ---------------------------------------------------------------- CORS (FULL-04)

def test_cors_expone_cabeceras_del_contrato(subir, client):
    r = client.post("/analisis", files={"file": ("a.png", imagen_pil("PNG"), "image/png")},
                    headers={"Origin": "http://localhost:5500"})
    assert r.headers["access-control-allow-origin"] == "*"
    expuestas = {h.strip().lower() for h in r.headers["access-control-expose-headers"].split(",")}
    assert {"content-disposition", "x-apuntia-perspectiva", "x-apuntia-dimensiones",
            "x-apuntia-tiempo-ms", "x-apuntia-archivo", "x-apuntia-error-id"} <= expuestas
    assert "access-control-allow-credentials" not in r.headers


def test_cors_preflight(client):
    r = client.options("/analisis", headers={"Origin": "http://192.168.1.20:5500",
                                             "Access-Control-Request-Method": "POST"})
    assert r.status_code == 200
    assert "POST" in r.headers["access-control-allow-methods"]


# ---------------------------------------------------------------- defecto D1 (FULL-08)

@pytest.mark.parametrize("modulo,funcion,exc", [
    ("app.routers.imagenes", "codificar_png", RuntimeError("inesperado")),
    ("app.services.procesamiento", "eliminar_ruido", __import__("cv2").error("cv2")),
])
def test_errores_500_llevan_cabeceras_cors(client, monkeypatch, modulo, funcion, exc):
    import importlib

    def falla(*_a, **_k):
        raise exc

    monkeypatch.setattr(importlib.import_module(modulo), funcion, falla)
    r = client.post("/analisis", files={"file": ("a.png", imagen_pil("PNG"), "image/png")},
                    headers={"Origin": "http://localhost:5500"})
    assert r.status_code == 500
    assert r.headers["access-control-allow-origin"] == "*"
    assert "x-apuntia-error-id" in r.headers["access-control-expose-headers"].lower()
    assert r.json()["error"]["codigo"] in {"ERROR_INTERNO", "ERROR_PROCESAMIENTO"}
