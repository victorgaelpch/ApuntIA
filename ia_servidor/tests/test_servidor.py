"""Pruebas del servidor IA con Ollama simulado (BACK-35). Sin red, sin GPU y sin modelos."""

import logging
import socket
import subprocess
import sys
import threading
import urllib.error
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from conftest import RESPUESTA_OK, OllamaFalso, png
from ia_servidor import API_VERSION, gpu
from ia_servidor.config import Configuracion, ConfiguracionInvalida

RAIZ = Path(__file__).resolve().parents[2]


def analizar(cliente, datos, tarea="formula", tipo="image/png"):
    return cliente.post(f"/api/v1/analisis?tarea={tarea}", content=datos, headers={"Content-Type": tipo})


# ---------------------------------------------------------------------------- estado

def test_salud_sin_datos_sensibles(armar):
    cliente, *_ = armar()
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "servicio": "apuntia-ia", "api_version": API_VERSION}
    assert r.headers["X-ApuntIA-Id-Correlacion"]


def test_listo_con_todo_correcto(armar):
    cliente, *_ = armar()
    r = cliente.get("/listo")
    assert r.status_code == 200, r.json()
    c = r.json()["componentes"]
    assert c["ollama"]["ok"] and c["modelo"]["ok"] and c["gpu"]["disponible"]
    assert c["modelo"]["cuantizacion"] == "Q4_K_M"


@pytest.mark.parametrize("ollama, motivo", [
    (OllamaFalso(modelos=()), "ollama pull qwen3-vl:8b-instruct"),
    (OllamaFalso(version="0.11.4"), "0.12.7"),
    (OllamaFalso(capacidades=("completion",)), "vision"),
])
def test_listo_falla_con_causa(armar, ollama, motivo):
    r = armar(ollama)[0].get("/listo")
    assert r.status_code == 503
    assert motivo in str(r.json()["componentes"])


def test_listo_sin_ollama(armar):
    def caido(*_):
        raise urllib.error.URLError(ConnectionRefusedError())
    r = armar(caido)[0].get("/listo")
    assert r.status_code == 503
    assert r.json()["componentes"]["ollama"]["codigo"] == "NO_DISPONIBLE"


def test_capacidades(armar):
    r = armar()[0].get("/api/v1/capacidades").json()
    assert {"formula", "texto_manuscrito", "tabla", "diagrama", "pagina"} <= set(r["tareas"])
    assert r["limites"]["inferencias_simultaneas"] == 1
    assert r["modelo"] == {"principal": "qwen3-vl:8b-instruct", "respaldo": "qwen3-vl:4b-instruct"}


# ---------------------------------------------------------------------------- análisis

def test_analisis_valido_devuelve_contrato(armar):
    cliente, ollama, _ = armar()
    r = analizar(cliente, png())
    assert r.status_code == 200, r.json()
    j = r.json()
    assert j["api_version"] == API_VERSION and j["pipeline_version"] and j["id_correlacion"] == r.headers["X-ApuntIA-Id-Correlacion"]
    assert j["resultado"] == {"estado": "propuesta", "revision_requerida": True, "origen": "imagen",
                              "texto": RESPUESTA_OK, "latex": RESPUESTA_OK, "descripcion": None,
                              "dudas": ["1 fragmento(s) que el modelo marcó como no legibles ([?])"]}
    assert j["modelo"] == {"nombre": "qwen3-vl:8b-instruct", "respaldo_usado": False}
    assert j["imagen"]["formato"] == "png" and j["imagen"]["ancho"] == 640
    assert j["calidad"]["disponible"] is True and j["calidad"]["nivel"] in {"buena", "aceptable", "insuficiente"}
    assert "confianza" not in str(j["resultado"])  # un VLM no da confianza calibrada: no se inventa
    chat = ollama.chats()[0]
    assert chat["model"] == "qwen3-vl:8b-instruct" and chat["stream"] is False and chat["options"]["temperature"] == 0
    assert "format" not in chat and len(chat["messages"][0]["images"]) == 1  # un esquema dispara el razonamiento
    assert len(chat["messages"][0]["content"]) < 400 and "LaTeX" in chat["messages"][0]["content"]  # prompt corto
    assert chat["options"]["num_ctx"] == 8192 and chat["options"]["num_predict"] == 2048  # siempre acotado


def test_imagen_grande_se_reduce_para_el_modelo(armar):
    cliente, *_ = armar(max_lado_modelo=800)
    j = analizar(cliente, png(2400, 1200)).json()
    assert j["imagen"]["ancho"] == 2400 and j["imagen"]["lado_enviado_al_modelo"] == 800


def test_ilegible(armar):
    cliente, *_ = armar(OllamaFalso(chat=["[ilegible]"]))
    assert analizar(cliente, png()).json()["resultado"]["estado"] == "ilegible"


