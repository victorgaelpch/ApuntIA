"""Historial, búsqueda, edición y versiones (BACK-26)."""

import copy

import pytest

from app.datos.apuntes import RepositorioApuntes
from app.services.documento import Bloque


@pytest.fixture
def con_apuntes(nuevo_cliente, datos_tmp):
    """Usuario con 3 apuntes analizados (sin OCR real: se escribe el documento)."""
    from tests.conftest import imagen_pil
    c = nuevo_cliente()
    usuario = c.registrar()
    repo = RepositorioApuntes(datos_tmp.bd, datos_tmp.almacen)
    from app.services.entrada import PaginaRecibida
    from app.services.validacion import ImagenRecibida
    import numpy as np
    ids = []
    for titulo, texto, tipo in (("Derivadas", "La derivada mide el cambio", "cuaderno"),
                                ("Integrales", "Área bajo la curva", "pizarron"),
                                ("Historia 100%", "Revolución_francesa", "cuaderno")):
        pag = PaginaRecibida(1, tipo, ImagenRecibida("a.png", "png", imagen_pil("PNG"), np.zeros((48, 64, 3), np.uint8)))
        apunte, _ = repo.crear(usuario["id"], titulo, [pag])
        doc = repo.documento(usuario["id"], apunte["id"])
        doc.bloques.append(Bloque(id="p1b1", pagina="p1", orden=0, tipo="texto", origen="ocr", texto=texto,
                                  texto_original=texto, confianza=0.95, bbox=[0, 0, 10, 10]))
        repo.nueva_version(usuario["id"], apunte["id"], doc, "analisis", estado="listo")
        ids.append(apunte["id"])
    return c, ids, repo, usuario


def test_listar_paginado_y_ordenado(con_apuntes):
    c, ids, *_ = con_apuntes
    r = c.get("/api/v2/apuntes?por_pagina=2").json()
    assert r["total"] == 3 and len(r["elementos"]) == 2 and r["elementos"][0]["id"] == ids[-1]
    assert c.get("/api/v2/apuntes?por_pagina=2&pagina=2").json()["elementos"][0]["id"] == ids[0]
    titulos = [e["titulo"] for e in c.get("/api/v2/apuntes?orden=titulo").json()["elementos"]]
    assert titulos == sorted(titulos, key=str.lower)


def test_busqueda_en_titulo_y_texto_y_filtros(con_apuntes):
    c, ids, *_ = con_apuntes
    assert [e["id"] for e in c.get("/api/v2/apuntes?q=curva").json()["elementos"]] == [ids[1]]
    assert [e["id"] for e in c.get("/api/v2/apuntes?q=deriva").json()["elementos"]] == [ids[0]]
    assert c.get("/api/v2/apuntes?tipo_fuente=pizarron").json()["total"] == 1
    assert c.get("/api/v2/apuntes?estado=fallido").json()["total"] == 0
    # Los comodines de SQL se buscan literalmente
    assert [e["id"] for e in c.get("/api/v2/apuntes?q=100%25").json()["elementos"]] == [ids[2]]
    assert c.get("/api/v2/apuntes?q=_").json()["total"] == 1


def test_otro_usuario_no_ve_ni_encuentra_nada(con_apuntes, nuevo_cliente):
    _, ids, *_ = con_apuntes
    otro = nuevo_cliente()
    otro.registrar("otro@example.com")
    assert otro.get("/api/v2/apuntes").json()["total"] == 0
    assert otro.get("/api/v2/apuntes?q=Derivadas").json()["total"] == 0
    for url in (f"/api/v2/apuntes/{ids[0]}", f"/api/v2/apuntes/{ids[0]}/versiones",
                f"/api/v2/apuntes/{ids[0]}/versiones/1"):
        assert otro.get(url).status_code == 404
    assert otro.put(f"/api/v2/apuntes/{ids[0]}/documento", json={}, headers={"If-Match": "2"}).status_code == 404
    assert otro.delete(f"/api/v2/apuntes/{ids[0]}").status_code == 404


def test_editar_con_control_de_concurrencia(con_apuntes):
    c, ids, *_ = con_apuntes
    apunte = c.get(f"/api/v2/apuntes/{ids[0]}").json()["apunte"]
    doc = copy.deepcopy(apunte["documento"])
    doc["bloques"][0]["texto"] = "La derivada mide la razón de cambio"
    assert c.put(f"/api/v2/apuntes/{ids[0]}/documento", json=doc).json()["error"]["codigo"] == "VERSION_REQUERIDA"
    r = c.put(f"/api/v2/apuntes/{ids[0]}/documento", json=doc, headers={"If-Match": str(apunte["version"])})
    assert r.status_code == 200 and r.json()["version"] == apunte["version"] + 1
    bloque = r.json()["apunte"]["documento"]["bloques"][0]
    assert bloque["editado"] and bloque["texto_original"] == "La derivada mide el cambio"
    # Otra pestaña con la versión vieja no pisa el cambio
    viejo = c.put(f"/api/v2/apuntes/{ids[0]}/documento", json=doc, headers={"If-Match": str(apunte["version"])})
    assert viejo.status_code == 409 and viejo.json()["error"]["codigo"] == "CONFLICTO_VERSION"
    # La búsqueda encuentra el texto corregido
    assert c.get("/api/v2/apuntes?q=razón").json()["total"] == 1


