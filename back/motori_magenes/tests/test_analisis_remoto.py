"""Análisis con el servidor IA remoto dentro de los trabajos durables (BACK-37, BACK-38).

Extremo a extremo SIN red ni GPU: el backend real (con su base de datos y su gestor de trabajos)
habla con el servidor IA real (ia_servidor) en proceso, que usa un Ollama simulado.
"""

import sys
import time
import urllib.error
from pathlib import Path

import cv2
import pytest
from fastapi.testclient import TestClient

from app.services import ia_remota
from app.services.ia_remota import Almacen, Circuito, ClienteIARemota, ErrorIARemota, codigo_publico
from herramientas.corpus import impreso_cuaderno

RAIZ = Path(__file__).resolve().parents[3]
URL = "https://ia.ejemplo.org"


@pytest.fixture
def servidor(tmp_path, monkeypatch, datos_tmp):
    sys.path.insert(0, str(RAIZ))
    sys.path.insert(0, str(RAIZ / "ia_servidor" / "tests"))
    try:
        from conftest import OllamaFalso, gpu_falsa
        from ia_servidor.app import crear_app
        from ia_servidor.config import Configuracion
        from ia_servidor.dispositivos import Registro
        from ia_servidor.ollama import ClienteOllama
        from ia_servidor.servicio import Servicio
    finally:
        sys.path.remove(str(RAIZ / "ia_servidor" / "tests"))
    ollama = OllamaFalso(chat=[r"$\frac{a}{b}$"] * 200)
    cfg = Configuracion(seg_hueco_lineas=0.6)
    registro = Registro(tmp_path / "servidor")
    servicio = Servicio(cfg, ClienteOllama(cfg.ollama_url, ollama), leer_gpu=gpu_falsa, carpeta_modelos=tmp_path)
    http = TestClient(crear_app(cfg, servicio, registro))
    estado = {"caido": False}

    def transporte(metodo, url, cuerpo, cabeceras, timeout):
        if estado["caido"]:
            raise urllib.error.URLError(ConnectionRefusedError())
        r = http.request(metodo, "/" + url.split("/", 3)[3], content=cuerpo, headers=cabeceras)
        return r.status_code, {k.lower(): v for k, v in r.headers.items()}, r.content

    monkeypatch.setattr(ia_remota, "transporte_urllib", transporte)
    monkeypatch.setattr("app.core.config.settings.ia_url", URL)
    ia_remota._CIRCUITOS.clear()
    return {"registro": registro, "ollama": ollama, "estado": estado, "datos": datos_tmp}


def vincular(servidor):
    c = ClienteIARemota(URL, Almacen(servidor["datos"].data_dir), circuito=Circuito())
    v = c.solicitar_vinculacion("Laptop de pruebas")
    servidor["registro"].resolver(v["codigo"], aprobar=True)
    assert c.sondear_vinculacion() == {"estado": "vinculado"}


def esperar(c, trabajo_id, limite=30):
    fin = time.time() + limite
    while time.time() < fin:
        t = c.get(f"/api/v2/trabajos/{trabajo_id}").json()["trabajo"]
        if t["estado"] not in ("pendiente", "procesando"):
            return t
        time.sleep(0.1)
    raise AssertionError("el análisis no terminó")


def crear(c, motor):
    png = cv2.imencode(".png", impreso_cuaderno().imagen)[1].tobytes()
    r = c.post("/api/v2/apuntes", files=[("paginas", ("hoja.png", png, "image/png"))],
               data={"tipos": ["cuaderno"], "titulo": "Clase", "motor": motor})
    assert r.status_code == 202, r.text
    return r.json()


def test_analisis_remoto_completo(nuevo_cliente, servidor):
    vincular(servidor)
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, "ia_remota")
    t = esperar(c, creado["trabajo"]["id"])
    assert t["estado"] == "completado", t
    assert t["resultado"]["motor"] == "ia_remota" and t["resultado"]["bloques"] >= 1
    doc = c.get(f"/api/v2/apuntes/{creado['apunte']['id']}").json()["apunte"]["documento"]
    b = doc["bloques"][0]
    assert b["procedencia"]["motor"] == "ia_remota" and b["revision"] == "sin_confirmar"
    assert b["confianza"] is None and b["recorte"] and b["bbox"] and b["latex"] == r"\frac{a}{b}"
    assert b["latex_valido"] is True and b["origen"] == "ocr"
    pagina = doc["paginas"][0]
    assert "servidor IA" in pagina["advertencias"][0]
    # el recorte de origen se puede descargar para revisar contra la foto (FRONT-26)
    assert c.get(f"/api/v2/apuntes/{creado['apunte']['id']}/archivos/{b['recorte']}").status_code == 200


