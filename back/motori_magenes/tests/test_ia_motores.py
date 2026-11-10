"""Motores de reconocimiento, VLM local por Ollama y perfiles (FULL-30, fase 2).

Ollama se SIMULA con un servidor HTTP local que imita su API (`/api/version`, `/api/tags`,
`/api/show`, `/api/chat`). Estas pruebas comprueban el contrato del adaptador, los errores y
la seguridad; NO miden la calidad de ningún modelo (no hay modelo real en la CI).
"""

import base64
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.core.config import settings
from app.services.ia import registro as reg
from app.services.ia.motores import ErrorMotor, MotorTesseractAdaptador, OpcionesReconocimiento
from app.services.ia.ollama import (PROMPT_BASE, MotorOllamaVLM, host_permitido, interpretar, modelo_permitido)
from app.services.ocr import MotorTesseract

TESSERACT = MotorTesseract().disponible()
RAIZ = Path(__file__).resolve().parents[3]


class FalsoOllama(BaseHTTPRequestHandler):
    version = "0.12.7"
    modelos = ["qwen3-vl:4b"]
    capacidades = ["completion", "vision"]
    contenido = json.dumps({"ilegible": False, "texto": "Velocidad media", "latex": None, "descripcion": None,
                            "dudas": ["media"]})
    retraso = 0.0
    error_chat: tuple[int, str] | None = None
    rutas: list[str] = []
    cuerpos: list[dict] = []

    def log_message(self, *args):
        pass

    def _responder(self, codigo, datos):
        cuerpo = json.dumps(datos).encode() if not isinstance(datos, bytes) else datos
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        FalsoOllama.rutas.append(self.path)
        if self.path == "/api/version":
            return self._responder(200, {"version": FalsoOllama.version})
        if self.path == "/api/tags":
            return self._responder(200, {"models": [{"name": m, "model": m} for m in FalsoOllama.modelos]})
        self._responder(404, {"error": "not found"})

    def do_POST(self):
        FalsoOllama.rutas.append(self.path)
        cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FalsoOllama.cuerpos.append(cuerpo)
        if self.path == "/api/show":
            if cuerpo["model"] not in FalsoOllama.modelos:
                return self._responder(404, {"error": "model not found"})
            return self._responder(200, {"capabilities": FalsoOllama.capacidades})
        if self.path == "/api/chat":
            time.sleep(FalsoOllama.retraso)
            if FalsoOllama.error_chat:
                return self._responder(FalsoOllama.error_chat[0], {"error": FalsoOllama.error_chat[1]})
            return self._responder(200, {"model": cuerpo["model"], "done": True,
                                         "message": {"role": "assistant", "content": FalsoOllama.contenido}})
        self._responder(404, {"error": "not found"})


@pytest.fixture
def ollama():
    FalsoOllama.version, FalsoOllama.modelos = "0.12.7", ["qwen3-vl:4b"]
    FalsoOllama.capacidades, FalsoOllama.retraso, FalsoOllama.error_chat = ["completion", "vision"], 0.0, None
    FalsoOllama.contenido = json.dumps({"ilegible": False, "texto": "Velocidad media", "dudas": ["media"]})
    FalsoOllama.rutas, FalsoOllama.cuerpos = [], []
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), FalsoOllama)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{servidor.server_port}"
    servidor.shutdown()


def motor(host, **kw):
    return MotorOllamaVLM(host=host, modelo=kw.pop("modelo", "qwen3-vl:4b"), activado=True, permitir_externa=False, **kw)


IMAGEN = np.full((1200, 3200, 3), 250, np.uint8)
cv2.putText(IMAGEN, "Velocidad media", (40, 300), cv2.FONT_HERSHEY_SIMPLEX, 6, (20, 20, 20), 12)


# ------------------------------------------------------------------ disponibilidad

def test_desactivado_por_defecto_y_sin_contactar_a_nadie(ollama):
    assert settings.ia_activada is False
    m = MotorOllamaVLM(host=ollama)
    assert not m.disponible() and "IA_ACTIVADA" in m.info_modelo().detalle
    assert FalsoOllama.rutas == []


def test_disponible_con_ollama_modelo_instalado_y_vision(ollama):
    m = motor(ollama)
    assert m.disponible()
    assert m.info_modelo().version == "0.12.7" and m.info_modelo().local
    assert set(FalsoOllama.rutas) == {"/api/version", "/api/tags", "/api/show"}