def test_documento_invalido_no_modifica_nada(con_apuntes):
    c, ids, *_ = con_apuntes
    apunte = c.get(f"/api/v2/apuntes/{ids[0]}").json()["apunte"]
    malo = copy.deepcopy(apunte["documento"])
    malo["bloques"][0]["bbox"] = [9, 9, 1, 1]
    r = c.put(f"/api/v2/apuntes/{ids[0]}/documento", json=malo, headers={"If-Match": str(apunte["version"])})
    assert r.json()["error"]["codigo"] == "DOCUMENTO_INVALIDO"
    assert c.get(f"/api/v2/apuntes/{ids[0]}").json()["apunte"]["version"] == apunte["version"]


def test_versiones_y_restaurar(con_apuntes):
    c, ids, *_ = con_apuntes
    apunte = c.get(f"/api/v2/apuntes/{ids[0]}").json()["apunte"]
    doc = copy.deepcopy(apunte["documento"])
    doc["bloques"][0]["texto"] = "cambio 1"
    c.put(f"/api/v2/apuntes/{ids[0]}/documento", json=doc, headers={"If-Match": str(apunte["version"])})
    versiones = c.get(f"/api/v2/apuntes/{ids[0]}/versiones").json()["versiones"]
    assert [v["motivo"] for v in versiones] == ["edicion", "analisis", "creacion"]
    v2 = c.get(f"/api/v2/apuntes/{ids[0]}/versiones/2").json()["documento"]
    assert v2["bloques"][0]["texto"] == "La derivada mide el cambio"
    r = c.post(f"/api/v2/apuntes/{ids[0]}/versiones/2/restaurar").json()
    assert r["version"] == 4 and r["apunte"]["documento"]["bloques"][0]["texto"] == "La derivada mide el cambio"
    assert len(c.get(f"/api/v2/apuntes/{ids[0]}/versiones").json()["versiones"]) == 4  # no se borra nada


def test_no_se_edita_durante_el_analisis(con_apuntes):
    c, ids, repo, _ = con_apuntes
    repo.cambiar_estado(ids[0], "procesando")
    apunte = c.get(f"/api/v2/apuntes/{ids[0]}").json()["apunte"]
    r = c.put(f"/api/v2/apuntes/{ids[0]}/documento", json=apunte["documento"],
              headers={"If-Match": str(apunte["version"])})
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "APUNTE_EN_PROCESO"


def test_borrar_apunte_y_archivos(con_apuntes, datos_tmp):
    c, ids, *_ = con_apuntes
    archivo = c.get(f"/api/v2/apuntes/{ids[0]}").json()["apunte"]["documento"]["paginas"][0]["archivo_original"]
    ruta = datos_tmp.almacen.obtener(c.get("/api/v2/perfil").json()["usuario"]["id"], archivo).ruta
    assert c.delete(f"/api/v2/apuntes/{ids[0]}").status_code == 204
    assert c.get(f"/api/v2/apuntes/{ids[0]}").status_code == 404
    assert not ruta.exists()
    assert c.get("/api/v2/apuntes").json()["total"] == 2


def test_persisten_tras_reiniciar(con_apuntes, datos_tmp):
    from app.core import contexto
    c, ids, *_ = con_apuntes
    contexto.reiniciar(datos_tmp.data_dir)  # «reinicio» del servidor con la misma carpeta
    assert c.get("/api/v2/apuntes").json()["total"] == 3


def test_filtro_por_fechas(con_apuntes, datos_tmp):
    c, ids, *_ = con_apuntes
    datos_tmp.bd.ejecutar("UPDATE apuntes SET creado = '2026-01-15T10:00:00+00:00' WHERE id = ?", (ids[0],))
    datos_tmp.bd.ejecutar("UPDATE apuntes SET creado = '2026-03-01T23:59:00+00:00' WHERE id = ?", (ids[1],))
    r = c.get("/api/v2/apuntes?desde=2026-01-01&hasta=2026-03-01").json()
    assert {e["id"] for e in r["elementos"]} == {ids[0], ids[1]}
    assert c.get("/api/v2/apuntes?hasta=2026-01-15").json()["total"] == 1
    assert c.get("/api/v2/apuntes?desde=2026-13-99x").status_code == 400
