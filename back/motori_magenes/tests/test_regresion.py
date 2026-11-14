"""Regresión de fallos de infraestructura y de contratos (BACK-25).

Disco lleno, tiempo agotado del OCR, investigación lenta o caída, migración
de datos antiguos y el contrato v1 congelado (rutas, tipos y cabeceras).
"""

import errno
import sqlite3
import time

import cv2
import numpy as np
import pytest

from app.datos.bd import BaseDatos, MIGRACIONES
from app.main import app
from app.services import analisis, investigacion
from app.services.ocr import ErrorOCR
from tests.conftest import imagen_pil

# Versión de la última migración (no fija: cada migración nueva la sube).
ULTIMA_MIGRACION = max(int(a.name[:4]) for a in __import__('app.datos.bd', fromlist=['x']).MIGRACIONES.glob('*.sql'))


def esperar(c, tid, limite=30):
    fin = time.time() + limite
    while time.time() < fin:
        t = c.get(f"/api/v2/trabajos/{tid}").json()["trabajo"]
        if t["estado"] not in ("pendiente", "procesando"):
            return t
        time.sleep(0.05)
    raise AssertionError("no terminó")


def subir(c, n=1):
    files = [("paginas", (f"p{i}.png", imagen_pil("PNG", (200, 150)), "image/png")) for i in range(n)]
    return c.post("/api/v2/apuntes", files=files, data={"tipos": "cuaderno", "titulo": "t"})


def disco_lleno(*_a, **_k):
    raise OSError(errno.ENOSPC, "No space left on device")


# ------------------------------------------------------------------ disco lleno

def test_disco_lleno_al_subir_responde_507_sin_huerfanos(nuevo_cliente, datos_tmp, monkeypatch):
    c = nuevo_cliente()
    c.registrar()
    monkeypatch.setattr("app.datos.almacen.os.fsync", disco_lleno)
    r = subir(c, 2)
    assert r.status_code == 507 and r.json()["error"]["codigo"] == "ALMACENAMIENTO_LLENO"
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM apuntes")["n"] == 0
    assert not [p for p in datos_tmp.data_dir.rglob("*") if p.is_file() and p.suffix != ".sqlite3"
                and "sqlite3" not in p.name]


def test_disco_lleno_durante_el_analisis_falla_el_trabajo(nuevo_cliente, datos_tmp, monkeypatch):
    c = nuevo_cliente()
    c.registrar()

    def pagina_sin_espacio(trabajo, pagina, idiomas):
        from app.core.errores import ApiError
        raise ApiError(507, "ALMACENAMIENTO_LLENO", "Sin espacio")

    monkeypatch.setattr(analisis, "analizar_pagina", pagina_sin_espacio)
    r = subir(c)
    t = esperar(c, r.json()["trabajo"]["id"])
    assert t["estado"] == "fallido" and t["error"]["codigo"] == "ALMACENAMIENTO_LLENO"
    assert c.get(f"/api/v2/apuntes/{r.json()['apunte']['id']}").json()["apunte"]["estado"] == "fallido"


def test_disco_lleno_al_guardar_el_pdf(nuevo_cliente, datos_tmp, monkeypatch):
    from tests.test_pdf import png
    from app.datos.apuntes import RepositorioApuntes
    from app.services.documento import Bloque
    from app.services.entrada import PaginaRecibida
    from app.services.validacion import ImagenRecibida
    c = nuevo_cliente()
    u = c.registrar()
    repo = RepositorioApuntes(datos_tmp.bd, datos_tmp.almacen)
    a, _ = repo.crear(u["id"], "t", [PaginaRecibida(1, "cuaderno", ImagenRecibida("a", "png", png(), np.zeros((2, 2, 3), np.uint8)))])
    doc = repo.documento(u["id"], a["id"])
    doc.bloques.append(Bloque(id="b", orden=0, tipo="texto", origen="usuario", texto="Hola"))
    repo.nueva_version(u["id"], a["id"], doc, "edicion", estado="listo")
    monkeypatch.setattr("app.datos.almacen.os.fsync", disco_lleno)
    r = c.post(f"/api/v2/apuntes/{a['id']}/exportaciones", json={})
    t = esperar(c, r.json()["trabajo"]["id"])
    assert t["estado"] == "fallido" and t["error"]["codigo"] == "ALMACENAMIENTO_LLENO"
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM archivos WHERE tipo = 'pdf'")["n"] == 0


# ------------------------------------------------------------------ tiempos agotados

def test_ocr_agotado_en_una_pagina_da_parcial(nuevo_cliente, monkeypatch):
    def lenta(trabajo, pagina, idiomas):
        if pagina.orden == 2:
            raise ErrorOCR("OCR_TIEMPO_AGOTADO", "El reconocimiento tardó demasiado en esta página.")
        return {"error": None}, []

    monkeypatch.setattr(analisis, "analizar_pagina", lenta)
    c = nuevo_cliente()
    c.registrar()
    r = subir(c, 2)
    t = esperar(c, r.json()["trabajo"]["id"])
    assert t["estado"] == "parcial" and "página 2" in t["error"]["mensaje"]


