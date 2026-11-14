"""Cliente del servidor IA remoto y rutas /api/v2/ia (FULL-31). Sin red ni GPU.

Incluye una prueba de extremo a extremo contra el servidor IA REAL (ia_servidor) en proceso,
con un Ollama simulado: vinculación, aprobación por consola, análisis, cambio de URL y revocación.
"""

import http.server
import json
import socket
import ssl
import sys
import threading
import urllib.error
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import ia_remota
from app.services.ia_remota import Almacen, Circuito, ClienteIARemota, ErrorIARemota, origen, validar_url
from tests.conftest import ClienteV2

RAIZ = Path(__file__).resolve().parents[3]
URL = "https://ia.ejemplo.org"


# ---------------------------------------------------------------------------- URL y origen

@pytest.mark.parametrize("url, ok", [
    ("https://ia.ejemplo.org", True), ("https://ia.ejemplo.org:8443/", True), ("http://127.0.0.1:8100", True),
    ("http://localhost:8100", True), ("http://ia.ejemplo.org", False), ("https://203.0.113.9", False),
    ("https://u:p@ia.ejemplo.org", False), ("https://ia.ejemplo.org/?token=x", False),
    ("https://ia.ejemplo.org/ruta", False), ("file:///C:/x", False), ("", False),
])
def test_validar_url(url, ok):
    assert (validar_url(url) is None) is ok


def test_origen():
    assert origen("https://IA.ejemplo.org/") == origen("https://ia.ejemplo.org:443") == "https://ia.ejemplo.org:443"
    assert origen("https://ia.ejemplo.org") != origen("https://ia.ejemplo.org:8443")
    assert origen("http://127.0.0.1:8100") != origen("https://127.0.0.1:8100")


# ---------------------------------------------------------------------------- credencial

def guardar_credencial(almacen, url=URL, token="token-secreto-de-prueba-0123456789"):
    t, p = ia_remota.proteger(token)
    almacen.actualizar(credencial={"origen": origen(url), "dispositivo_id": "d1", "token": t, "proteccion": p})
    return token


def test_credencial_solo_para_su_origen(tmp_path):
    a = Almacen(tmp_path)
    token = guardar_credencial(a)
    assert a.token_para(URL) == token
    assert a.token_para("https://otro.ejemplo.org") is None
    assert a.token_para("https://ia.ejemplo.org:8443") is None


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI solo existe en Windows")
def test_dpapi_cifra_la_credencial(tmp_path):
    a = Almacen(tmp_path)
    token = guardar_credencial(a)
    contenido = a.archivo.read_text(encoding="utf-8")
    assert token not in contenido and '"proteccion": "dpapi"' in contenido
    import base64
    assert token.encode() not in base64.b64decode(a.leer()["credencial"]["token"])


def test_id_de_instalacion_estable(tmp_path):
    a = Almacen(tmp_path)
    assert a.dispositivo_id() == a.dispositivo_id() and a.dispositivo_id().startswith("apuntia-")


# ---------------------------------------------------------------------------- transporte simulado

class Falso:
    def __init__(self, respuestas):
        self.respuestas, self.peticiones = list(respuestas), []

    def __call__(self, metodo, url, cuerpo, cabeceras, timeout):
        self.peticiones.append((metodo, url, dict(cabeceras)))
        r = self.respuestas.pop(0)
        if isinstance(r, BaseException):
            raise r
        estado, cuerpo_r = r[0], r[1]
        cab = r[2] if len(r) > 2 else {}
        return estado, cab, json.dumps(cuerpo_r).encode() if not isinstance(cuerpo_r, bytes) else cuerpo_r


SALUD = (200, {"estado": "ok", "servicio": "apuntia-ia", "api_version": "1.0"})


def nuevo(tmp_path, respuestas, **kw):
    esperas = []
    c = ClienteIARemota(URL, Almacen(tmp_path), transporte=Falso(respuestas), espera=esperas.append,
                        circuito=kw.pop("circuito", Circuito()), **kw)
    return c, esperas


