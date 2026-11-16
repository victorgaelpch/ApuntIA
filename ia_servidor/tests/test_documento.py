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
    cliente, *_ = armar(ollama, seg_hueco_lineas=0.6)  # párrafos de la imagen sintética en un bloque
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
    assert res["revision_requerida"] is True and r.json()["pipeline_version"] == "1.3.0"
    assert res["segmentacion"]["descartes"] == []                       # nada parecía plantilla


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
    cliente, *_ = armar(Cortada(chat=["uno", "dos", "tres"]), seg_hueco_lineas=0.6)
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


# ---------------------------------------------------------------------------- cuaderno (hallazgo del 15/11/2026)

def cuaderno(oscuridad: int = 90) -> np.ndarray:
    """Hoja cuadriculada como en una foto de móvil (cuadrícula ondulada e inclinada), con dos
    párrafos, una fórmula, un circuito sencillo y un separador punteado."""
    alto, ancho = 2000, 1500
    img = np.full((alto, ancho, 3), (236, 240, 242), np.int16)
    rejilla = np.zeros((alto, ancho), np.uint8)
    for k, x in enumerate(range(0, ancho, 30)):
        ys = np.arange(0, alto, 6)
        xs = (x + 4 * np.sin(ys / 200 + k) + ys * 0.01).astype(int)
        cv2.polylines(rejilla, [np.stack([xs, ys], 1).reshape(-1, 1, 2)], False, 255, 2)
    for k, y in enumerate(range(0, alto, 30)):
        xs = np.arange(0, ancho, 6)
        ys = (y + 5 * np.sin(xs / 170 + k) + xs * 0.012).astype(int)
        cv2.polylines(rejilla, [np.stack([xs, ys], 1).reshape(-1, 1, 2)], False, 255, 2)
    img[rejilla > 0] -= np.array([oscuridad, oscuridad // 2, 0], np.int16)
    img = np.clip(img, 0, 255).astype(np.uint8)
    azul, negro = (150, 60, 30), (40, 40, 40)
    for i, linea in enumerate(["Para nodos es ley de ohm", "Potencial mayor menos menor"]):
        cv2.putText(img, linea, (700, 400 + i * 55), cv2.FONT_HERSHEY_SIMPLEX, 1.1, azul, 3)
    cv2.putText(img, "I = (VB - VA) / R", (760, 600), cv2.FONT_HERSHEY_SIMPLEX, 1.2, negro, 3)
    cv2.rectangle(img, (150, 380), (420, 600), negro, 4)                   # circuito
    cv2.circle(img, (285, 490), 45, negro, 4)
    for x in range(100, 1400, 60):                                         # separador punteado
        cv2.line(img, (x, 800), (x + 35, 800), azul, 4)
    for i, linea in enumerate(["Para mallas es diferencia", "de corrientes"]):
        cv2.putText(img, linea, (700, 1000 + i * 55), cv2.FONT_HERSHEY_SIMPLEX, 1.1, azul, 3)
    return img


@pytest.mark.parametrize("oscuridad", [60, 90, 120])
def test_la_cuadricula_no_une_todo_el_apunte(oscuridad):
    # Antes, con la cuadrícula de una foto real, TODO el apunte salía en una región (76-100 % de la foto).
    regiones = regiones_opencv(cuaderno(oscuridad))
    areas = [(r.bbox[2] - r.bbox[0]) * (r.bbox[3] - r.bbox[1]) / (2000 * 1500) for r in regiones]
    assert regiones and max(areas) < 0.10
    for linea in ([700, 375, 1100, 415], [700, 428, 1180, 470], [760, 570, 1040, 612]):  # cada línea, entera
        assert any(contencion(linea, r.bbox) >= 0.85 for r in regiones), linea
    assert not any(r.bbox[0] < 450 and r.bbox[2] > 700 for r in regiones)            # circuito y texto, aparte
    assert not any(r.bbox[2] - r.bbox[0] > 1000 and r.bbox[3] - r.bbox[1] < 60 for r in regiones)  # sin el punteado


def test_el_pizarron_no_cambia_con_la_atencion_a_la_cuadricula():
    # Sin cuadrícula no se resta nada: el pizarrón sintético da las mismas 3 regiones de siempre.
    assert len(regiones_opencv(pizarron())) == 3


@pytest.mark.parametrize("texto, plantilla", [
    ("Día Mes Año", True), ("Folio", True), ("Nombre:\nTema:", True), ("NOMBRE", True),
    ("Tema: Mallas", False), ("Fecha 15/11/2026", False), ("Corrientes", False), ("", False),
])
def test_es_plantilla(texto, plantilla):
    from ia_servidor.depurar import es_plantilla
    assert es_plantilla(texto) is plantilla


def _b(tipo, bbox, texto="", estado="reconocido", dudas=None, descripcion=None):
    return {"id": f"p1b{bbox[0]}", "orden": 0, "tipo": tipo, "bbox": bbox, "texto": texto, "latex": None,
            "estado": estado, "dudas": dudas or [], "descripcion": descripcion}


def test_depurar_aparta_plantilla_y_adornos_y_conserva_el_apunte():
    from ia_servidor.depurar import depurar
    ancho, alto = 1000, 1000
    bloques = [
        _b("texto", [300, 20, 600, 80], "Día Mes Año"),                                  # plantilla
        _b("imagen", [20, 20, 120, 120], descripcion="dos figuras abstractas"),           # logo arriba
        _b("manuscrito", [20, 140, 120, 170], estado="no_reconocido"),                    # adorno ilegible arriba
        _b("manuscrito", [400, 150, 500, 190], estado="no_reconocido",
           dudas=["el modelo no dio una respuesta válida"]),                             # fallo: se queda
        _b("texto", [300, 300, 700, 340], "Tema: Mallas"),
        _b("imagen", [100, 500, 200, 600], descripcion="una resistencia"),               # circuito, abajo
        _b("imagen", [205, 520, 300, 610], descripcion="una fuente"),                   # se toca con el anterior
        _b("imagen", [800, 800, 900, 900], descripcion="una gráfica"),                  # lejos: aparte
    ]
    quedan, descartes = depurar(bloques, ancho, alto)
    assert [d["motivo"] for d in descartes] == ["plantilla impresa del cuaderno"] + ["adorno del encabezado del cuaderno"] * 2
    assert [b["texto"] or b["descripcion"] for b in quedan] == [
        None, "Tema: Mallas", "una resistencia; una fuente", "una gráfica"]
    assert quedan[2]["bbox"] == [100, 500, 300, 610]
    assert [b["orden"] for b in quedan] == [1, 2, 3, 4]


def test_documento_informa_los_descartes(armar):
    img = pizarron()
    cv2.putText(img, "Folio", (80, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (30, 30, 160), 3)
    ollama = OllamaFalso(chat=["Folio", r"$\sin(t)=0$", "DIBUJO: una tabla", "Recordatorios"])
    cliente, *_ = armar(ollama, seg_hueco_lineas=0.6)
    png = cv2.imencode(".png", img)[1].tobytes()
    res = cliente.post("/api/v1/analisis?tarea=documento", content=png, headers={"Content-Type": "image/png"}).json()["resultado"]
    assert [d["motivo"] for d in res["segmentacion"]["descartes"]] == ["plantilla impresa del cuaderno"]
    assert res["segmentacion"]["regiones"] == 4 and len(res["bloques"]) == 3
    assert "Folio" not in res["texto"]