def test_investigacion_lenta_no_cuelga_ni_toca_el_apunte(nuevo_cliente, datos_tmp):
    from tests.test_investigacion import TEXTO  # noqa: F401
    from app.services.investigacion import ProveedorWikipedia

    def agota(peticion, timeout=None):
        assert timeout == pytest.approx(0.2)  # se respeta el límite configurado
        raise TimeoutError("timed out")

    investigacion.usar_proveedor(ProveedorWikipedia(timeout=0.2, abrir=agota))
    try:
        c = nuevo_cliente()
        c.registrar()
        c.patch("/api/v2/perfil", json={"preferencias": {"investigacion_permitida": True}})
        from app.datos.apuntes import RepositorioApuntes
        r = subir(c)
        aid = r.json()["apunte"]["id"]
        RepositorioApuntes(datos_tmp.bd, datos_tmp.almacen).cambiar_estado(aid, "listo")
        antes = c.get(f"/api/v2/apuntes/{aid}").json()["apunte"]["version"]
        inicio = time.monotonic()
        r = c.post(f"/api/v2/apuntes/{aid}/investigacion", json={"consentimiento": True, "conceptos": ["Derivada"]})
        t = esperar(c, r.json()["trabajo"]["id"])
        assert t["estado"] == "fallido" and t["error"]["codigo"] == "INVESTIGACION_NO_DISPONIBLE"
        assert time.monotonic() - inicio < 10
        assert c.get(f"/api/v2/apuntes/{aid}").json()["apunte"]["version"] == antes
    finally:
        investigacion.usar_proveedor(None)


# ------------------------------------------------------------------ migraciones

def test_migracion_0004_conserva_exportaciones_antiguas(tmp_path):
    previas = tmp_path / "previas"
    previas.mkdir()
    for archivo in sorted(MIGRACIONES.glob("000[123]_*.sql")):
        (previas / archivo.name).write_text(archivo.read_text(encoding="utf-8"), encoding="utf-8")
    bd = BaseDatos(tmp_path / "bd.sqlite3")
    bd.migrar(previas)
    bd.ejecutar("INSERT INTO usuarios VALUES ('u', 'u@x.com', 'U', 'h', '{}', 'f', 'f')")
    bd.ejecutar("INSERT INTO apuntes (id, usuario_id, titulo, estado, tipo_fuente, version_actual, creado, actualizado)"
                " VALUES ('a', 'u', 't', 'listo', 'cuaderno', 1, 'f', 'f')")
    bd.ejecutar("INSERT INTO exportaciones VALUES ('e', 'a', 1, 'completado', NULL, 'f')")
    assert bd.migrar()[0] == "0004_exportaciones.sql"   # y las posteriores
    fila = bd.uno("SELECT * FROM exportaciones WHERE id = 'e'")
    assert fila["usuario_id"] == "u" and fila["clave"] and fila["estado"] == "completado"
    with pytest.raises(sqlite3.IntegrityError):  # unicidad por (apunte, versión, opciones)
        bd.ejecutar("INSERT INTO exportaciones (id, apunte_id, usuario_id, version, clave, estado, creado, actualizado)"
                    " VALUES ('e2', 'a', 'u', 1, ?, 'pendiente', 'f', 'f')", (fila["clave"],))
    assert bd.version_esquema() == ULTIMA_MIGRACION
    bd.cerrar()


# ------------------------------------------------------------------ contrato v1 congelado

RUTAS_V1 = {("/", "get"), ("/salud", "get"), ("/analisis", "post"), ("/imagen-memoria", "post")}


def test_contrato_v1_congelado(client):
    rutas = {(r, m) for r, ms in app.openapi()["paths"].items() for m in ms if not r.startswith("/api/v2/")}
    assert rutas == RUTAS_V1
    salud = client.get("/salud").json()
    assert {"estado", "formatos", "max_mb", "max_megapixeles"} <= set(salud)
    r = client.post("/analisis", files={"file": ("a.png", imagen_pil("PNG"), "image/png")})
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    for cabecera in ("x-apuntia-archivo", "x-apuntia-perspectiva", "x-apuntia-dimensiones", "x-apuntia-tiempo-ms"):
        assert cabecera in r.headers
    assert cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR) is not None
    error = client.post("/analisis", files={"file": ("a.png", b"no", "image/png")}).json()
    assert set(error) == {"error"} and set(error["error"]) == {"codigo", "mensaje"}
    assert client.post("/analisis").json()["error"]["codigo"] == "ARCHIVO_AUSENTE"


def test_v1_no_requiere_sesion_ni_csrf(client):
    r = client.post("/analisis", files={"file": ("a.png", imagen_pil("PNG"), "image/png")},
                    headers={"Origin": "https://otro.example"})
    assert r.status_code == 200
