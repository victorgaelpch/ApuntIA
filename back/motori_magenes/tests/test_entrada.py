"""Entrada de varias páginas de pizarrón o cuaderno (BACK-11)."""

import pytest

from app.core.config import settings
from tests.conftest import imagen_pil


def fotos(n, fmt="PNG"):
    return [("paginas", (f"hoja{i}.{fmt.lower()}", imagen_pil(fmt, (60 + i, 40)), f"image/{fmt.lower()}"))
            for i in range(1, n + 1)]


def test_varias_paginas_conservan_orden_y_tipo(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    r = c.post("/api/v2/apuntes", files=fotos(3),
               data={"tipos": ["cuaderno", "pizarron", "cuaderno"], "titulo": "Clase 1"})
    assert r.status_code == 202, r.text
    apunte = r.json()["apunte"]
    assert apunte["estado"] == "pendiente" and apunte["tipo_fuente"] == "mixto" and apunte["paginas"] == 3
    paginas = apunte["documento"]["paginas"]
    assert [p["orden"] for p in paginas] == [1, 2, 3]
    assert [p["tipo_fuente"] for p in paginas] == ["cuaderno", "pizarron", "cuaderno"]
    assert [p["ancho"] for p in paginas] == [61, 62, 63]  # el orden corresponde a cada foto


def test_un_solo_tipo_vale_para_todas(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    r = c.post("/api/v2/apuntes", files=fotos(2), data={"tipos": ["cuaderno"]})
    assert r.json()["apunte"]["tipo_fuente"] == "cuaderno"


def test_el_original_se_guarda_intacto_y_privado(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    original = imagen_pil("PNG", (50, 30))
    apunte = c.post("/api/v2/apuntes", files=[("paginas", ("a.png", original, "image/png"))],
                    data={"tipos": ["pizarron"]}).json()["apunte"]
    archivo = apunte["documento"]["paginas"][0]["archivo_original"]
    r = c.get(f"/api/v2/apuntes/{apunte['id']}/archivos/{archivo}")
    assert r.status_code == 200 and r.content == original
    assert r.headers["cache-control"] == "private, no-store"
    otro = nuevo_cliente()
    otro.registrar("otro@example.com")
    assert otro.get(f"/api/v2/apuntes/{apunte['id']}/archivos/{archivo}").status_code == 404


def test_una_pagina_invalida_identifica_cual_y_no_guarda_nada(nuevo_cliente, datos_tmp):
    c = nuevo_cliente()
    c.registrar()
    archivos = fotos(3)
    archivos[1] = ("paginas", ("falsa.png", b"%PDF-1.4 no", "image/png"))
    r = c.post("/api/v2/apuntes", files=archivos, data={"tipos": ["cuaderno"]})
    assert r.status_code == 400
    error = r.json()["error"]
    assert error["codigo"] == "TIPO_NO_PERMITIDO" and "página 2" in error["mensaje"]
    assert error["detalles"] == [{"pagina": 2, "codigo": "TIPO_NO_PERMITIDO", "mensaje": error["detalles"][0]["mensaje"]}]
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM apuntes")["n"] == 0
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM archivos")["n"] == 0
    assert "/" not in error["mensaje"].replace("JPEG, PNG o WEBP", "")  # sin rutas internas


@pytest.mark.parametrize("datos,codigo", [
    ({"tipos": ["libro"]}, "DATOS_INVALIDOS"),
    ({"tipos": ["cuaderno", "cuaderno", "cuaderno"]}, "DATOS_INVALIDOS"),
])
def test_tipos_invalidos(nuevo_cliente, datos, codigo):
    c = nuevo_cliente()
    c.registrar()
    assert c.post("/api/v2/apuntes", files=fotos(2), data=datos).json()["error"]["codigo"] in (codigo, "PAGINAS_INVALIDAS")


def test_sin_paginas_y_demasiadas(nuevo_cliente, monkeypatch):
    c = nuevo_cliente()
    c.registrar()
    assert c.post("/api/v2/apuntes", data={"titulo": "x"}).json()["error"]["codigo"] == "ARCHIVO_AUSENTE"
    monkeypatch.setattr(settings, "max_paginas", 2)
    assert c.post("/api/v2/apuntes", files=fotos(3), data={"tipos": ["cuaderno"]}).json()["error"]["codigo"] == "DEMASIADAS_PAGINAS"


def test_idempotencia(nuevo_cliente, datos_tmp):
    c = nuevo_cliente()
    c.registrar()
    r1 = c.post("/api/v2/apuntes", files=fotos(1), data={"tipos": ["cuaderno"]}, headers={"Idempotency-Key": "k1"})
    r2 = c.post("/api/v2/apuntes", files=fotos(1), data={"tipos": ["cuaderno"]}, headers={"Idempotency-Key": "k1"})
    assert r1.status_code == 202 and r2.status_code == 200
    assert r1.json()["apunte"]["id"] == r2.json()["apunte"]["id"]
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM apuntes")["n"] == 1


def test_requiere_sesion(nuevo_cliente):
    r = nuevo_cliente().post("/api/v2/apuntes", files=fotos(1), data={"tipos": ["cuaderno"]})
    assert r.status_code == 401


def test_analisis_v1_sigue_igual(client):
    r = client.post("/analisis", files={"file": ("a.png", imagen_pil("PNG"), "image/png")})
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
