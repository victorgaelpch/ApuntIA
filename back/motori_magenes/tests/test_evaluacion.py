"""Evaluación real del OCR y las fórmulas con el corpus etiquetado (BACK-25, opt-in).

Usa Tesseract de verdad, así que no entra en la suite rápida:

    pytest -m evaluacion

Los umbrales son la línea base medida (PROCESAMIENTO.md) con un margen: si una
mejora del preprocesado o una actualización de Tesseract empeora el
reconocimiento, esta prueba lo detecta.
"""

import pytest

from app.services.ocr import MotorTesseract

pytestmark = [pytest.mark.evaluacion,
              pytest.mark.skipif(not MotorTesseract().disponible(), reason="Tesseract no está instalado")]

UMBRAL_CER = {"impreso_cuaderno": 0.02, "cuaderno_con_sombra": 0.02, "impreso_pizarron": 0.02,
              "pizarron_con_ruido": 0.02, "pizarron_oscuro": 0.02, "manuscrito_cuaderno": 0.05,
              "manuscrito_dificil": 0.12}


@pytest.fixture(scope="module")
def filas():
    from herramientas.evaluar_ocr import evaluar
    return {f["muestra"]: f for f in evaluar()}


@pytest.mark.parametrize("muestra,umbral", sorted(UMBRAL_CER.items()))
def test_cer_dentro_de_la_linea_base(filas, muestra, umbral):
    assert filas[muestra]["cer"] <= umbral, f"{muestra}: CER {filas[muestra]['cer']:.3f} > {umbral}"


def test_manuscritos_sin_texto_falso_como_reconocido(filas):
    assert all(f["falsos"] == 0 for f in filas.values() if f["escritura"] == "manuscrito")


def test_formulas_2d_no_se_inventan(filas):
    f = filas["formulas_2d"]
    assert f["reconocidos"] == 0 and f["falsos"] == 0


def test_formulas_en_linea_a_latex():
    from herramientas.corpus import formulas_pizarron
    from herramientas.evaluar_formulas import evaluar
    resultado, obtenidas = evaluar(formulas_pizarron())
    exactas = sum(b is not None for _, b in resultado)
    assert exactas >= 3, f"solo {exactas}/4 fórmulas exactas"
    falsas = [b for b in obtenidas if b.tipo == "formula" and getattr(b, "latex_valido", False) and b.estado ==
              "reconocido" and all(b is not r for _, r in resultado)]
    assert not falsas, "hay fórmulas reconocidas que no están en el corpus"