def test_marcar_revisado_se_guarda_sin_cambiar_la_procedencia(nuevo_cliente, servidor):
    vincular(servidor)
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, "ia_remota")
    esperar(c, creado["trabajo"]["id"])
    aid = creado["apunte"]["id"]
    apunte = c.get(f"/api/v2/apuntes/{aid}").json()["apunte"]
    doc = apunte["documento"]
    assert doc["bloques"][0]["revisado"] is False
    doc["bloques"][0]["revisado"] = True
    doc["bloques"][0]["procedencia"] = {"motor": "usuario-tramposo"}   # el servidor lo ignora
    doc["bloques"][0]["revision"] = None
    assert c.put(f"/api/v2/apuntes/{aid}/documento", json=doc, headers={"If-Match": str(apunte["version"])}).status_code == 200
    b = c.get(f"/api/v2/apuntes/{aid}").json()["apunte"]["documento"]["bloques"][0]
    assert b["revisado"] is True and b["procedencia"]["motor"] == "ia_remota" and b["revision"] == "sin_confirmar"


def test_reanalizar_no_repite_la_gpu(nuevo_cliente, servidor):
    vincular(servidor)
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, "ia_remota")
    esperar(c, creado["trabajo"]["id"])
    llamadas = len(servidor["ollama"].chats())
    r = c.post(f"/api/v2/apuntes/{creado['apunte']['id']}/analisis", json={"motor": "ia_remota"})
    assert r.status_code == 202
    assert esperar(c, r.json()["trabajo"]["id"])["estado"] == "completado"
    assert len(servidor["ollama"].chats()) == llamadas      # resultado reutilizado por su clave
    versiones = c.get(f"/api/v2/apuntes/{creado['apunte']['id']}/versiones").json()
    assert len(versiones["versiones"]) >= 2                  # versión nueva; la anterior sigue en el historial


def test_sin_vinculacion_falla_con_codigo_publico(nuevo_cliente, servidor):
    c = nuevo_cliente()
    c.registrar()
    t = esperar(c, crear(c, "ia_remota")["trabajo"]["id"])
    assert t["estado"] == "fallido" and t["error"]["codigo"] == "AI_NO_AUTORIZADA"


def test_servidor_caido_conserva_la_foto_y_reintentar_lo_completa(nuevo_cliente, servidor):
    vincular(servidor)
    servidor["estado"]["caido"] = True
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, "ia_remota")
    t = esperar(c, creado["trabajo"]["id"])
    assert t["estado"] == "fallido" and t["error"]["codigo"] == "AI_NO_DISPONIBLE"
    apunte = c.get(f"/api/v2/apuntes/{creado['apunte']['id']}").json()["apunte"]
    original = apunte["documento"]["paginas"][0]["archivo_original"]
    assert c.get(f"/api/v2/apuntes/{creado['apunte']['id']}/archivos/{original}").status_code == 200  # foto intacta
    servidor["estado"]["caido"] = False
    ia_remota._CIRCUITOS.clear()
    r = c.post(f"/api/v2/trabajos/{t['id']}/reintentar")
    assert r.status_code in (200, 202)
    assert esperar(c, t["id"])["estado"] == "completado"     # el MISMO trabajo, sin duplicar el apunte


def test_reanalizar_con_ediciones_pide_confirmacion(nuevo_cliente, servidor):
    vincular(servidor)
    c = nuevo_cliente()
    c.registrar()
    creado = crear(c, "ia_remota")
    esperar(c, creado["trabajo"]["id"])
    aid = creado["apunte"]["id"]
    apunte = c.get(f"/api/v2/apuntes/{aid}").json()["apunte"]
    doc = apunte["documento"]
    doc["bloques"][0]["texto"] = "corregido a mano"
    r = c.put(f"/api/v2/apuntes/{aid}/documento", json=doc, headers={"If-Match": str(apunte["version"])})
    assert r.status_code == 200, r.text
    r = c.post(f"/api/v2/apuntes/{aid}/analisis", json={"motor": "ia_remota"})
    assert (r.status_code, r.json()["error"]["codigo"]) == (409, "APUNTE_CON_EDICIONES")
    assert c.post(f"/api/v2/apuntes/{aid}/analisis", json={"motor": "ia_remota", "sobrescribir_ediciones": True}).status_code == 202


# ---------------------------------------------------------------------------- cliente asíncrono

class Cola:
    def __init__(self, respuestas):
        self.respuestas, self.vistas = list(respuestas), []

    def __call__(self, metodo, url, cuerpo, cabeceras, timeout):
        self.vistas.append((metodo, url.split("/api/v1")[-1], cabeceras.get("Idempotency-Key")))
        estado, datos = self.respuestas.pop(0)
        import json as j
        return estado, {}, j.dumps(datos).encode()