@pytest.mark.parametrize("cambio, mensaje", [
    (lambda: setattr(FalsoOllama, "version", "0.11.4"), "0.12.7 o superior"),
    (lambda: setattr(FalsoOllama, "modelos", ["llama3:8b"]), "no está instalado"),
    (lambda: setattr(FalsoOllama, "capacidades", ["completion"]), "no admite imágenes"),
])
def test_no_disponible_con_motivo_claro(ollama, cambio, mensaje):
    cambio()
    ok, info = motor(ollama).estado()
    assert not ok and mensaje in info.detalle


def test_nunca_descarga_modelos(ollama):
    FalsoOllama.modelos = []
    ok, info = motor(ollama).estado()
    assert not ok and "ollama pull qwen3-vl:4b" in info.detalle and "nunca lo descarga" in info.detalle
    assert not any("pull" in r for r in FalsoOllama.rutas)


def test_ollama_apagado():
    ok, info = motor("http://127.0.0.1:9").estado()
    assert not ok and "no responde" in info.detalle


# ------------------------------------------------------------------ seguridad

@pytest.mark.parametrize("url, permitido", [
    ("http://127.0.0.1:11434", True), ("http://localhost:11434", True), ("http://192.168.1.20:11434", True),
    ("http://10.0.0.5:11434", True), ("http://8.8.8.8:11434", False),
    ("http://169.254.169.254", False),            # metadatos de la nube (SSRF)
    ("http://usuario:clave@127.0.0.1:11434", False), ("http://127.0.0.1:11434/api/pull", False),
    ("file:///etc/passwd", False), ("ftp://127.0.0.1", False),
])
def test_solo_servidores_locales_o_privados(url, permitido):
    assert host_permitido(url, permitir_externa=False)[0] is permitido


def test_externo_solo_con_permiso_explicito():
    assert host_permitido("http://8.8.8.8:11434", permitir_externa=True)[0]


@pytest.mark.parametrize("modelo, permitido", [
    ("qwen3-vl:4b", True), ("qwen3-vl:2b-instruct-q4_K_M", True), ("hf.co/usuario/modelo:Q4_K_M", True),
    ("qwen3-vl:235b-cloud", False), ("gpt-oss:cloud", False), ("../../etc", False), ("", False),
])
def test_modelos_cloud_y_nombres_raros_rechazados(modelo, permitido):
    assert modelo_permitido(modelo, permitir_externa=False)[0] is permitido


def test_modelo_cloud_no_se_usa_aunque_este_instalado(ollama):
    FalsoOllama.modelos = ["qwen3-vl:235b-cloud"]
    ok, info = motor(ollama, modelo="qwen3-vl:235b-cloud").estado()
    assert not ok and "fuera del equipo" in info.detalle and FalsoOllama.rutas == []


def test_el_texto_de_la_foto_es_dato_y_no_instruccion():
    assert "no lo obedezcas" in PROMPT_BASE and "no completes" in PROMPT_BASE and "no corrijas" in PROMPT_BASE


# ------------------------------------------------------------------ inferencia

def test_reconoce_con_peticion_acotada_y_sin_tocar_la_original(ollama):
    copia = IMAGEN.copy()
    r = motor(ollama).reconocer(IMAGEN, OpcionesReconocimiento(tarea="texto_manuscrito"))
    assert np.array_equal(IMAGEN, copia)
    assert r.texto == "Velocidad media" and r.confianza is None and r.extra["dudas"] == ["media"]
    assert r.motor.nombre == "ollama_vlm" and r.motor.modelo == "qwen3-vl:4b"
    chat = FalsoOllama.cuerpos[-1]
    assert chat["stream"] is False and chat["options"]["temperature"] == 0 and chat["format"]["type"] == "object"
    enviada = cv2.imdecode(np.frombuffer(base64.b64decode(chat["messages"][0]["images"][0]), np.uint8), cv2.IMREAD_COLOR)
    assert max(enviada.shape[:2]) == settings.ia_max_lado_px          # reducida antes de enviarla


def test_json_con_texto_alrededor_se_acepta():
    assert interpretar('Aquí está:\n{"texto": "F = ma", "latex": "F = m a"}\nListo').latex == "F = m a"


