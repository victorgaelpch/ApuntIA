"""Cola asíncrona de trabajos del servidor IA (BACK-37). Sin GPU: Ollama simulado."""

import threading
import time

import cv2

from conftest import OllamaFalso, png, vincular
from ia_servidor.errores import ErrorIA
from ia_servidor.trabajos import ColaTrabajos

import pytest


def crear(cliente, clave=None, tarea="formula"):
    cab = {"Content-Type": "image/png", **({"Idempotency-Key": clave} if clave else {})}
    return cliente.post(f"/api/v1/trabajos?tarea={tarea}", content=png(), headers=cab)


def esperar(cliente, tid, limite=10):
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        r = cliente.get(f"/api/v1/trabajos/{tid}").json()
        if r["estado"] in ("completado", "fallido", "cancelado"):
            return r
        time.sleep(0.05)
    raise AssertionError("no terminó")


def test_trabajo_asincrono_completo(armar):
    cliente, ollama, _ = armar()
    r = crear(cliente, "apunte1/p1/v1")
    assert r.status_code == 202 and r.json()["estado"] in ("en_cola", "procesando")
    fin = esperar(cliente, r.json()["trabajo_id"])
    assert fin["estado"] == "completado" and fin["progreso"] == 100
    assert fin["resultado"]["resultado"]["latex"] and len(ollama.chats()) == 1


def test_misma_clave_no_repite_la_gpu(armar):
    cliente, ollama, _ = armar()
    a = crear(cliente, "apunte1/p1/v1").json()
    esperar(cliente, a["trabajo_id"])
    b = crear(cliente, "apunte1/p1/v1")
    assert b.status_code == 200 and b.json()["trabajo_id"] == a["trabajo_id"] and b.json()["estado"] == "completado"
    assert len(ollama.chats()) == 1                      # ninguna inferencia nueva


def test_otro_dispositivo_no_ve_el_trabajo(armar):
    cliente, *_ = armar()
    tid = crear(cliente).json()["trabajo_id"]
    otro = vincular(cliente, cliente.registro, dispositivo_id="otra-laptop-0002", nombre="Otra")
    r = cliente.get(f"/api/v1/trabajos/{tid}", headers={"Authorization": f"Bearer {otro}"})
    assert (r.status_code, r.json()["error"]["codigo"]) == (404, "TRABAJO_NO_ENCONTRADO")


def test_trabajo_inexistente(armar):
    r = armar()[0].get("/api/v1/trabajos/no-existe")
    assert r.status_code == 404 and r.json()["error"]["reintentable"] is False


def test_requiere_credencial(armar):
    cliente, *_ = armar(autenticado=False)
    assert crear(cliente).status_code == 401


def test_fallo_del_modelo_queda_en_el_trabajo(armar):
    cliente, *_ = armar(OllamaFalso(chat=[(404, '{"error":"model not found"}')]))
    fin = esperar(cliente, crear(cliente).json()["trabajo_id"])
    assert fin["estado"] == "fallido" and fin["error"]["codigo"] == "MODELO_NO_INSTALADO"


def test_tras_un_fallo_la_misma_clave_crea_otro_trabajo(armar):
    cliente, *_ = armar(OllamaFalso(chat=[(404, '{"error":"model not found"}'), "x^2"]))
    a = crear(cliente, "k1").json()
    esperar(cliente, a["trabajo_id"])
    b = crear(cliente, "k1").json()
    assert b["trabajo_id"] != a["trabajo_id"] and esperar(cliente, b["trabajo_id"])["estado"] == "completado"


# ---------------------------------------------------------------------------- cola en aislamiento (sin hilo)

class ServicioLento:
    def __init__(self):
        self.liberar = threading.Event()
        self.llamadas = 0

    def analizar(self, datos, tarea, id_correlacion, progreso=None):
        self.llamadas += 1
        for i in range(1, 4):
            self.liberar.wait(2)
            if progreso:
                progreso(i, 3)
        return {"resultado": {"texto": "ok"}}


def test_cola_llena_429():
    cola = ColaTrabajos(ServicioLento(), max_cola=2)
    cola.iniciar = lambda: None                          # sin trabajador: los trabajos se quedan en cola
    cola.encolar("d", "documento", b"x", None)
    cola.encolar("d", "documento", b"x", None)
    with pytest.raises(ErrorIA) as e:
        cola.encolar("d", "documento", b"x", None)
    assert e.value.codigo == "OCUPADO" and e.value.estado == 429


def test_posicion_y_cancelacion_en_cola():
    cola = ColaTrabajos(ServicioLento())
    cola.iniciar = lambda: None
    a, _ = cola.encolar("d", "documento", b"x", None)
    b, _ = cola.encolar("d", "documento", b"x", None)
    assert cola.obtener("d", b.id)[1] == 2
    assert cola.cancelar("d", a.id).estado == "cancelado" and a.datos is None   # imagen liberada
    assert cola.obtener("d", b.id)[1] == 1


def test_cancelar_mientras_procesa():
    servicio = ServicioLento()
    cola = ColaTrabajos(servicio)
    cola.iniciar = lambda: None
    t, _ = cola.encolar("d", "documento", b"x", None)
    cola.cola.popleft()
    t.estado = "procesando"
    hilo = threading.Thread(target=cola.procesar, args=(t,))
    hilo.start()
    cola.cancelar("d", t.id)
    servicio.liberar.set()
    hilo.join(5)
    assert t.estado == "cancelado" and t.resultado is None


def test_progreso_honesto():
    servicio = ServicioLento()
    servicio.liberar.set()
    cola = ColaTrabajos(servicio)
    cola.iniciar = lambda: None
    t, _ = cola.encolar("d", "documento", b"x", None)
    cola.cola.popleft()
    vistos = []
    original = servicio.analizar

    def espiar(datos, tarea, idc, progreso=None):
        return original(datos, tarea, idc, progreso=lambda h, n: (progreso(h, n), vistos.append(t.progreso)))
    servicio.analizar = espiar
    cola.procesar(t)
    assert vistos == [33, 66, 100] and t.estado == "completado"


def test_resultados_caducan():
    reloj = [1000.0]
    servicio = ServicioLento()
    servicio.liberar.set()
    cola = ColaTrabajos(servicio, ttl_s=60, ahora=lambda: reloj[0])
    cola.iniciar = lambda: None
    t, _ = cola.encolar("d", "documento", b"x", None)
    cola.cola.popleft()
    cola.procesar(t)
    reloj[0] += 61
    with pytest.raises(ErrorIA):
        cola.obtener("d", t.id)