def test_una_sola_llamada_al_modelo(armar):
    cliente, ollama, _ = armar()
    assert analizar(cliente, png()).status_code == 200
    assert len(ollama.chats()) == 1


def test_respuesta_demasiado_larga_es_invalida_y_no_guarda_basura(armar):
    cliente, *_ = armar(OllamaFalso(chat=["x" * 30001]))
    r = analizar(cliente, png(), tarea="texto_impreso")
    assert r.status_code == 502
    assert r.json()["error"]["codigo"] == "RESPUESTA_INVALIDA" and r.json()["error"]["reintentable"] is True


def test_oom_usa_el_respaldo_si_esta_instalado(armar):
    ollama = OllamaFalso(chat=[(500, '{"error":"CUDA error: out of memory"}'), RESPUESTA_OK],
                         modelos=("qwen3-vl:8b-instruct", "qwen3-vl:4b-instruct"))
    cliente, *_ = armar(ollama)
    j = analizar(cliente, png()).json()
    assert j["modelo"] == {"nombre": "qwen3-vl:4b-instruct", "respaldo_usado": True}
    assert [c["model"] for c in ollama.chats()] == ["qwen3-vl:8b-instruct", "qwen3-vl:4b-instruct"]


def test_oom_sin_respaldo_es_reintentable(armar):
    cliente, *_ = armar(OllamaFalso(chat=[(500, '{"error":"model requires more system memory"}')]))
    r = analizar(cliente, png())
    assert r.status_code == 503
    assert r.json()["error"] | {"id_correlacion": None} == {
        "codigo": "SIN_MEMORIA", "mensaje": r.json()["error"]["mensaje"], "reintentable": True, "id_correlacion": None}


def test_modelo_no_instalado(armar):
    cliente, *_ = armar(OllamaFalso(chat=[(404, '{"error":"model \\"qwen3-vl:8b-instruct\\" not found, try pulling it first"}')]))
    r = analizar(cliente, png())
    assert (r.status_code, r.json()["error"]["codigo"], r.json()["error"]["reintentable"]) == (503, "MODELO_NO_INSTALADO", False)


def test_ollama_caido_y_timeout(armar):
    cliente, *_ = armar(OllamaFalso(chat=[urllib.error.URLError(ConnectionRefusedError())]))
    assert analizar(cliente, png()).json()["error"]["codigo"] == "NO_DISPONIBLE"
    cliente, *_ = armar(OllamaFalso(chat=[socket.timeout()]))
    r = analizar(cliente, png())
    assert (r.status_code, r.json()["error"]["codigo"]) == (504, "TIEMPO_AGOTADO")


def test_respuesta_cortada_por_longitud(armar):
    class Cortado(OllamaFalso):
        def __call__(self, metodo, url, cuerpo, timeout):
            estado, datos = super().__call__(metodo, url, cuerpo, timeout)
            return estado, datos.replace(b'"done_reason": "stop"', b'"done_reason": "length"')
    r = analizar(armar(Cortado())[0], png())
    assert r.json()["error"]["codigo"] == "RESPUESTA_INVALIDA"


# ---------------------------------------------------------------------------- entradas inválidas

@pytest.mark.parametrize("datos, estado, codigo", [
    (b"", 400, "IMAGEN_VACIA"),
    (b"%PDF-1.7 no es una imagen", 415, "FORMATO_NO_SOPORTADO"),
    (b"\x89PNG\r\n\x1a\n" + b"\x00" * 50, 400, "IMAGEN_CORRUPTA"),
    (b"GIF89a" + b"\x00" * 20, 415, "FORMATO_NO_SOPORTADO"),
])
def test_entradas_invalidas(armar, datos, estado, codigo):
    cliente, ollama, _ = armar()
    r = analizar(cliente, datos)
    assert (r.status_code, r.json()["error"]["codigo"]) == (estado, codigo)
    assert ollama.chats() == []  # nunca llega al modelo


def test_tarea_invalida(armar):
    r = analizar(armar()[0], png(), tarea="borrar_todo")
    assert (r.status_code, r.json()["error"]["codigo"]) == (400, "TAREA_INVALIDA")


def test_limite_de_tamano(armar):
    cliente, ollama, _ = armar(max_mb=1)
    r = analizar(cliente, b"\x89PNG\r\n\x1a\n" + b"\x00" * (1024 * 1024 + 10))
    assert (r.status_code, r.json()["error"]["codigo"]) == (413, "IMAGEN_DEMASIADO_GRANDE")


def test_bomba_de_descompresion_se_rechaza_por_cabecera(armar):
    # PNG válido de 20000×20000 (400 MP) que pesa poco: se rechaza sin decodificar los píxeles.
    buf = BytesIO()
    Image.new("1", (20000, 20000)).save(buf, "PNG")
    assert len(buf.getvalue()) < 1024 * 1024
    r = analizar(armar()[0], buf.getvalue())
    assert (r.status_code, r.json()["error"]["codigo"]) == (413, "RESOLUCION_EXCESIVA")


