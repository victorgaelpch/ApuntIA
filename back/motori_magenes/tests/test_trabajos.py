"""Gestor de trabajos durables (BACK-27)."""

import threading
import time

import pytest

from app.core.errores import ApiError
from app.datos.bd import ahora
from app.services.trabajos import ErrorTrabajo, GestorTrabajos, Resultado


def esperar(gestor, uid, tid, estados=("completado", "fallido", "cancelado", "parcial"), limite=10):
    fin = time.time() + limite
    while time.time() < fin:
        t = gestor.obtener(uid, tid)
        if t["estado"] in estados:
            return t
        time.sleep(0.05)
    raise AssertionError(f"el trabajo no terminó: {gestor.obtener(uid, tid)}")


@pytest.fixture
def entorno(datos_tmp):
    bd = datos_tmp.bd
    for uid in ("u1", "u2"):
        bd.ejecutar("INSERT INTO usuarios (id, email, nombre, hash_password, creado, actualizado) "
                    "VALUES (?, ?, 'x', 'h', ?, ?)", (uid, f"{uid}@x.com", ahora(), ahora()))
    gestor = GestorTrabajos(bd, simultaneos=2, intervalo=0.05)
    liberar = threading.Event()
    ejecuciones = []

    def ok(t):
        ejecuciones.append(t.id)
        t.avance("ocr", 50)
        return Resultado(datos={"x": t.parametros.get("x")})

    def falla(t):
        raise ErrorTrabajo("OCR_NO_DISPONIBLE", "Tesseract no está instalado.")

    def explota(t):
        raise RuntimeError("detalle interno /ruta/secreta")

    def lento(t):
        for i in range(200):
            t.avance("procesando", i)
            if liberar.wait(0.02):
                break
        return Resultado()

    limpiados = []
    gestor.registrar("ok", ok)
    gestor.registrar("falla", falla)
    gestor.registrar("explota", explota)
    gestor.registrar("lento", lento, al_cancelar=lambda t: limpiados.append(t.id))
    gestor.registrar("parcial", lambda t: Resultado(estado="parcial", aviso="La página 2 no se pudo leer."))
    yield gestor, liberar, ejecuciones, limpiados
    liberar.set()
    gestor.detener()


def test_completa_con_resultado(entorno):
    gestor, *_ = entorno
    t = gestor.encolar("u1", "ok", parametros={"x": 7})
    assert t["estado"] == "pendiente"
    fin = esperar(gestor, "u1", t["id"])
    assert fin["estado"] == "completado" and fin["progreso"] == 100 and fin["resultado"] == {"x": 7}


def test_fallo_previsto_y_fallo_inesperado_sin_trazas(entorno):
    gestor, *_ = entorno
    f = esperar(gestor, "u1", gestor.encolar("u1", "falla")["id"])
    assert f["estado"] == "fallido" and f["error"]["codigo"] == "OCR_NO_DISPONIBLE"
    e = esperar(gestor, "u1", gestor.encolar("u1", "explota")["id"])
    assert e["error"]["codigo"] == "ERROR_INTERNO" and "secreta" not in e["error"]["mensaje"]
    assert len(e["error"]["referencia"]) == 12


def test_parcial_no_es_completado(entorno):
    gestor, *_ = entorno
    p = esperar(gestor, "u1", gestor.encolar("u1", "parcial")["id"])
    assert p["estado"] == "parcial" and "página 2" in p["error"]["mensaje"]


def test_cancelar_en_curso_limpia(entorno):
    gestor, _, _, limpiados = entorno
    t = gestor.encolar("u1", "lento")
    esperar(gestor, "u1", t["id"], estados=("procesando",))
    gestor.cancelar("u1", t["id"])
    assert esperar(gestor, "u1", t["id"])["estado"] == "cancelado"
    assert limpiados == [t["id"]]


def test_reintentar_no_duplica(entorno, datos_tmp):
    gestor, *_ = entorno
    t = esperar(gestor, "u1", gestor.encolar("u1", "falla")["id"])
    gestor.registrar("falla", lambda tr: Resultado(datos={"ok": True}))
    r = gestor.reintentar("u1", t["id"])
    assert r["id"] == t["id"]
    assert esperar(gestor, "u1", t["id"])["estado"] == "completado"
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM trabajos")["n"] == 1
    with pytest.raises(ApiError) as exc:
        gestor.reintentar("u1", t["id"])
    assert exc.value.codigo == "TRABAJO_NO_REINTENTABLE"


