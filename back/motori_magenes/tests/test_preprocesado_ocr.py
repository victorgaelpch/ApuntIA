"""Preprocesado por perfil para OCR (BACK-12)."""

import cv2
import numpy as np
import pytest

from app.services.ocr import MotorTesseract, reconocer
from app.services.preprocesado_ocr import (advertencias_calidad, iluminacion_desigual, preprocesar_para_ocr,
                                           quitar_lineas_largas, quitar_renglones, ruido_estimado)
from herramientas.corpus import CELDAS_TABLA, corpus, diagrama, hoja_cuaderno, impreso_pizarron, pizarron_oscuro, tabla_cuaderno
from herramientas.metricas import cer

requiere_tesseract = pytest.mark.skipif(not MotorTesseract().disponible(), reason="Tesseract no está instalado")


def gris(pil):
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2GRAY)


def test_quita_el_rayado_del_cuaderno():
    g = gris(hoja_cuaderno())
    antes = (g < 225).sum()
    despues = (quitar_renglones(g) < 225).sum()
    assert despues < antes * 0.2


def test_conserva_tablas_y_barras_de_fraccion():
    g = gris(hoja_cuaderno())
    cv2.rectangle(g, (300, 300), (800, 600), 20, 3)                 # tabla
    for y in (380, 460, 540):
        cv2.line(g, (300, y), (800, y), 20, 3)
    cv2.line(g, (900, 450), (1000, 450), 20, 3)                     # barra de fracción
    limpia = quitar_renglones(g)
    assert (limpia[380, 300:800] < 100).mean() > 0.9
    assert (limpia[450, 900:1000] < 100).mean() > 0.9


def test_pizarron_de_tiza_se_invierte():
    pre = preprocesar_para_ocr(pizarron_oscuro().imagen, "pizarron")
    assert pre.imagen_ocr.mean() > 150  # fondo claro, texto oscuro


def test_cuaderno_y_pizarron_usan_perfiles_distintos():
    img = corpus()[0].imagen
    assert preprocesar_para_ocr(img, "cuaderno").psm != preprocesar_para_ocr(img, "pizarron").psm


def test_el_original_no_se_modifica():
    img = corpus()[2].imagen
    copia = img.copy()
    preprocesar_para_ocr(img, "pizarron")
    assert np.array_equal(img, copia)


def test_advertencias_de_calidad():
    nitida = corpus()[0].imagen
    assert advertencias_calidad(nitida) == []
    assert "IMAGEN_BORROSA" in advertencias_calidad(cv2.GaussianBlur(nitida, (0, 0), 6))
    assert "BAJA_RESOLUCION" in advertencias_calidad(cv2.resize(nitida, (500, 350)))


def test_detectores_adaptativos():
    muestras = {m.nombre: m.imagen for m in corpus()}
    g = lambda n: cv2.cvtColor(muestras[n], cv2.COLOR_BGR2GRAY)
    assert iluminacion_desigual(g("cuaderno_con_sombra")) and not iluminacion_desigual(g("impreso_cuaderno"))
    assert ruido_estimado(g("pizarron_con_ruido")) > 6 > ruido_estimado(g("impreso_pizarron"))


@requiere_tesseract
def test_sin_regresiones_frente_a_la_linea_base():
    """Con preprocesado, ninguna muestra empeora y las difíciles mejoran mucho."""
    for m in corpus():
        if m.escritura == "diagrama":
            # Etapa aislada: aquí solo se mide el preprocesado sobre TEXTO. En un dibujo, el
            # perfil de cuaderno hace que Tesseract lea las figuras como letras (57 % de CER en
            # esta etapa); en el flujo de producción la etapa de respaldo descarta ese texto de
            # baja confianza y conserva el dibujo como imagen (CER 0 %): lo comprueban
            # test_evaluacion.py y fullstack/evaluacion (FULL-19).
            continue
        real = "\n".join(m.lineas)
        base = cer("\n".join(b.texto for b in reconocer(m.imagen)), real)
        pre = preprocesar_para_ocr(m.imagen, m.tipo_fuente)
        nuevo = cer("\n".join(b.texto for b in reconocer(pre.imagen_ocr, psm=pre.psm)), real)
        assert nuevo <= base + 0.005, f"{m.nombre}: {base:.1%} → {nuevo:.1%}"
        if m.nombre in ("impreso_pizarron", "pizarron_con_ruido", "cuaderno_con_sombra"):
            assert nuevo < 0.05, f"{m.nombre}: {nuevo:.1%}"


def test_una_tabla_no_se_toma_por_el_borde_de_la_hoja():
    """FULL-24: la cuadrícula de la tabla se detectaba como «la hoja» y se perdía el título de fuera."""
    pre = preprocesar_para_ocr(tabla_cuaderno().imagen, "cuaderno")
    assert pre.perspectiva == "figura_interior"
    assert pre.imagen_vista.shape[:2] == tabla_cuaderno().imagen.shape[:2]  # sin recortar


def test_el_pizarron_sobre_la_pared_se_sigue_enderezando():
    assert preprocesar_para_ocr(impreso_pizarron().imagen, "pizarron").perspectiva == "corregida"


def test_quita_la_cuadricula_de_una_tabla_pero_no_un_recuadro_ni_un_diagrama():
    g = gris(tabla_cuaderno().imagen)
    y = 200 + 130  # una línea interior de la tabla
    assert (g[y - 1:y + 2, 300:1000] < 120).mean() > 0.3
    assert (quitar_lineas_largas(g)[y - 1:y + 2, 300:1000] < 120).mean() < 0.05
    recuadro = np.full((800, 1200), 250, np.uint8)
    cv2.rectangle(recuadro, (100, 100), (1100, 700), 20, 4)
    assert np.array_equal(quitar_lineas_largas(recuadro), recuadro)
    d = gris(diagrama().imagen)
    assert np.array_equal(quitar_lineas_largas(d), d)


@requiere_tesseract
def test_se_leen_las_celdas_y_el_titulo_de_una_tabla_fotografiada():
    pre = preprocesar_para_ocr(tabla_cuaderno().imagen, "cuaderno")
    texto = "\n".join(b.texto for b in reconocer(pre.imagen_ocr, psm=pre.psm))
    assert "Unidades del SI" in texto
    assert sum(c in texto for fila in CELDAS_TABLA for c in fila) >= 6, texto  # antes: 0 de 8
