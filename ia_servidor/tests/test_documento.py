"""Segmentación por regiones y tarea «documento» (BACK-36). Sin GPU: Ollama simulado."""

import cv2
import numpy as np
import pytest

from conftest import OllamaFalso
from ia_servidor.esquemas import construir
from ia_servidor.segmentacion import contencion, evaluar_segmentacion, regiones_opencv


def pizarron() -> np.ndarray:
    """Tres bloques separados (dos columnas) dentro de un marco oscuro, como una foto de pizarrón."""
    img = np.full((900, 1200, 3), 235, np.uint8)
    cv2.rectangle(img, (0, 0), (1199, 899), (60, 60, 60), 18)                     # marco
    for i, linea in enumerate(["sin(t) = 0", "cos(t) = 1"]):                       # bloque 1 (izquierda, arriba)
        cv2.putText(img, linea, (80, 150 + i * 60), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (20, 20, 20), 3)
    cv2.putText(img, "Tabla", (80, 600), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (30, 30, 160), 3)   # bloque 2 (rojo)
    for i, linea in enumerate(["Recordatorios", "- estudiar"]):                    # bloque 3 (derecha)
        cv2.putText(img, linea, (720, 300 + i * 60), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (20, 20, 20), 3)
    return img


def test_segmenta_bloques_sin_el_marco_y_en_orden_de_lectura():
    regiones = regiones_opencv(pizarron())
    assert len(regiones) == 3
    centros_x = [(r.bbox[0] + r.bbox[2]) / 2 for r in regiones]
    assert centros_x[0] < 600 and centros_x[1] < 600 and centros_x[2] > 600     # columna izquierda primero
    assert regiones[0].bbox[1] < regiones[1].bbox[1]                            # de arriba abajo
    assert all(r.bbox[0] > 5 and r.bbox[2] < 1195 for r in regiones)            # el marco no es una región


def test_bloque_contiene_sus_lineas():
    regiones = regiones_opencv(pizarron())
    assert contencion([80, 115, 300, 225], regiones[0].bbox) >= 0.85


def test_pizarron_vacio_no_da_regiones():
    assert regiones_opencv(np.full((600, 800, 3), 240, np.uint8)) == []


def test_evaluar_segmentacion():
    ev = evaluar_segmentacion({"a": [0, 0, 10, 10], "b": [50, 50, 60, 60]}, [[0, 0, 12, 12]])
    assert ev["enteras"] == 1 and ev["detalle"]["a"]["entera"] and not ev["detalle"]["b"]["entera"]


@pytest.mark.parametrize("contenido, esperado", [
    ("DIBUJO: dos cajas unidas por una flecha", ("imagen", None)),
    (r"$\frac{a}{b} = c$" + "\n" + r"$\sqrt{x}$", ("formula", r"\frac{a}{b} = c" + "\n" + r"\sqrt{x}")),
    ("Recordatorios\n- estudiar", ("texto", None)),
])
def test_construir_region(contenido, esperado):
    r = construir("region", contenido)
    tipo = "imagen" if r.descripcion and not r.texto else "formula" if r.latex else "texto"
    assert (tipo, r.latex) == esperado


def test_tarea_documento(armar):
    ollama = OllamaFalso(chat=[r"$\sin(t)=0$" + "\n" + r"$\cos(t)=1$", "DIBUJO: una tabla", "Recordatorios [?]"])
    cliente, *_ = armar(ollama)
    png = cv2.imencode(".png", pizarron())[1].tobytes()
    r = cliente.post("/api/v1/analisis?tarea=documento", content=png, headers={"Content-Type": "image/png"})
    assert r.status_code == 200, r.json()
    res = r.json()["resultado"]
    assert [b["id"] for b in res["bloques"]] == ["p1b1", "p1b2", "p1b3"] and res["segmentacion"]["regiones"] == 3
    assert [b["tipo"] for b in res["bloques"]] == ["formula", "imagen", "texto"]
    assert [b["estado"] for b in res["bloques"]] == ["reconocido", "reconocido", "incierto"]
    assert all(0 <= b["bbox"][0] < b["bbox"][2] <= 1200 and 0 <= b["bbox"][1] < b["bbox"][3] <= 900 for b in res["bloques"])
    assert len(ollama.chats()) == 3                                     # una inferencia por región
    assert all(len(c["messages"][0]["images"]) == 1 for c in ollama.chats())
    assert res["revision_requerida"] is True and r.json()["pipeline_version"] == "1.2.0"


def test_documento_respeta_el_maximo_de_regiones(armar):
    cliente, ollama, _ = armar(OllamaFalso(chat=["x"] * 5), max_regiones=2)
    png = cv2.imencode(".png", pizarron())[1].tobytes()
    r = cliente.post("/api/v1/analisis?tarea=documento", content=png, headers={"Content-Type": "image/png"})
    assert len(r.json()["resultado"]["bloques"]) == 2 and len(ollama.chats()) == 2


def test_region_no_es_tarea_publica(armar):
    cliente, *_ = armar()
    r = cliente.post("/api/v1/analisis?tarea=region", content=cv2.imencode(".png", pizarron())[1].tobytes(),
                     headers={"Content-Type": "image/png"})
    assert r.json()["error"]["codigo"] == "TAREA_INVALIDA"
    assert "documento" in cliente.get("/api/v1/capacidades").json()["tareas"]


def test_una_region_invalida_no_tumba_el_documento(armar):
    # 2.ª región: respuesta cortada por longitud (done_reason=length) → «no_reconocido», el resto sigue
    class Cortada(OllamaFalso):
        def __call__(self, metodo, url, cuerpo, timeout):
            estado, datos = super().__call__(metodo, url, cuerpo, timeout)
            if url.endswith("/api/chat") and len(self.chats()) == 2:
                datos = datos.replace(b'"done_reason": "stop"', b'"done_reason": "length"')
            return estado, datos
    cliente, *_ = armar(Cortada(chat=["uno", "dos", "tres"]))
    png = cv2.imencode(".png", pizarron())[1].tobytes()
    r = cliente.post("/api/v1/analisis?tarea=documento", content=png, headers={"Content-Type": "image/png"})
    assert r.status_code == 200
    estados = [b["estado"] for b in r.json()["resultado"]["bloques"]]
    assert estados == ["reconocido", "no_reconocido", "reconocido"]


def test_ollama_caido_si_detiene_el_documento(armar):
    import urllib.error
    cliente, *_ = armar(OllamaFalso(chat=["uno", urllib.error.URLError(ConnectionRefusedError())]))
    png = cv2.imencode(".png", pizarron())[1].tobytes()
    r = cliente.post("/api/v1/analisis?tarea=documento", content=png, headers={"Content-Type": "image/png"})
    assert r.status_code == 503 and r.json()["error"]["codigo"] == "NO_DISPONIBLE"
