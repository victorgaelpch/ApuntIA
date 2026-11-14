"""Diagnóstico del sistema (FULL-21): id de petición, logs sin datos sensibles, disponibilidad
separada de la salud y métricas solo desde el propio equipo."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.core import diagnostico
from app.core.config import settings
from app.main import app
from herramientas.claves_prueba import clave_de_prueba


def test_id_de_peticion_generado_o_respetado(client):
    r = client.get("/salud")
    pid = r.headers["x-apuntia-peticion-id"]
    assert len(pid) == 16
    assert client.get("/salud", headers={"X-ApuntIA-Peticion-Id": "interfaz-1234abcd"}).headers["x-apuntia-peticion-id"] == "interfaz-1234abcd"
    # Un valor raro no se acepta (no se refleja tal cual)
    raro = client.get("/salud", headers={"X-ApuntIA-Peticion-Id": "<script>"}).headers["x-apuntia-peticion-id"]
    assert raro != "<script>" and len(raro) == 16


def test_el_id_aparece_en_los_logs_de_la_peticion_y_del_trabajo(nuevo_cliente, caplog):
    caplog.set_level(logging.INFO)
    c = nuevo_cliente()
    c.registrar()
    from tests.conftest import imagen_pil
    r = c.post("/api/v2/apuntes", files=[("paginas", ("a.png", imagen_pil("PNG", (300, 200)), "image/png"))],
               data={"tipos": "cuaderno"}, headers={"X-ApuntIA-Peticion-Id": "prueba-correlacion-1"})
    assert r.status_code == 202
    registros = [x for x in caplog.records if getattr(x, "peticion", None) == "prueba-correlacion-1"]
    mensajes = " ".join(x.getMessage() for x in registros)
    assert f"trabajo={r.json()['trabajo']['id']}" in mensajes and "encolado" in mensajes
    assert "POST /api/v2/apuntes 202" in mensajes


def test_los_logs_enmascaran_datos_sensibles(caplog):
    caplog.set_level(logging.INFO)
    log = logging.getLogger("apuntia.prueba")
    filtro = diagnostico.FiltroDiagnostico()
    registro = log.makeRecord("apuntia.prueba", logging.INFO, __file__, 1,
                              "login de ana@example.com password=%s token: %s", (clave_de_prueba("c23"), "x" * 45), None)
    filtro.filter(registro)
    texto = registro.getMessage()
    assert "ana@example.com" not in texto and clave_de_prueba("c23") not in texto and "x" * 45 not in texto
    assert "[email]" in texto and "[oculto]" in texto


def test_formato_json(caplog):
    registro = logging.LogRecord("apuntia.x", logging.ERROR, __file__, 1, "fallo con %s", ("dato",), None)
    registro.peticion = "abc12345"
    import json
    linea = json.loads(diagnostico.FormatoJson().format(registro))
    assert linea["peticion"] == "abc12345" and linea["mensaje"] == "fallo con dato" and linea["nivel"] == "ERROR"


def test_rutas_agrupadas_sin_ids_ni_consultas():
    assert diagnostico.grupo_de_ruta("/api/v2/apuntes/0123456789abcdef0123/versiones/2?q=privado") == "/api/v2/apuntes/{id}/versiones/{id}"


def test_listo_cuando_todo_funciona(client, datos_tmp):
    datos_tmp.trabajos.iniciar()
    r = client.get("/api/v2/listo")
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["listo"] is True
    assert {"base_datos", "almacenamiento", "trabajos", "ocr", "investigacion"} <= set(cuerpo["dependencias"])
    assert client.get("/salud").json()["base_datos"] == {"disponible": True}


def test_no_esta_listo_si_cae_la_base_de_datos(client, datos_tmp, monkeypatch):
    datos_tmp.trabajos.iniciar()

    def caida(*_a, **_k):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(datos_tmp.bd, "uno", caida)
    r = client.get("/api/v2/listo")
    assert r.status_code == 503 and r.json()["listo"] is False
    assert r.json()["dependencias"]["base_datos"]["ok"] is False
    assert "base_datos" in r.json()["mensaje"]
    # /salud sigue respondiendo (la app está viva) y lo indica sin romper el contrato v1
    s = client.get("/salud")
    assert s.status_code == 200 and s.json()["estado"] == "ok" and s.json()["base_datos"]["disponible"] is False


def test_no_esta_listo_sin_ocr_configurado_ni_sin_espacio(client, datos_tmp, monkeypatch):
    from app.services import ocr
    datos_tmp.trabajos.iniciar()
    monkeypatch.setattr(ocr, "_motor", ocr.MotorNinguno())
    monkeypatch.setattr(settings, "ocr_motor", "tesseract")
    r = client.get("/api/v2/listo").json()
    assert r["listo"] is False and "Tesseract" in r["dependencias"]["ocr"]["detalle"]
    monkeypatch.setattr(settings, "ocr_motor", "ninguno")
    assert client.get("/api/v2/listo").json()["dependencias"]["ocr"]["obligatoria"] is False
    monkeypatch.setattr(settings, "minimo_disco_mb", 10 ** 12)
    r = client.get("/api/v2/listo")
    assert r.status_code == 503 and "libera espacio" in r.json()["dependencias"]["almacenamiento"]["detalle"]


def test_no_esta_listo_sin_despachador(client, datos_tmp):
    datos_tmp.trabajos.detener()
    r = client.get("/api/v2/listo")
    assert r.status_code == 503 and r.json()["dependencias"]["trabajos"]["ok"] is False


def test_diagnostico_solo_desde_el_equipo(datos_tmp, client):
    assert client.get("/api/v2/diagnostico").status_code == 404   # TestClient no es 127.0.0.1
    local = TestClient(app, client=("127.0.0.1", 50000))
    local.get("/api/v2/apuntes")  # alguna petición para las métricas
    d = local.get("/api/v2/diagnostico").json()
    assert {"version", "dependencias", "peticiones", "trabajos", "datos_mb", "limites"} <= set(d)
    assert d["peticiones"]["total"] >= 1
    assert all("{id}" in k or "/" in k for k in d["peticiones"]["rutas"])


def test_alerta_de_trabajo_lento(datos_tmp, caplog, monkeypatch):
    import time
    from app.services.trabajos import Resultado
    caplog.set_level(logging.WARNING, logger="apuntia.trabajos")
    monkeypatch.setattr(settings, "alerta_trabajo_s", 0)
    datos_tmp.bd.ejecutar("INSERT INTO usuarios (id, email, nombre, hash_password, creado, actualizado) VALUES ('u', 'u@x.com', 'u', 'h', 'f', 'f')")
    datos_tmp.trabajos.registrar("lento_prueba", lambda t: (time.sleep(0.05), Resultado())[1])
    t = datos_tmp.trabajos.encolar("u", "lento_prueba")
    fin = time.time() + 5
    while time.time() < fin and datos_tmp.trabajos.obtener("u", t["id"])["estado"] != "completado":
        time.sleep(0.05)
    assert any("ALERTA" in r.getMessage() and t["id"] in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize("ruta", ["/salud", "/api/v2/listo"])
def test_salud_y_listo_sin_sesion(client, datos_tmp, ruta):
    assert client.get(ruta).status_code in (200, 503)


def test_la_linea_de_acceso_de_uvicorn_no_guarda_consultas():
    registro = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, '%s - "%s %s HTTP/%s" %d',
                                 ("127.0.0.1:1", "GET", "/api/v2/apuntes?q=mi%20secreto", "1.1", 200), None)
    diagnostico.SinConsulta().filter(registro)
    assert "secreto" not in registro.getMessage() and "/api/v2/apuntes" in registro.getMessage()
    assert any(isinstance(f, diagnostico.SinConsulta) for f in logging.getLogger("uvicorn.access").filters)


def test_listo_avisa_si_faltan_idiomas_del_ocr(client, datos_tmp, monkeypatch):
    """FULL-32: un Tesseract sin «spa» funciona pero pierde tildes; se avisa sin bloquear."""
    from app.services import ocr

    class SinEspanol:
        def info(self):
            return {"disponible": True, "motor": "tesseract", "version": "5.4.0", "idiomas": ["eng"]}

    monkeypatch.setattr(ocr, "motor_ocr", lambda: SinEspanol())
    monkeypatch.setattr(settings, "ocr_idiomas", "spa+eng")
    datos_tmp.trabajos.iniciar()
    cuerpo = client.get("/api/v2/listo").json()
    assert cuerpo["dependencias"]["ocr"]["ok"] is True and cuerpo["dependencias"]["ocr"]["faltan_idiomas"] == ["spa"]
    assert "spa.traineddata" in cuerpo["dependencias"]["ocr"]["detalle"]
