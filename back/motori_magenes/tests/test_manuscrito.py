"""Escritura a mano con alternativa segura (BACK-14)."""

import cv2
import numpy as np
import pytest

from app.services.manuscrito import leer_con_respaldo, zonas_sin_texto
from app.services.ocr import BloqueOCR, MotorOCR, MotorTesseract, Palabra, agrupar, reconocer
from app.services.preprocesado_ocr import preprocesar_para_ocr, quitar_renglones
from herramientas.corpus import hoja_cuaderno, impreso_cuaderno, manuscrito_dificil

requiere_tesseract = pytest.mark.skipif(not MotorTesseract().disponible(), reason="Tesseract no está instalado")


class MotorFijo(MotorOCR):
    """Motor de prueba que siempre devuelve las mismas palabras."""

    def __init__(self, palabras):
        self.lista = palabras

    def palabras(self, imagen, idiomas, psm):
        return self.lista


def test_una_palabra_dudosa_hace_incierto_el_bloque():
    b = agrupar([Palabra("Repasar", 0.95, (0, 0, 80, 20), 1, 1, 1), Palabra("integrales", 0.95, (90, 0, 200, 20), 1, 1, 1),
                 Palabra("inte", 0.7, (0, 30, 40, 50), 1, 1, 2)])[0]
    assert b.estado == "incierto" and b.dudosas == ["inte"]


def test_ilegible_no_inventa_texto_y_conserva_recorte():
    gris = np.full((300, 600), 250, np.uint8)
    ilegible = BloqueOCR("xq#z", 0.2, [50, 50, 300, 90], ["xq#z"], 30)
    salida = leer_con_respaldo(gris, [ilegible], "spa", motor=MotorFijo([]))
    b = salida[0]
    assert b.texto == "" and b.tipo == "manuscrito" and b.recortar and b.bbox == [50, 50, 300, 90]


def test_bloques_reconocidos_no_se_tocan():
    gris = np.full((300, 600), 250, np.uint8)
    bueno = BloqueOCR("Derivadas", 0.96, [10, 10, 200, 50], ["Derivadas"], 30, tipo="titulo")
    # Si el segundo intento se aplicara, devolvería otro texto: no debe ocurrir.
    salida = leer_con_respaldo(gris, [bueno], "spa", motor=MotorFijo([Palabra("Otra", 0.99, (0, 0, 9, 9), 1, 1, 1)]))
    assert salida[0].texto == "Derivadas" and salida[0].tipo == "titulo" and not salida[0].recortar


def test_incierto_conserva_texto_y_recorte():
    gris = np.full((300, 600), 250, np.uint8)
    dudoso = BloqueOCR("Examen e viernes", 0.7, [10, 10, 300, 50], ["Examen e viernes"], 30, dudosas=["e"])
    b = leer_con_respaldo(gris, [dudoso], "spa", motor=MotorFijo([]))[0]
    assert b.texto == "Examen e viernes" and b.recortar


def test_dibujo_sin_texto_se_conserva_como_imagen():
    g = cv2.cvtColor(np.array(hoja_cuaderno()), cv2.COLOR_RGB2GRAY)
    cv2.circle(g, (700, 500), 150, 30, 3)
    cv2.arrowedLine(g, (500, 500), (640, 500), 30, 3)
    zonas = zonas_sin_texto(quitar_renglones(g), [])  # en producción llega sin renglones
    assert any(z.tipo == "imagen" and z.recortar and z.texto == "" for z in zonas)


@requiere_tesseract
def test_manuscrito_dificil_sin_falsos_reconocidos():
    m = manuscrito_dificil()
    pre = preprocesar_para_ocr(m.imagen, m.tipo_fuente)
    bloques = leer_con_respaldo(pre.imagen_ocr, reconocer(pre.imagen_ocr, psm=pre.psm), "spa+eng")
    reales = {" ".join(l.split()) for l in m.lineas}
    for b in bloques:
        if b.texto and b.estado == "reconocido":
            assert all(" ".join(l.split()) in reales for l in b.texto.split("\n")), b.texto
    assert any(b.recortar for b in bloques)  # lo dudoso queda para revisión con su imagen


@requiere_tesseract
def test_texto_impreso_no_empeora_con_el_respaldo():
    m = impreso_cuaderno()
    pre = preprocesar_para_ocr(m.imagen, m.tipo_fuente)
    antes = reconocer(pre.imagen_ocr, psm=pre.psm)
    despues = leer_con_respaldo(pre.imagen_ocr, antes, "spa+eng")
    assert [b.texto for b in despues if b.texto] == [b.texto for b in antes]