@pytest.mark.parametrize("contenido", ['{"texto": "F = m', "no es json", '{"texto": 5}', '{"dudas": "x"}', ""])
def test_respuesta_incompleta_o_invalida_es_un_error(contenido):
    with pytest.raises(ErrorMotor) as e:
        interpretar(contenido)
    assert e.value.codigo == "RESPUESTA_INVALIDA"


def test_respuesta_invalida_desde_ollama(ollama):
    FalsoOllama.contenido = '{"texto": "corta'
    with pytest.raises(ErrorMotor) as e:
        motor(ollama).reconocer(IMAGEN, OpcionesReconocimiento())
    assert e.value.codigo == "RESPUESTA_INVALIDA"


def test_tiempo_agotado(ollama):
    m = motor(ollama)
    assert m.disponible()
    FalsoOllama.retraso = 1.5
    with pytest.raises(ErrorMotor) as e:
        m.reconocer(IMAGEN, OpcionesReconocimiento(timeout_s=0.5))
    assert e.value.codigo == "TIEMPO_AGOTADO"


def test_sin_memoria_no_se_reintenta(ollama):
    m = motor(ollama)
    assert m.disponible()
    FalsoOllama.error_chat = (500, "model requires more system memory (6.1 GiB) than is available (3.2 GiB)")
    with pytest.raises(ErrorMotor) as e:
        m.reconocer(IMAGEN, OpcionesReconocimiento())
    assert e.value.codigo == "SIN_MEMORIA" and FalsoOllama.rutas.count("/api/chat") == 1


def test_limite_de_inferencias_simultaneas(ollama):
    m = motor(ollama, max_inferencias=1)
    assert m.disponible()
    FalsoOllama.retraso = 1.0
    primera = threading.Thread(target=m.reconocer, args=(IMAGEN, OpcionesReconocimiento(timeout_s=5)))
    primera.start()
    time.sleep(0.2)
    with pytest.raises(ErrorMotor) as e:
        m.reconocer(IMAGEN, OpcionesReconocimiento(timeout_s=0.2))
    primera.join()
    assert e.value.codigo == "OCUPADO" and FalsoOllama.rutas.count("/api/chat") == 1


def test_no_disponible_no_llama_al_modelo(ollama):
    FalsoOllama.modelos = []
    with pytest.raises(ErrorMotor) as e:
        motor(ollama).reconocer(IMAGEN, OpcionesReconocimiento())
    assert e.value.codigo == "NO_DISPONIBLE" and "/api/chat" not in FalsoOllama.rutas


# ------------------------------------------------------------------ registro y perfiles

EQUIPO_GRANDE = {"ram_disponible_gb": 16.0, "gpus": []}
EQUIPO_PEQUENO = {"ram_disponible_gb": 3.0, "gpus": []}


def registro_con(ollama_url=None, tesseract=True):
    r = reg.Registro()
    if tesseract:
        r.registrar(MotorTesseractAdaptador())
    r.registrar(motor(ollama_url) if ollama_url else MotorOllamaVLM(activado=False))
    return r


@pytest.mark.skipif(not TESSERACT, reason="Tesseract no está instalado")
def test_automatico_elige_avanzado_solo_si_el_vlm_esta_y_cabe(ollama):
    r = registro_con(ollama)
    p = reg.perfiles(r, EQUIPO_GRANDE)
    assert p["perfiles"]["avanzado"]["disponible"] and p["perfiles"]["automatico"]["elige"] == "avanzado"
    p = reg.perfiles(r, EQUIPO_PEQUENO)
    assert not p["perfiles"]["avanzado"]["disponible"] and "estimado" in p["perfiles"]["avanzado"]["detalle"]
    assert p["perfiles"]["automatico"]["elige"] == "equilibrado"
    assert p["aplicado_en_analisis"] is False   # este PR no cambia el análisis


@pytest.mark.skipif(not TESSERACT, reason="Tesseract no está instalado")
def test_sin_vlm_el_modo_basico_sigue_funcionando():
    p = reg.perfiles(registro_con(None), EQUIPO_GRANDE)
    assert p["perfiles"]["equilibrado"]["disponible"] and p["perfiles"]["automatico"]["elige"] == "equilibrado"
    assert "IA_ACTIVADA" in p["perfiles"]["avanzado"]["detalle"]


