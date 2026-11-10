"""API de análisis con estado de trabajos (BACK-21)."""

import time

import cv2
import pytest

from app.services import analisis, ocr
from app.services.ocr import MotorNinguno
from herramientas.corpus import formulas_pizarron, impreso_cuaderno, impreso_pizarron

requiere_tesseract = pytest.mark.skipif(not ocr.MotorTesseract().disponible(), reason="Tesseract no está instalado")


def png(muestra):
    return cv2.imencode(".png", muestra.imagen)[1].tobytes()


def esperar(c, trabajo_id, limite=60):
    fin = time.time() + limite
    while time.time() < fin:
        t = c.get(f"/api/v2/trabajos/{trabajo_id}").json()["trabajo"]
        if t["estado"] not in ("pendiente", "procesando"):
            return t
        time.sleep(0.2)
    raise AssertionError("el análisis no terminó")


def crear(c, muestras, tipos):
    files = [("paginas", (f"{m.nombre}.png", png(m), "image/png")) for m in muestras]
    r = c.post("/api/v2/apuntes", files=files, data={"tipos": tipos, "titulo": "Clase"})
    assert r.status_code == 202, r.text
    return r.json()


@requiere_tesseract
def test_analisis_completo_de_dos_paginas(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, [impreso_cuaderno(), formulas_pizarron()], ["cuaderno", "pizarron"])
    assert creado["trabajo"]["tipo"] == "analisis"
    t = esperar(c, creado["trabajo"]["id"])
    assert t["estado"] == "completado" and t["resultado"]["bloques"] > 3
    apunte = c.get(f"/api/v2/apuntes/{creado['apunte']['id']}").json()["apunte"]
    doc = apunte["documento"]
    assert apunte["estado"] == "listo" and apunte["version"] == 2
    textos = " ".join(b["texto"] for b in doc["bloques"])
    assert "Derivadas" in textos and "función" in textos
    assert [b["pagina"] for b in doc["bloques"]].index("p2") > 0  # orden: página 1 y después la 2
    assert any(b["tipo"] == "formula" and b["latex"] for b in doc["bloques"])
    # La imagen procesada y los recortes son archivos privados accesibles al propietario
    pagina = doc["paginas"][0]
    assert c.get(f"/api/v2/apuntes/{apunte['id']}/archivos/{pagina['archivo_procesado']}").status_code == 200
    recorte = next(b["recorte"] for b in doc["bloques"] if b["recorte"])
    assert c.get(f"/api/v2/apuntes/{apunte['id']}/archivos/{recorte}").headers["content-type"] == "image/png"


@requiere_tesseract
def test_bloques_con_procedencia_y_confianza(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, [impreso_pizarron()], ["pizarron"])
    esperar(c, creado["trabajo"]["id"])
    doc = c.get(f"/api/v2/apuntes/{creado['apunte']['id']}").json()["apunte"]["documento"]
    for b in doc["bloques"]:
        assert b["origen"] == "ocr" and b["texto_original"] == b["texto"] and not b["editado"]
        assert 0 <= b["confianza"] <= 1 and len(b["bbox"]) == 4
    assert doc["paginas"][0]["advertencias"] == []


def test_ocr_no_disponible_es_fallo_y_no_texto_vacio(nuevo_cliente, monkeypatch):
    monkeypatch.setattr(ocr, "_motor", MotorNinguno())
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, [impreso_cuaderno()], ["cuaderno"])
    t = esperar(c, creado["trabajo"]["id"])
    assert t["estado"] == "fallido" and t["error"]["codigo"] == "OCR_NO_DISPONIBLE"
    assert c.get(f"/api/v2/apuntes/{creado['apunte']['id']}").json()["apunte"]["estado"] == "fallido"


@requiere_tesseract
def test_una_pagina_fallida_da_parcial(nuevo_cliente, monkeypatch):
    original = analisis.analizar_pagina

    def falla_la_segunda(trabajo, pagina, idiomas):
        if pagina.orden == 2:
            raise RuntimeError("fallo simulado")
        return original(trabajo, pagina, idiomas)

    monkeypatch.setattr(analisis, "analizar_pagina", falla_la_segunda)
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, [impreso_cuaderno(), impreso_cuaderno()], ["cuaderno"])
    t = esperar(c, creado["trabajo"]["id"])
    assert t["estado"] == "parcial" and "página 2" in t["error"]["mensaje"]
    apunte = c.get(f"/api/v2/apuntes/{creado['apunte']['id']}").json()["apunte"]
    assert apunte["estado"] == "parcial"
    assert apunte["documento"]["paginas"][1]["error"] and not apunte["documento"]["paginas"][0]["error"]
    assert all(b["pagina"] == "p1" for b in apunte["documento"]["bloques"])


def test_cancelar_borra_intermedios(nuevo_cliente, datos_tmp, monkeypatch):
    def lento(trabajo, pagina, idiomas):
        analisis._guardar(trabajo, b"intermedio", "procesada", "image/jpeg")
        for _ in range(100):
            trabajo.avance("ocr", 10)
            time.sleep(0.05)
        raise AssertionError("no se canceló")

    monkeypatch.setattr(analisis, "analizar_pagina", lento)
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, [impreso_cuaderno()], ["cuaderno"])
    time.sleep(0.5)
    c.delete(f"/api/v2/trabajos/{creado['trabajo']['id']}")
    assert esperar(c, creado["trabajo"]["id"])["estado"] == "cancelado"
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM archivos WHERE tipo = 'procesada'")["n"] == 0
    assert c.get(f"/api/v2/apuntes/{creado['apunte']['id']}").json()["apunte"]["estado"] == "cancelado"


def test_idempotencia_no_lanza_otro_analisis(nuevo_cliente, datos_tmp, monkeypatch):
    monkeypatch.setattr(ocr, "_motor", MotorNinguno())
    c = nuevo_cliente()
    c.registrar()
    files = [("paginas", ("a.png", png(impreso_cuaderno()), "image/png"))]
    r1 = c.post("/api/v2/apuntes", files=files, data={"tipos": ["cuaderno"]}, headers={"Idempotency-Key": "x"})
    r2 = c.post("/api/v2/apuntes", files=files, data={"tipos": ["cuaderno"]}, headers={"Idempotency-Key": "x"})
    assert r2.json()["trabajo"]["id"] == r1.json()["trabajo"]["id"]
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM trabajos")["n"] == 1
