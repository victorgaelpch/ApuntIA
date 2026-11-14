"""Endurecimiento de la API v2 (BACK-24): IDOR, traversal, CSRF, CORS, límites y fugas.

`RUTAS_CON_RECURSO` debe cubrir TODAS las rutas v2 con identificadores: la
prueba `test_todas_las_rutas_con_id_estan_cubiertas` falla si se añade una ruta
nueva sin su prueba de acceso cruzado.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.core import endurecimiento
from app.core.config import settings
from app.datos.bd import ahora
from app.main import app
from tests.conftest import imagen_pil
from tests.test_historial import con_apuntes  # noqa: F401 (fixture)
from herramientas.claves_prueba import clave_de_prueba

RUTAS_CON_RECURSO = [
    ("GET", "/api/v2/apuntes/{apunte_id}"),
    ("GET", "/api/v2/apuntes/{apunte_id}/archivos/{archivo_id}"),
    ("PUT", "/api/v2/apuntes/{apunte_id}/documento"),
    ("GET", "/api/v2/apuntes/{apunte_id}/versiones"),
    ("GET", "/api/v2/apuntes/{apunte_id}/versiones/{numero}"),
    ("POST", "/api/v2/apuntes/{apunte_id}/versiones/{numero}/restaurar"),
    ("DELETE", "/api/v2/apuntes/{apunte_id}"),
    ("GET", "/api/v2/apuntes/{apunte_id}/estructura"),
    ("GET", "/api/v2/apuntes/{apunte_id}/conceptos"),
    ("POST", "/api/v2/apuntes/{apunte_id}/investigacion"),
    ("PATCH", "/api/v2/apuntes/{apunte_id}/ampliaciones/{ampliacion_id}"),
    ("POST", "/api/v2/apuntes/{apunte_id}/exportaciones"),
    ("GET", "/api/v2/apuntes/{apunte_id}/exportaciones"),
    ("GET", "/api/v2/exportaciones/{exportacion_id}"),
    ("GET", "/api/v2/exportaciones/{exportacion_id}/pdf"),
    ("GET", "/api/v2/trabajos/{trabajo_id}"),
    ("DELETE", "/api/v2/trabajos/{trabajo_id}"),
    ("POST", "/api/v2/trabajos/{trabajo_id}/reintentar"),
]


def rutas_v2_con_id():
    rutas = set()
    for ruta, metodos in app.openapi()["paths"].items():
        if ruta.startswith("/api/v2/") and "{" in ruta:
            rutas |= {(m.upper(), ruta) for m in metodos}
    return rutas


def test_todas_las_rutas_con_id_estan_cubiertas():
    assert rutas_v2_con_id() == set(RUTAS_CON_RECURSO)


@pytest.fixture
def victima_y_atacante(con_apuntes, nuevo_cliente, datos_tmp):
    duena, ids, repo, usuario = con_apuntes
    apunte = ids[0]
    archivo = datos_tmp.bd.uno("SELECT id FROM archivos WHERE apunte_id = ?", (apunte,))["id"]
    trabajo = "t" * 32
    datos_tmp.bd.ejecutar("INSERT INTO trabajos (id, usuario_id, apunte_id, tipo, estado, parametros, creado, "
                          "actualizado) VALUES (?, ?, ?, 'analisis', 'fallido', '{}', ?, ?)",
                          (trabajo, usuario["id"], apunte, ahora(), ahora()))
    from app.services.documento import Ampliacion, Fuente
    doc = repo.documento(usuario["id"], apunte)
    doc.ampliaciones.append(Ampliacion(id="a1", concepto="c", texto="t", fuente=Fuente(
        titulo="t", url="https://es.wikipedia.org/wiki/C", proveedor="wikipedia", consultado="2026-11-10")))
    repo.nueva_version(usuario["id"], apunte, doc, "investigacion")
    exportacion = "e" * 32
    datos_tmp.bd.ejecutar("INSERT INTO exportaciones (id, apunte_id, usuario_id, version, clave, estado, archivo_id, "
                          "sha256, creado, actualizado) VALUES (?, ?, ?, 1, 'x', 'completado', ?, 'h', ?, ?)",
                          (exportacion, apunte, usuario["id"], archivo, ahora(), ahora()))
    atacante = nuevo_cliente()
    atacante.registrar("intruso@example.com")
    atacante.patch("/api/v2/perfil", json={"preferencias": {"investigacion_permitida": True}})
    valores = {"apunte_id": apunte, "archivo_id": archivo, "numero": 1, "trabajo_id": trabajo,
               "ampliacion_id": "a1", "exportacion_id": exportacion}
    return duena, atacante, valores


@pytest.mark.parametrize("metodo,ruta", RUTAS_CON_RECURSO)
def test_idor_otro_usuario_recibe_404(victima_y_atacante, metodo, ruta, datos_tmp):
    duena, atacante, valores = victima_y_atacante
    antes = datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM versiones")["n"]
    url = ruta.format(**valores)
    cuerpos = {"PUT": {"titulo": "robado"}, "PATCH": {"estado": "aceptada"},
               "POST": {"consentimiento": True, "conceptos": ["x"]}}
    kw = {"headers": {"If-Match": "3"}, "json": cuerpos[metodo]} if metodo in ("PUT", "PATCH") else {}
    if metodo == "POST" and ruta.endswith("investigacion"):
        kw = {"json": cuerpos["POST"]}
    if metodo == "POST" and ruta.endswith("exportaciones"):
        kw = {"json": {}}
    r = getattr(atacante, metodo.lower())(url, **kw)
    assert r.status_code == 404, (metodo, url, r.text)
    assert r.json()["error"]["codigo"] == "NO_ENCONTRADO"
    # Nada cambió para la dueña
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM versiones")["n"] == antes
    assert duena.get(f"/api/v2/apuntes/{valores['apunte_id']}").status_code == 200
    estado = datos_tmp.bd.uno("SELECT estado FROM trabajos WHERE id = ?", (valores["trabajo_id"],))["estado"]
    assert estado == "fallido"


@pytest.mark.parametrize("metodo,ruta", RUTAS_CON_RECURSO)
def test_sin_sesion_recibe_401(victima_y_atacante, metodo, ruta):
    _, _, valores = victima_y_atacante
    r = TestClient(app).request(metodo, ruta.format(**valores))
    assert r.status_code == 401 and r.json()["error"]["codigo"] == "NO_AUTENTICADO"


def test_archivo_de_otro_apunte_propio_no_se_sirve(con_apuntes, datos_tmp):
    c, ids, *_ = con_apuntes
    archivo_b = datos_tmp.bd.uno("SELECT id FROM archivos WHERE apunte_id = ?", (ids[1],))["id"]
    assert c.get(f"/api/v2/apuntes/{ids[0]}/archivos/{archivo_b}").status_code == 404


@pytest.mark.parametrize("archivo", ["..%2F..%2Fdatos.sqlite3", "%2E%2E", "%2E%2E%2F%2E%2E", "a%00b", "C:%5Cwindows"])
def test_traversal_en_archivos(con_apuntes, archivo):
    c, ids, *_ = con_apuntes
    r = c.get(f"/api/v2/apuntes/{ids[0]}/archivos/{archivo}")
    assert r.status_code == 404
    assert "sqlite" not in r.text and "datos" not in r.text


def test_nombre_de_archivo_subido_no_construye_rutas(nuevo_cliente, datos_tmp):
    c = nuevo_cliente()
    c.registrar()
    r = c.post("/api/v2/apuntes", data={"tipos": "cuaderno", "titulo": "t"},
               files=[("paginas", ("../../../evil.png", imagen_pil("PNG"), "image/png"))])
    assert r.status_code == 202, r.text
    rutas = [f["ruta"] for f in datos_tmp.bd.todos("SELECT ruta FROM archivos")]
    assert rutas and all(".." not in ruta and "evil" not in ruta for ruta in rutas)
    assert not any(p.name == "evil.png" for p in datos_tmp.data_dir.parent.rglob("evil.png"))


@pytest.mark.parametrize("contenido", [b"<html><script>alert(1)</script></html>", b"%PDF-1.4 falso",
                                       b"MZ\x90\x00 ejecutable", b""])
def test_contenido_disfrazado_se_rechaza(nuevo_cliente, contenido, datos_tmp):
    c = nuevo_cliente()
    c.registrar()
    r = c.post("/api/v2/apuntes", data={"tipos": "cuaderno"},
               files=[("paginas", ("foto.png", contenido, "image/png"))])
    assert r.status_code == 400
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM archivos")["n"] == 0


@pytest.mark.parametrize("latex", [r"\input{/etc/passwd}", r"\write18{rm -rf /}", r"\href{javascript:x}{a}",
                                   r"\def\x{\x}\x", "x" * 3000])
def test_latex_peligroso_se_rechaza(nuevo_cliente, latex):
    c = nuevo_cliente()
    c.registrar()
    r = c.post("/api/v2/formulas/validar", json={"latex": latex})
    assert r.status_code == 400, r.text
    assert r.json()["error"]["codigo"] in ("LATEX_NO_PERMITIDO", "DATOS_INVALIDOS")


def test_html_en_el_documento_se_guarda_como_texto_y_no_se_ejecuta(con_apuntes):
    c, ids, *_ = con_apuntes
    doc = c.get(f"/api/v2/apuntes/{ids[0]}").json()["apunte"]["documento"]
    doc["bloques"][0]["texto"] = "<img src=x onerror=alert(1)><script>alert(2)</script>"
    r = c.put(f"/api/v2/apuntes/{ids[0]}/documento", json=doc, headers={"If-Match": "2"})
    assert r.status_code == 200, r.text
    r = c.get(f"/api/v2/apuntes/{ids[0]}")
    assert r.headers["content-type"].startswith("application/json")
    assert "sandbox" in r.headers["content-security-policy"]
    assert r.json()["apunte"]["documento"]["bloques"][0]["texto"].startswith("<img")


# ------------------------------------------------------------------ tamaño del cuerpo

def test_cuerpo_enorme_por_content_length(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    r = c.post("/api/v2/formulas/validar", content=b"{}",
               headers={"Content-Type": "application/json", "Content-Length": str(50 * 1024 * 1024)})
    assert r.status_code == 413 and r.json()["error"]["codigo"] == "CARGA_DEMASIADO_GRANDE"


def test_cuerpo_enorme_por_trozos(nuevo_cliente, monkeypatch):
    monkeypatch.setattr(settings, "max_json_kb", 1)
    c = nuevo_cliente()
    c.registrar()

    def trozos():
        for _ in range(10):
            yield b"x" * 1024

    r = c.post("/api/v2/formulas/validar", content=trozos(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413 and r.json()["error"]["codigo"] == "CARGA_DEMASIADO_GRANDE"


def test_subida_multipart_mayor_que_el_total_permitido(nuevo_cliente, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 0.01)
    monkeypatch.setattr(settings, "max_paginas", 2)
    c = nuevo_cliente()
    c.registrar()
    r = c.post("/api/v2/apuntes", data={"tipos": "cuaderno"},
               files=[("paginas", ("a.png", b"\x89PNG" + b"0" * 600_000, "image/png"))])
    assert r.status_code == 413


def test_v1_conserva_su_contrato_de_tamano(client, subir, monkeypatch):
    assert subir(imagen_pil("PNG")).status_code == 200
    monkeypatch.setattr(settings, "max_upload_mb", 0.01)
    r = subir(b"\x89PNG" + b"0" * 20_000)
    assert r.status_code == 413 and r.json()["error"]["codigo"] == "ARCHIVO_DEMASIADO_GRANDE"


# ------------------------------------------------------------------ CSRF, origen y CORS

def test_csrf_y_origen(con_apuntes):
    c, ids, *_ = con_apuntes
    sin_token = c.http.delete(f"/api/v2/apuntes/{ids[0]}")
    assert sin_token.status_code == 403 and sin_token.json()["error"]["codigo"] == "CSRF_INVALIDO"
    otro_origen = c.delete(f"/api/v2/apuntes/{ids[0]}", headers={"Origin": "https://malicioso.example"})
    assert otro_origen.status_code == 403 and otro_origen.json()["error"]["codigo"] == "ORIGEN_NO_PERMITIDO"
    assert c.get(f"/api/v2/apuntes/{ids[0]}").status_code == 200


def test_cors_no_permite_credenciales_ni_origenes_desconocidos(client):
    r = client.options("/api/v2/apuntes", headers={"Origin": "https://malicioso.example",
                                                   "Access-Control-Request-Method": "DELETE"})
    assert "access-control-allow-credentials" not in r.headers
    assert r.headers.get("access-control-allow-origin") in (None, "*") or "malicioso" not in r.headers.get(
        "access-control-allow-origin", "")
    r = client.get("/salud", headers={"Origin": "https://malicioso.example"})
    assert "access-control-allow-credentials" not in r.headers


def test_cookie_de_sesion_protegida(datos_tmp):
    r = TestClient(app).post("/api/v2/auth/registro",
                             json={"email": "c@example.com", "nombre": "C", "password": clave_de_prueba("c1")})
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "path=/" in cookie


# ------------------------------------------------------------------ límites de abuso

def test_limite_de_registros_por_ip(datos_tmp, monkeypatch):
    monkeypatch.setitem(endurecimiento.LIMITES, "registro", (2, 3600))
    http = TestClient(app)
    codigos = [http.post("/api/v2/auth/registro", json={"email": f"u{i}@example.com", "nombre": "U",
                                                        "password": clave_de_prueba("c1")}).status_code
               for i in range(3)]
    assert codigos == [201, 201, 429]


def test_limite_de_recuperacion_por_email(datos_tmp, monkeypatch):
    http = TestClient(app)
    codigos = [http.post("/api/v2/auth/recuperacion", json={"email": "x@example.com"}).status_code for _ in range(4)]
    assert codigos == [202, 202, 202, 429]


def test_limite_de_formulas(nuevo_cliente, monkeypatch):
    monkeypatch.setitem(endurecimiento.LIMITES, "formulas", (2, 60))
    c = nuevo_cliente()
    c.registrar()
    codigos = [c.post("/api/v2/formulas/validar", json={"latex": "x"}).status_code for _ in range(3)]
    assert codigos == [200, 200, 429]
    assert c.post("/api/v2/formulas/validar", json={"latex": "x"}).json()["error"]["codigo"] == "DEMASIADAS_PETICIONES"


def test_limite_de_subidas_y_cuota(nuevo_cliente, monkeypatch, datos_tmp):
    c = nuevo_cliente()
    c.registrar()
    monkeypatch.setattr(settings, "cuota_mb_usuario", 0)
    r = c.post("/api/v2/apuntes", data={"tipos": "cuaderno"}, files=[("paginas", ("a.png", imagen_pil("PNG"), "image/png"))])
    assert r.status_code == 413 and r.json()["error"]["codigo"] == "CUOTA_EXCEDIDA"
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM apuntes")["n"] == 0


def test_los_fallos_de_login_no_borran_otros_limites(datos_tmp, monkeypatch):
    monkeypatch.setitem(endurecimiento.LIMITES, "registro", (1, 3600))
    http = TestClient(app)
    assert http.post("/api/v2/auth/registro", json={"email": "a@example.com", "nombre": "A",
                                                     "password": clave_de_prueba("c1")}).status_code == 201
    http.post("/api/v2/auth/sesion", json={"email": "a@example.com", "password": clave_de_prueba("mala")})  # limpia intentos viejos
    assert http.post("/api/v2/auth/registro", json={"email": "b@example.com", "nombre": "B",
                                                     "password": clave_de_prueba("c1")}).status_code == 429


# ------------------------------------------------------------------ cabeceras y fugas

@pytest.mark.parametrize("url", ["/salud", "/api/v2/auth/sesion", "/no-existe"])
def test_cabeceras_de_seguridad(client, url):
    r = client.get(url)
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "no-referrer"
    if url.startswith("/api/v2/"):
        assert r.headers["cache-control"] == "private, no-store"
        assert "default-src 'none'" in r.headers["content-security-policy"]


def test_error_interno_sin_trazas_ni_rutas(nuevo_cliente, monkeypatch):
    from app.routers import v2_apuntes

    def explota(*a, **k):
        raise RuntimeError("fallo en /home/secreto/datos.sqlite3 token=abc123")

    c = nuevo_cliente()
    c.registrar()
    monkeypatch.setattr(v2_apuntes, "repositorio", explota)
    r = c.get("/api/v2/apuntes")
    assert r.status_code == 500
    assert r.json()["error"]["codigo"] == "ERROR_INTERNO"
    assert "secreto" not in r.text and "Traceback" not in r.text and "abc123" not in r.text
    assert r.headers.get("x-apuntia-error-id") and r.headers["x-content-type-options"] == "nosniff"


def test_logs_sin_contrasenas_ni_tokens(datos_tmp, caplog):
    caplog.set_level(logging.DEBUG)
    http = TestClient(app)
    password = clave_de_prueba("c8")
    r = http.post("/api/v2/auth/registro", json={"email": "log@example.com", "nombre": "L", "password": password})
    token = http.cookies.get("apuntia_sesion")
    http.post("/api/v2/auth/sesion", json={"email": "log@example.com", "password": clave_de_prueba("c6")})
    http.post("/api/v2/auth/recuperacion", json={"email": "log@example.com"})
    texto = caplog.text
    assert r.status_code == 201 and token
    assert password not in texto and clave_de_prueba("c6") not in texto and token not in texto
    assert "log@example.com" not in texto and r.json()["csrf"] not in texto


def test_borrar_cuenta_no_deja_archivos(con_apuntes, datos_tmp):
    c, _, _, usuario = con_apuntes
    carpeta = datos_tmp.data_dir / "archivos" / usuario["id"]
    assert any(carpeta.rglob("*"))
    assert c.delete("/api/v2/perfil", json={"password": clave_de_prueba("c1")}).status_code == 204
    assert not carpeta.exists() or not any(p.is_file() for p in carpeta.rglob("*"))
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM archivos")["n"] == 0


def test_v1_no_guarda_nada_en_el_servidor(subir, datos_tmp):
    antes = sorted(p for p in datos_tmp.data_dir.rglob("*") if p.is_file())
    assert subir(imagen_pil("PNG")).status_code == 200
    assert sorted(p for p in datos_tmp.data_dir.rglob("*") if p.is_file()) == antes


def _bomba_png(lado=20000) -> bytes:
    """PNG válido de lado×lado píxeles en gris (400 MP) que comprimido ocupa ~380 KB."""
    import struct
    import zlib

    def trozo(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xffffffff)

    comp = zlib.compressobj(9)
    fila = b"\x00" * (lado + 1)
    idat = b"".join(comp.compress(fila) for _ in range(lado)) + comp.flush()
    return (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", lado, lado, 8, 0, 0, 0, 0))
            + trozo(b"IDAT", idat) + trozo(b"IEND", b""))


def test_bomba_de_descompresion_se_rechaza_sin_descomprimir(client, nuevo_cliente):
    import resource
    import time as reloj
    bomba = _bomba_png()
    antes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    inicio = reloj.monotonic()
    r = client.post("/analisis", files={"file": ("b.png", bomba, "image/png")})
    assert r.status_code == 413 and r.json()["error"]["codigo"] == "IMAGEN_DEMASIADO_GRANDE"
    assert reloj.monotonic() - inicio < 2
    assert (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - antes) < 100 * 1024, "no se reservaron 400 MB"
    c = nuevo_cliente()
    c.registrar()
    r = c.post("/api/v2/apuntes", data={"tipos": "cuaderno"}, files=[("paginas", ("b.png", bomba, "image/png"))])
    # Contrato v2: fotos inválidas → 400 con el código de la página (fullstack/docs/api-v2.md §6)
    assert r.status_code == 400 and r.json()["error"]["codigo"] == "IMAGEN_DEMASIADO_GRANDE"