def test_limite_por_usuario_y_aislamiento(entorno):
    gestor, liberar, *_ = entorno
    for _ in range(3):
        gestor.encolar("u1", "lento")
    with pytest.raises(ApiError) as exc:
        gestor.encolar("u1", "lento")
    assert exc.value.status_code == 429 and exc.value.codigo == "DEMASIADOS_TRABAJOS"
    t2 = gestor.encolar("u2", "ok")  # otro usuario no se ve afectado
    with pytest.raises(ApiError) as exc:
        gestor.obtener("u1", t2["id"])
    assert exc.value.status_code == 404
    liberar.set()


def test_concurrencia_limitada(entorno, datos_tmp):
    gestor, liberar, *_ = entorno
    ids = [gestor.encolar(u, "lento")["id"] for u in ("u1", "u1", "u2")]
    time.sleep(0.4)
    procesando = datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM trabajos WHERE estado = 'procesando'")["n"]
    assert procesando == 2  # MAX_TRABAJOS_SIMULTANEOS
    liberar.set()
    for tid, uid in zip(ids, ("u1", "u1", "u2")):
        assert esperar(gestor, uid, tid)["estado"] == "completado"


def test_recuperacion_tras_reinicio(datos_tmp):
    bd = datos_tmp.bd
    bd.ejecutar("INSERT INTO usuarios (id, email, nombre, hash_password, creado, actualizado) "
                "VALUES ('u1', 'a@x.com', 'x', 'h', ?, ?)", (ahora(), ahora()))
    for tid, intentos in (("t1", 1), ("t2", 3)):
        bd.ejecutar("INSERT INTO trabajos (id, usuario_id, tipo, estado, intentos, creado, actualizado) "
                    "VALUES (?, 'u1', 'ok', 'procesando', ?, ?, ?)", (tid, intentos, ahora(), ahora()))
    gestor = GestorTrabajos(bd, intervalo=0.05)
    gestor.registrar("ok", lambda t: Resultado())
    gestor.iniciar()
    try:
        assert esperar(gestor, "u1", "t1")["estado"] == "completado"   # se reencoló
        t2 = gestor.obtener("u1", "t2")
        assert t2["estado"] == "fallido" and t2["error"]["codigo"] == "INTERRUMPIDO"
    finally:
        gestor.detener()


def test_api_de_trabajos(nuevo_cliente, datos_tmp):
    c = nuevo_cliente()
    usuario = c.registrar()
    datos_tmp.trabajos.registrar("ok", lambda t: Resultado(datos={"listo": True}))
    t = datos_tmp.trabajos.encolar(usuario["id"], "ok")
    esperar(datos_tmp.trabajos, usuario["id"], t["id"])
    assert c.get(f"/api/v2/trabajos/{t['id']}").json()["trabajo"]["estado"] == "completado"
    otro = nuevo_cliente()
    otro.registrar("b@example.com")
    assert otro.get(f"/api/v2/trabajos/{t['id']}").status_code == 404
    assert otro.delete(f"/api/v2/trabajos/{t['id']}").status_code == 404
    assert c.post(f"/api/v2/trabajos/{t['id']}/reintentar").json()["error"]["codigo"] == "TRABAJO_NO_REINTENTABLE"


def test_log_de_correlacion_sin_datos_privados(entorno, caplog):
    import logging
    gestor, *_ = entorno
    uid = "u1"
    caplog.set_level(logging.INFO, logger="apuntia.trabajos")
    gestor.registrar("eco", lambda t: Resultado("completado", {"version": 7, "texto": "secreto del apunte"}))
    t = gestor.encolar(uid, "eco", parametros={"conceptos": ["privado"]})
    esperar(gestor, uid, t["id"])
    linea = next(r.getMessage() for r in caplog.records if f"trabajo={t['id']}" in r.getMessage())
    assert "tipo=eco" in linea and "version=7" in linea and "estado=completado" in linea and "ms=" in linea
    assert "secreto" not in caplog.text and "privado" not in caplog.text