@pytest.mark.parametrize("exc, codigo", [
    (urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed")), "AI_NET_DNS"),
    (urllib.error.URLError(ssl.SSLCertVerificationError("certificate has expired")), "AI_NET_TLS"),
    (urllib.error.URLError(socket.timeout("timed out")), "AI_NET_TIMEOUT"),
    (urllib.error.URLError(ConnectionRefusedError()), "AI_NET_CONEXION"),
    (TimeoutError(), "AI_NET_TIMEOUT"),
])
def test_errores_de_red(tmp_path, exc, codigo):
    c, _ = nuevo(tmp_path, [exc] * 3)
    with pytest.raises(ErrorIARemota) as e:
        c.salud()
    assert e.value.codigo == codigo


def test_tls_no_se_reintenta(tmp_path):
    c, _ = nuevo(tmp_path, [urllib.error.URLError(ssl.SSLCertVerificationError("x"))] * 3)
    with pytest.raises(ErrorIARemota):
        c.salud()
    assert len(c.transporte.peticiones) == 1


@pytest.mark.parametrize("estado, codigo", [(401, "AI_AUTH"), (403, "AI_REVOCADO")])
def test_401_403_sin_reintento(tmp_path, estado, codigo):
    guardar_credencial(Almacen(tmp_path))
    c, _ = nuevo(tmp_path, [(estado, {"error": {"codigo": "X", "mensaje": "m"}})] * 3)
    with pytest.raises(ErrorIARemota) as e:
        c.yo()
    assert e.value.codigo == codigo and len(c.transporte.peticiones) == 1


def test_429_respeta_retry_after_y_luego_funciona(tmp_path):
    guardar_credencial(Almacen(tmp_path))
    c, esperas = nuevo(tmp_path, [(429, {}, {"retry-after": "3"}), (200, {"nombre": "x"})])
    assert c.yo() == {"nombre": "x"} and esperas == [3.0]


def test_503_reintenta_con_espera_creciente(tmp_path):
    guardar_credencial(Almacen(tmp_path))
    c, esperas = nuevo(tmp_path, [(503, {"error": {"reintentable": True}}), (503, {"error": {"reintentable": True}}),
                                  (200, {"nombre": "x"})])
    assert c.yo()["nombre"] == "x" and esperas == [0.5, 1.0]


def test_error_no_reintentable_del_servidor(tmp_path):
    guardar_credencial(Almacen(tmp_path))
    c, _ = nuevo(tmp_path, [(503, {"error": {"codigo": "MODELO_NO_INSTALADO", "mensaje": "falta el modelo", "reintentable": False}})])
    with pytest.raises(ErrorIARemota) as e:
        c.yo()
    assert e.value.codigo == "AI_SERVIDOR" and "falta el modelo" in e.value.mensaje


def test_respuesta_no_json(tmp_path):
    c, _ = nuevo(tmp_path, [(200, b"<html>portal cautivo</html>")])
    with pytest.raises(ErrorIARemota) as e:
        c.salud()
    assert e.value.codigo == "AI_RESPUESTA"


def test_no_es_un_servidor_ia(tmp_path):
    c, _ = nuevo(tmp_path, [(200, {"estado": "ok"})])
    with pytest.raises(ErrorIARemota, match="no es un servidor IA"):
        c.salud()


def test_version_incompatible(tmp_path):
    c, _ = nuevo(tmp_path, [(200, {"servicio": "apuntia-ia", "api_version": "2.0"})])
    with pytest.raises(ErrorIARemota) as e:
        c.salud()
    assert e.value.codigo == "AI_VERSION"


def test_sin_vincular_no_envia_nada(tmp_path):
    c, _ = nuevo(tmp_path, [])
    with pytest.raises(ErrorIARemota) as e:
        c.analizar(b"png")
    assert e.value.codigo == "AI_NO_VINCULADO" and c.transporte.peticiones == []


def test_circuit_breaker(tmp_path):
    reloj = [0.0]
    circuito = Circuito(umbral=3, enfriamiento_s=30, reloj=lambda: reloj[0])
    caido = urllib.error.URLError(ConnectionRefusedError())
    c, _ = nuevo(tmp_path, [caido] * 3 + [SALUD], reintentos=0, circuito=circuito)
    for _ in range(3):
        with pytest.raises(ErrorIARemota):
            c.salud()
    with pytest.raises(ErrorIARemota) as e:
        c.salud()
    assert e.value.codigo == "AI_CIRCUITO_ABIERTO" and len(c.transporte.peticiones) == 3  # ni lo intentó
    reloj[0] = 31
    assert c.salud()["api_version"] == "1.0" and circuito.fallos == 0


# ---------------------------------------------------------------------------- redirecciones (HTTP real)

class _Redirige(http.server.BaseHTTPRequestHandler):
    vistos = []

    def do_GET(self):
        _Redirige.vistos.append((self.path, self.headers.get("Authorization")))
        if self.path.startswith("/robar"):
            self.send_response(200); self.end_headers(); self.wfile.write(b"{}")
            return
        self.send_response(302)
        self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/robar")
        self.end_headers()

    def log_message(self, *a):
        pass


def test_no_sigue_redirecciones_ni_filtra_el_token(tmp_path):
    servidor = http.server.HTTPServer(("127.0.0.1", 0), _Redirige)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{servidor.server_port}"
        a = Almacen(tmp_path)
        guardar_credencial(a, url)
        c = ClienteIARemota(url, a, circuito=Circuito())
        with pytest.raises(ErrorIARemota) as e:
            c.yo()
        assert e.value.codigo == "AI_REDIRECCION"
        assert [p for p, _ in _Redirige.vistos] == ["/api/v1/yo"]  # nunca llegó a /robar
    finally:
        servidor.shutdown()


# ---------------------------------------------------------------------------- extremo a extremo con el servidor IA real

@pytest.fixture
def servidor_ia(tmp_path):
    sys.path.insert(0, str(RAIZ))
    sys.path.insert(0, str(RAIZ / "ia_servidor" / "tests"))
    try:
        from conftest import OllamaFalso, gpu_falsa  # dobles del servidor IA
        from ia_servidor.app import crear_app
        from ia_servidor.config import Configuracion
        from ia_servidor.dispositivos import Registro
        from ia_servidor.ollama import ClienteOllama
        from ia_servidor.servicio import Servicio
    finally:
        sys.path.remove(str(RAIZ / "ia_servidor" / "tests"))
    cfg = Configuracion()
    registro = Registro(tmp_path / "servidor")
    servicio = Servicio(cfg, ClienteOllama(cfg.ollama_url, OllamaFalso(chat=["Hola [?]"] * 10)), leer_gpu=gpu_falsa,
                        carpeta_modelos=tmp_path)
    http = TestClient(crear_app(cfg, servicio, registro))
    vistas = []

    def transporte(metodo, url, cuerpo, cabeceras, timeout):  # «red» hacia el servidor en proceso
        vistas.append((url, cabeceras.get("Authorization")))
        ruta = "/" + url.split("/", 3)[3]
        r = http.request(metodo, ruta, content=cuerpo, headers=cabeceras)
        return r.status_code, {k.lower(): v for k, v in r.headers.items()}, r.content

    return registro, transporte, vistas


def test_extremo_a_extremo(tmp_path, servidor_ia):
    registro, transporte, vistas = servidor_ia
    almacen = Almacen(tmp_path / "laptop")
    c = ClienteIARemota(URL, almacen, transporte=transporte, espera=lambda s: None, circuito=Circuito())
    assert c.estado()["requiere_vinculacion"] is True

    v = c.solicitar_vinculacion("ApuntIA de Ana")
    assert c.sondear_vinculacion()["estado"] == "pendiente"
    registro.resolver(v["codigo"], aprobar=True)                       # el administrador, en su consola
    assert c.sondear_vinculacion() == {"estado": "vinculado"}
    assert c.estado()["modo"] == "remoto" and c.yo()["nombre"] == "ApuntIA de Ana"
    import cv2
    import numpy as np
    png = cv2.imencode(".png", np.full((200, 300, 3), 255, np.uint8))[1].tobytes()
    r = c.analizar(png, "texto_impreso")
    assert r["resultado"]["texto"] == "Hola [?]" and r["resultado"]["revision_requerida"] is True

    with pytest.raises(ErrorIARemota) as e:                             # error del contrato del servidor
        c.analizar(b"\x89PNG\r\n\x1a\n" + bytes(10), "texto_impreso")
    assert e.value.codigo == "IMAGEN_CORRUPTA" and e.value.estado_http == 400

    # Cambiar la URL a mano: la credencial NO viaja al servidor nuevo
    otro = ClienteIARemota("https://otro.ejemplo.org", almacen, transporte=transporte, circuito=Circuito())
    with pytest.raises(ErrorIARemota) as e:
        otro.analizar(png)
    assert e.value.codigo == "AI_NO_VINCULADO"
    assert not any(url.startswith("https://otro") for url, _ in vistas)
    assert otro.estado()["requiere_vinculacion"] is True

    registro.revocar(c.yo()["dispositivo_id"])                          # el administrador revoca
    with pytest.raises(ErrorIARemota) as e:
        c.analizar(png)
    assert e.value.codigo == "AI_REVOCADO"


def test_vinculacion_rechazada(tmp_path, servidor_ia):
    registro, transporte, _ = servidor_ia
    c = ClienteIARemota(URL, Almacen(tmp_path / "laptop"), transporte=transporte, circuito=Circuito())
    v = c.solicitar_vinculacion("x")
    registro.resolver(v["codigo"], aprobar=False)
    assert c.sondear_vinculacion()["estado"] == "rechazada"
    with pytest.raises(ErrorIARemota) as e:
        c.sondear_vinculacion()
    assert e.value.codigo == "AI_VINCULACION"


# ---------------------------------------------------------------------------- rutas /api/v2/ia

class ClienteLocal(ClienteV2):
    def __init__(self, host="127.0.0.1"):
        super().__init__()
        self.http = TestClient(app, raise_server_exceptions=False, client=(host, 50000))


def test_estado_requiere_sesion(nuevo_cliente):
    assert nuevo_cliente().get("/api/v2/ia/estado").status_code == 401


def test_estado_sin_configurar_es_modo_local(nuevo_cliente, monkeypatch):
    monkeypatch.setattr("app.routers.v2_ia.settings.ia_url", "")
    c = nuevo_cliente()
    c.registrar()
    e = c.get("/api/v2/ia/estado").json()
    assert e["modo"] == "local" and e["url"] is None and "token" not in json.dumps(e)


def test_acciones_solo_desde_el_propio_equipo(nuevo_cliente):
    c = nuevo_cliente()  # TestClient normal: no es 127.0.0.1 (como un alumno por la red del aula)
    c.registrar()
    for metodo, ruta in [("put", "/api/v2/ia/configuracion"), ("post", "/api/v2/ia/vinculacion"),
                         ("get", "/api/v2/ia/vinculacion"), ("delete", "/api/v2/ia/vinculacion"), ("get", "/api/v2/ia/diagnostico")]:
        kw = {"json": {"url": URL}} if metodo == "put" else {}
        r = getattr(c, metodo)(ruta, **kw)
        assert (r.status_code, r.json()["error"]["codigo"]) == (403, "SOLO_EQUIPO_LOCAL"), ruta


def test_configurar_url_valida_y_rechaza_insegura(datos_tmp, monkeypatch):
    monkeypatch.setattr("app.routers.v2_ia.settings.ia_url", "")
    c = ClienteLocal()
    c.registrar()
    r = c.put("/api/v2/ia/configuracion", json={"url": "http://ia.ejemplo.org"})
    assert (r.status_code, r.json()["error"]["codigo"]) == (400, "AI_URL_INVALIDA")
    e = c.put("/api/v2/ia/configuracion", json={"url": URL + "/"}).json()
    assert e["url"] == URL and e["requiere_vinculacion"] is True
    assert c.put("/api/v2/ia/configuracion", json={"url": None}).json()["modo"] == "local"


def test_configurar_exige_csrf(datos_tmp):
    c = ClienteLocal()
    c.registrar()
    c.csrf = "otro"
    assert c.put("/api/v2/ia/configuracion", json={"url": URL}).status_code == 403


def test_vinculacion_y_diagnostico_por_la_api(datos_tmp, servidor_ia, monkeypatch):
    registro, transporte, _ = servidor_ia
    monkeypatch.setattr(ia_remota, "transporte_urllib", transporte)
    monkeypatch.setattr("app.routers.v2_ia.settings.ia_url", URL)
    monkeypatch.setattr(ia_remota.socket, "getaddrinfo", lambda *a, **k: [(0, 0, 0, "", ("203.0.113.7", 443))])
    ia_remota._CIRCUITOS.clear()
    c = ClienteLocal()
    c.registrar(nombre="Ana")
    v = c.post("/api/v2/ia/vinculacion")
    assert v.status_code == 201 and len(v.json()["codigo"]) == 9
    assert c.get("/api/v2/ia/vinculacion").json()["estado"] == "pendiente"
    registro.resolver(v.json()["codigo"], aprobar=True)
    assert c.get("/api/v2/ia/vinculacion").json() == {"estado": "vinculado"}
    d = c.get("/api/v2/ia/diagnostico").json()
    assert d["ok"] is True and [p["paso"] for p in d["pasos"]] == ["configuracion", "dns", "salud_tls_y_version",
                                                                   "credencial", "modelo_y_gpu"]
    assert "token" not in json.dumps(d).lower().replace("token_", "")
    e = c.delete("/api/v2/ia/vinculacion").json()
    assert e["vinculado"] is False and "revoque" in e["aviso"]


def test_diagnostico_con_dns_caido(datos_tmp, monkeypatch):
    monkeypatch.setattr("app.routers.v2_ia.settings.ia_url", URL)

    def sin_dns(*a, **k):
        raise socket.gaierror(11001, "getaddrinfo failed")
    monkeypatch.setattr(ia_remota.socket, "getaddrinfo", sin_dns)
    c = ClienteLocal()
    c.registrar()
    d = c.get("/api/v2/ia/diagnostico").json()
    assert d["ok"] is False and d["pasos"][-1]["codigo"] == "AI_NET_DNS" and d["pasos"][-1]["solucion"]