def test_multipart_no_se_acepta(armar):
    r = armar()[0].post("/api/v1/analisis", files={"imagen": ("a.png", png(), "image/png")})
    assert r.json()["error"]["codigo"] == "FALTA_IMAGEN"


def test_ruta_desconocida_con_formato_de_error(armar):
    r = armar()[0].get("/api/pull")
    assert r.status_code == 404 and r.json()["error"]["codigo"] == "RUTA_NO_ENCONTRADA"


# ---------------------------------------------------------------------------- concurrencia y seguridad

def test_cola_llena_devuelve_429_con_retry_after(armar):
    cliente, _, servicio = armar(espera_cola_s=0)
    servicio._turnos.acquire()  # otra inferencia en curso
    try:
        r = analizar(cliente, png())
    finally:
        servicio._turnos.release()
    assert (r.status_code, r.json()["error"]["codigo"]) == (429, "OCUPADO")
    assert int(r.headers["Retry-After"]) >= 5


def test_una_sola_inferencia_a_la_vez(armar):
    activas, maximo, cerrojo = [0], [0], threading.Lock()

    class Lento(OllamaFalso):
        def __call__(self, metodo, url, cuerpo, timeout):
            if url.endswith("/api/chat"):
                with cerrojo:
                    activas[0] += 1
                    maximo[0] = max(maximo[0], activas[0])
                threading.Event().wait(0.2)
                with cerrojo:
                    activas[0] -= 1
            return super().__call__(metodo, url, cuerpo, timeout)

    cliente, *_ = armar(Lento(chat=[RESPUESTA_OK] * 3))
    hilos = [threading.Thread(target=analizar, args=(cliente, png())) for _ in range(3)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert maximo[0] == 1


def test_solo_rutas_de_ollama_permitidas(armar):
    _, ollama, servicio = armar()
    from ia_servidor.errores import ErrorIA
    with pytest.raises(ErrorIA):
        servicio.ollama._pedir("/api/pull", {"model": "x"})
    assert not any(r in ("/api/pull", "/api/delete", "/api/create") for _, r, _ in ollama.peticiones)


def test_logs_sin_contenido_de_la_imagen(armar, caplog):
    cliente, *_ = armar()
    with caplog.at_level(logging.INFO, logger="apuntia.ia"):
        analizar(cliente, png())
    texto = caplog.text
    assert "caracteres=" in texto
    assert "frac" not in texto and "m[?]" not in texto and "iVBOR" not in texto


@pytest.mark.parametrize("cambios, mensaje", [
    ({"host": "0.0.0.0"}, "solo escucha en 127.0.0.1"),
    ({"host": "192.168.1.10"}, "solo escucha en 127.0.0.1"),
    ({"ollama_url": "http://192.168.1.5:11434"}, "Ollama nunca se usa"),
    ({"ollama_url": "http://usuario:clave@127.0.0.1:11434"}, "credenciales"),
    ({"modelo": "qwen3-vl:235b-cloud"}, "cloud"),
    ({"modelo": "qwen3 vl; rm"}, "formato"),
    ({"keep_alive": "para siempre"}, "IA_KEEP_ALIVE"),
])
def test_configuracion_insegura_no_arranca(cambios, mensaje):
    with pytest.raises(ConfiguracionInvalida, match=mensaje):
        Configuracion(**cambios).validar()


def test_configuracion_desde_entorno(monkeypatch):
    monkeypatch.setenv("IA_MAX_INFERENCIAS", "9")
    with pytest.raises(ConfiguracionInvalida, match="entre 1 y 4"):
        Configuracion.desde_entorno()
    monkeypatch.setenv("IA_MAX_INFERENCIAS", "2")
    assert Configuracion.desde_entorno().max_inferencias == 2


def test_no_importa_bd_ni_config_del_cliente():
    """El OpenCV compartido no arrastra la base de datos, las cuentas ni la configuración del cliente."""
    codigo = ("import sys, ia_servidor.app; "
              "malos = [m for m in sys.modules if m.startswith(('app.datos', 'app.core.config', 'app.services.cuentas', "
              "'app.routers', 'sqlite3'))]; "
              "assert 'app.services.calidad' in sys.modules; print(malos); assert not malos, malos")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout


def test_gpu_lee_nvidia_smi_simulado():
    class R:
        returncode, stdout = 0, "NVIDIA GeForce RTX 3060, 560.94, 12288, 812, 11476\n"
    info = gpu.leer(ejecutar=lambda *a, **k: R(), cache_s=0)
    assert info["gpus"][0]["vram_total_mb"] == 12288 and info["disponible"]
    falla = gpu.leer(ejecutar=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()), cache_s=0)
    assert falla["disponible"] is False
