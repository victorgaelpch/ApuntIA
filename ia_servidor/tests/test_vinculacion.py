"""Vinculación, autorización, revocación y límites del servidor IA (FULL-31)."""

import json
import threading

import pytest

from conftest import png, vincular
from ia_servidor import admin
from ia_servidor.config import Configuracion, ConfiguracionInvalida
from ia_servidor.dispositivos import MAX_PENDIENTES, ErrorVinculacion, Registro


def solicitar(cliente, dispositivo_id="laptop-profesor-0001", nombre="Laptop del profesor"):
    return cliente.post("/api/v1/vinculacion/solicitudes", json={"dispositivo_id": dispositivo_id, "nombre": nombre})


def sondear(cliente, s, secreto=None):
    return cliente.post(f"/api/v1/vinculacion/solicitudes/{s['solicitud_id']}/estado",
                        json={"secreto": secreto or s["secreto"]})


def analizar(cliente, token=None):
    cabeceras = {"Content-Type": "image/png"}
    if token is not None:
        cabeceras["Authorization"] = f"Bearer {token}"
    return cliente.post("/api/v1/analisis?tarea=formula", content=png(), headers=cabeceras)


# ---------------------------------------------------------------------------- sin credencial

def test_salud_publica_y_sin_documentacion_publica(armar):
    cliente, *_ = armar(autenticado=False)
    assert cliente.get("/salud").status_code == 200
    assert cliente.get("/docs").status_code == 404 and cliente.get("/openapi.json").status_code == 404


@pytest.mark.parametrize("ruta, metodo", [("/api/v1/analisis", "post"), ("/api/v1/capacidades", "get"), ("/api/v1/yo", "get")])
def test_rutas_protegidas_sin_credencial(armar, ruta, metodo):
    cliente, ollama, _ = armar(autenticado=False)
    r = getattr(cliente, metodo)(ruta, **({"content": png(), "headers": {"Content-Type": "image/png"}} if metodo == "post" else {}))
    assert (r.status_code, r.json()["error"]["codigo"]) == (401, "NO_AUTENTICADO")
    assert ollama.chats() == []  # nunca llega a la GPU


def test_token_inventado(armar):
    cliente, *_ = armar(autenticado=False)
    r = analizar(cliente, "inventado-" + "x" * 40)
    assert (r.status_code, r.json()["error"]["codigo"]) == (401, "NO_AUTENTICADO")


def test_listo_sin_credencial_no_revela_el_equipo(armar):
    cliente, *_ = armar(autenticado=False)
    j = cliente.get("/listo").json()
    assert set(j) == {"listo", "api_version"}


def test_listo_con_credencial_da_detalle(armar):
    cliente, *_ = armar()
    assert "componentes" in cliente.get("/listo").json()


# ---------------------------------------------------------------------------- flujo de vinculación

def test_flujo_completo(armar):
    cliente, ollama, _ = armar(autenticado=False)
    s = solicitar(cliente).json()
    assert len(s["codigo"]) == 9 and s["codigo"][4] == "-" and s["expira_en_s"] == 600
    assert sondear(cliente, s).json() == {"estado": "pendiente"}
    cliente.registro.resolver(s["codigo"].lower().replace("-", ""), aprobar=True)  # se dicta sin guion ni mayúsculas
    r = sondear(cliente, s).json()
    assert r["estado"] == "aprobada" and len(r["token"]) >= 40
    assert sondear(cliente, s).json() == {"estado": "entregada"}  # el token se entrega UNA vez
    yo = cliente.get("/api/v1/yo", headers={"Authorization": f"Bearer {r['token']}"}).json()
    assert yo["dispositivo_id"] == "laptop-profesor-0001" and yo["nombre"] == "Laptop del profesor"
    assert analizar(cliente, r["token"]).status_code == 200


def test_el_registro_no_guarda_tokens_ni_secretos(armar):
    cliente, *_ = armar(autenticado=False)
    s = solicitar(cliente).json()
    cliente.registro.resolver(s["codigo"], aprobar=True)
    token = sondear(cliente, s).json()["token"]
    contenido = cliente.registro.archivo.read_text(encoding="utf-8")
    assert token not in contenido and s["secreto"] not in contenido


def test_rechazada(armar):
    cliente, *_ = armar(autenticado=False)
    s = solicitar(cliente).json()
    cliente.registro.resolver(s["codigo"], aprobar=False)
    assert sondear(cliente, s).json() == {"estado": "rechazada"}


def test_secreto_incorrecto_y_anulacion(armar):
    cliente, *_ = armar(autenticado=False)
    s = solicitar(cliente).json()
    for _ in range(10):
        assert sondear(cliente, s, secreto="equivocado-123").status_code == 401
    cliente.registro.resolver  # tras 10 fallos la solicitud queda anulada: ya no se puede aprobar
    with pytest.raises(ErrorVinculacion):
        cliente.registro.resolver(s["codigo"], aprobar=True)
    assert sondear(cliente, s).json() == {"estado": "anulada"}


def test_caduca(tmp_path):
    reloj = [1000.0]
    r = Registro(tmp_path, ahora=lambda: reloj[0])
    s = r.solicitar("laptop-0000001", "x")
    reloj[0] += 601
    assert r.sondear(s["solicitud_id"], s["secreto"]) == {"estado": "expirada"}
    with pytest.raises(ErrorVinculacion):
        r.resolver(s["codigo"], aprobar=True)