def cliente(tmp_path, respuestas):
    a = Almacen(tmp_path)
    t, p = ia_remota.proteger("token-de-prueba-0123456789")
    a.actualizar(credencial={"origen": ia_remota.origen(URL), "dispositivo_id": "d", "token": t, "proteccion": p})
    esperas = []
    return ClienteIARemota(URL, a, transporte=Cola(respuestas), espera=esperas.append, circuito=Circuito()), esperas


def test_cliente_envia_espera_y_recoge(tmp_path):
    guardados = []
    c, esperas = cliente(tmp_path, [(202, {"trabajo_id": "t1", "estado": "en_cola"}),
                                    (200, {"estado": "en_cola", "posicion": 1}),
                                    (200, {"estado": "procesando", "progreso": 50}),
                                    (200, {"estado": "completado", "progreso": 100, "resultado": {"ok": 1}})])
    avances = []
    r = c.analizar_trabajo(b"png", "documento", "clave-1", guardar_id=guardados.append,
                           al_avance=lambda e, p, pos: avances.append((e, p)))
    assert r == {"ok": 1} and guardados == ["t1"]
    assert c.transporte.vistas[0] == ("POST", "/trabajos?tarea=documento", "clave-1")
    assert avances == [("en_cola", 0), ("procesando", 50), ("completado", 100)]
    assert 0.8 <= esperas[0] <= 1.2 and esperas[1] > esperas[0]   # espera creciente con jitter


def test_cliente_retoma_por_id_sin_reenviar(tmp_path):
    c, _ = cliente(tmp_path, [(200, {"estado": "procesando"}), (200, {"estado": "completado", "resultado": {"ok": 2}})])
    assert c.analizar_trabajo(b"png", "documento", "k", trabajo_remoto="t9") == {"ok": 2}
    assert all(m == "GET" for m, _, _ in c.transporte.vistas)    # nada de POST: no se repite la GPU


def test_cliente_reenvia_si_el_servidor_olvido_el_trabajo(tmp_path):
    c, _ = cliente(tmp_path, [(404, {"error": {"codigo": "TRABAJO_NO_ENCONTRADO", "mensaje": "x"}}),
                              (202, {"trabajo_id": "t2", "estado": "en_cola"}),
                              (200, {"estado": "completado", "resultado": {"ok": 3}})])
    assert c.analizar_trabajo(b"png", "documento", "k", trabajo_remoto="viejo") == {"ok": 3}
    assert [m for m, _, _ in c.transporte.vistas] == ["GET", "POST", "GET"]


def test_cliente_cancela_tambien_en_el_servidor(tmp_path):
    c, _ = cliente(tmp_path, [(202, {"trabajo_id": "t3", "estado": "en_cola"}), (200, {"estado": "cancelado"})])
    with pytest.raises(ErrorIARemota) as e:
        c.analizar_trabajo(b"png", "documento", "k", cancelado=lambda: True)
    assert e.value.codigo == "AI_CANCELADO" and c.transporte.vistas[-1][0] == "DELETE"


def test_trabajo_fallido_en_el_servidor(tmp_path):
    c, _ = cliente(tmp_path, [(202, {"trabajo_id": "t4", "estado": "en_cola"}),
                              (200, {"estado": "fallido", "error": {"codigo": "SIN_MEMORIA", "mensaje": "GPU llena",
                                                                    "reintentable": True}})])
    with pytest.raises(ErrorIARemota) as e:
        c.analizar_trabajo(b"png", "documento", "k")
    assert codigo_publico(e.value)[0] == "AI_MEMORIA_INSUFICIENTE" and e.value.reintentable


@pytest.mark.parametrize("error, publico", [
    (ErrorIARemota("AI_NET_DNS", ""), "AI_NO_DISPONIBLE"),
    (ErrorIARemota("AI_CIRCUITO_ABIERTO", ""), "AI_NO_DISPONIBLE"),
    (ErrorIARemota("AI_REVOCADO", ""), "AI_NO_AUTORIZADA"),
    (ErrorIARemota("AI_SERVIDOR", "", codigo_servidor="MODELO_NO_INSTALADO"), "AI_MODELO_AUSENTE"),
    (ErrorIARemota("AI_SERVIDOR", "", codigo_servidor="RESPUESTA_INVALIDA"), "AI_RESPUESTA_INVALIDA"),
    (ErrorIARemota("AI_LIMITE", ""), "AI_COLA_LLENA"),
    (ErrorIARemota("AI_VERSION", ""), "AI_CONTRATO_INCOMPATIBLE"),
    (ErrorIARemota("AI_NET_TIMEOUT", ""), "AI_TIEMPO_AGOTADO"),
])
def test_codigos_publicos(error, publico):
    codigo, mensaje = codigo_publico(error)
    assert codigo == publico and len(mensaje) > 30