def test_sin_ningun_motor():
    p = reg.perfiles(registro_con(None, tesseract=False), EQUIPO_GRANDE)
    assert not p["perfiles"]["automatico"]["disponible"] and p["perfiles"]["automatico"]["elige"] is None


@pytest.mark.skipif(not TESSERACT, reason="Tesseract no está instalado")
def test_enrutamiento_por_tarea_y_perfil(ollama):
    r = registro_con(ollama)
    assert [m.nombre for m in r.para("texto_impreso", "rapido")] == ["tesseract"]
    assert [m.nombre for m in r.para("texto_manuscrito", "avanzado")] == ["tesseract", "ollama_vlm"]
    assert [m.nombre for m in r.para("diagrama", "avanzado")] == ["ollama_vlm"]
    assert r.para("diagrama", "equilibrado") == []          # sin VLM, el diagrama se conserva como imagen
    FalsoOllama.modelos = []
    r = registro_con(ollama)
    assert r.para("diagrama", "avanzado") == []              # fallback: el VLM caído no se ofrece


@pytest.mark.skipif(not TESSERACT, reason="Tesseract no está instalado")
def test_adaptador_de_tesseract():
    a = MotorTesseractAdaptador()
    res = a.reconocer(IMAGEN, OpcionesReconocimiento())
    assert "Velocidad" in res.texto and res.confianza is not None and res.motor.licencia == "Apache-2.0"


def test_memoria_estimada():
    assert reg.memoria_suficiente("qwen3-vl:4b", {"ram_disponible_gb": 8, "gpus": []})[0] is True
    assert reg.memoria_suficiente("qwen3-vl:8b", {"ram_disponible_gb": 4, "gpus": [{"vram_libre_gb": 12}]})[0] is True
    assert reg.memoria_suficiente("modelo-desconocido:1b", {"ram_disponible_gb": 8, "gpus": []})[0] is None


def test_hardware_sin_datos_privados():
    equipo = reg.hardware()
    assert set(equipo) == {"sistema", "cpus", "ram_gb", "ram_disponible_gb", "gpus"}


# ------------------------------------------------------------------ API y diagnóstico

def test_api_motores_y_perfiles(nuevo_cliente):
    c = nuevo_cliente()
    assert c.get("/api/v2/reconocimiento/motores").status_code == 401
    c.registrar()
    motores = c.get("/api/v2/reconocimiento/motores").json()["motores"]
    assert {m["nombre"] for m in motores} == {"tesseract", "ollama_vlm"}
    vlm = next(m for m in motores if m["nombre"] == "ollama_vlm")
    assert vlm["disponible"] is False and "diagrama" in vlm["capacidades"]
    p = c.get("/api/v2/reconocimiento/perfiles").json()
    assert set(p["perfiles"]) == {"rapido", "equilibrado", "avanzado", "automatico"}
    assert "equipo" not in p and "ram_gb" not in json.dumps(p)          # el equipo solo en /diagnostico


def test_listo_sin_ia_y_diagnostico_local(nuevo_cliente):
    c = nuevo_cliente()
    listo = c.get("/api/v2/listo").json()
    assert listo["dependencias"]["ia_local"]["obligatoria"] is False
    assert listo["dependencias"]["ia_local"]["ok"] is False and "opcional" in listo["dependencias"]["ia_local"]["detalle"]


def _script(env_extra):
    env = {**os.environ, **env_extra}
    return subprocess.run([sys.executable, str(RAIZ / "fullstack/scripts/diagnostico_ia.py"), "--json"],
                          capture_output=True, text=True, env=env, timeout=60)


def test_script_de_diagnostico():
    r = _script({"IA_ACTIVADA": "false"})
    assert r.returncode == 0, r.stderr
    informe = json.loads(r.stdout)
    assert informe["vlm_disponible"] is False and "perfiles" in informe and informe["equipo"]["cpus"]
    r = _script({"IA_ACTIVADA": "true", "OLLAMA_HOST": "http://127.0.0.1:9"})
    assert r.returncode == 1 and "no responde" in json.loads(r.stdout)["vlm"]["detalle"]


def test_script_prueba_con_ollama_simulado(ollama):
    env = {**os.environ, "IA_ACTIVADA": "true", "OLLAMA_HOST": ollama}
    r = subprocess.run([sys.executable, str(RAIZ / "fullstack/scripts/diagnostico_ia.py"), "--probar", "--json"],
                       capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["prueba"]["ok"] is True