def test_limite_de_pendientes(armar):
    cliente, *_ = armar(autenticado=False)
    for i in range(MAX_PENDIENTES):
        assert solicitar(cliente, f"dispositivo-{i:04d}").status_code == 201
    r = solicitar(cliente, "dispositivo-9999")
    assert (r.status_code, r.json()["error"]["codigo"]) == (429, "DEMASIADAS_SOLICITUDES") and r.headers["Retry-After"]


@pytest.mark.parametrize("cuerpo, estado", [
    ({"dispositivo_id": "corto", "nombre": "x"}, 400),
    ({"dispositivo_id": "../../etc/passwd", "nombre": "x"}, 400),
    ({"nombre": "sin id"}, 400),
])
def test_datos_invalidos(armar, cuerpo, estado):
    cliente, *_ = armar(autenticado=False)
    assert cliente.post("/api/v1/vinculacion/solicitudes", json=cuerpo).status_code == estado


def test_cuerpo_enorme(armar):
    cliente, *_ = armar(autenticado=False)
    r = cliente.post("/api/v1/vinculacion/solicitudes", content=json.dumps({"dispositivo_id": "a" * 20, "nombre": "x" * 5000}),
                     headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_nombre_saneado(armar):
    cliente, *_ = armar(autenticado=False)
    s = solicitar(cliente, nombre="<script>alert(1)</script>\x00 Laptop").json()
    assert "<" not in cliente.registro.pendientes()[0]["nombre"] and s["codigo"]


# ---------------------------------------------------------------------------- revocación y revinculación

def test_revocar(armar):
    cliente, *_ = armar(autenticado=False)
    token = vincular(cliente, cliente.registro)
    assert cliente.registro.revocar("laptop-profesor-0001") == 1
    r = analizar(cliente, token)
    assert (r.status_code, r.json()["error"]["codigo"]) == (403, "DISPOSITIVO_REVOCADO")


def test_revincular_invalida_el_token_anterior(armar):
    cliente, *_ = armar(autenticado=False)
    viejo = vincular(cliente, cliente.registro)
    nuevo = vincular(cliente, cliente.registro)
    assert analizar(cliente, viejo).status_code == 401
    assert analizar(cliente, nuevo).status_code == 200


def test_solicitudes_concurrentes_no_se_pisan(armar):
    cliente, *_ = armar(autenticado=False)
    codigos = []
    hilos = [threading.Thread(target=lambda i=i: codigos.append(solicitar(cliente, f"concurrente-{i:03d}").json()["codigo"]))
             for i in range(4)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert len(set(codigos)) == 4 and len(cliente.registro.pendientes()) == 4


def test_el_cerrojo_aguanta_mucha_contencion(tmp_path):
    # En Windows, crear el cerrojo mientras otro hilo lo borra daba PermissionError (visto en CI).
    from ia_servidor.dispositivos import Registro
    registro, errores = Registro(tmp_path), []

    def golpear():
        for _ in range(100):
            try:
                with registro._bloqueo():
                    pass
            except Exception as exc:  # noqa: BLE001
                errores.append(repr(exc))

    hilos = [threading.Thread(target=golpear) for _ in range(8)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert errores == []


# ---------------------------------------------------------------------------- límites y administración

def test_limite_por_dispositivo(armar):
    cliente, *_ = armar(max_analisis_min=2)
    assert [analizar(cliente).status_code for _ in range(2)] == [200, 200]
    r = analizar(cliente)
    assert (r.status_code, r.json()["error"]["codigo"], r.headers["Retry-After"]) == (429, "LIMITE_PETICIONES", "60")


def test_token_de_administrador_local(armar):
    cliente, *_ = armar(autenticado=False, max_analisis_min=1)
    admin_token = cliente.registro.token_admin()
    assert [analizar(cliente, admin_token).status_code for _ in range(3)] == [200, 200, 200]  # sin límite


def test_consola_de_administracion(armar, monkeypatch, capsys):
    cliente, *_ = armar(autenticado=False)
    monkeypatch.setenv("IA_DATOS", str(cliente.registro.carpeta))
    s = solicitar(cliente).json()
    assert admin.main(["pendientes"]) == 0 and s["codigo"] in capsys.readouterr().out
    assert admin.main(["aprobar", s["codigo"]]) == 0
    assert sondear(cliente, s).json()["estado"] == "aprobada"
    assert admin.main(["aprobar", "ZZZZ-ZZZZ"]) == 1
    assert admin.main(["revocar", "laptop-profesor-0001"]) == 0
    assert "REVOCADO" in (admin.main(["dispositivos"]) or capsys.readouterr().out)


@pytest.mark.parametrize("host, valido", [("127.0.0.1", True), ("100.101.102.103", True), ("0.0.0.0", False),
                                          ("192.168.1.10", False), ("::", False)])
def test_hosts_permitidos(host, valido):
    if valido:
        Configuracion(host=host).validar()
    else:
        with pytest.raises(ConfiguracionInvalida):
            Configuracion(host=host).validar()
