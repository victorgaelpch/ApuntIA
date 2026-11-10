"""OCR de texto impreso por bloques (BACK-13)."""

import numpy as np
import pytest

from app.services import ocr
from app.services.ocr import ErrorOCR, MotorNinguno, Palabra, agrupar, estado_por_confianza, reconocer
from herramientas.corpus import impreso_cuaderno, pizarron_oscuro

TESSERACT = ocr.MotorTesseract().disponible()
requiere_tesseract = pytest.mark.skipif(not TESSERACT, reason="Tesseract no está instalado")


@requiere_tesseract
def test_texto_impreso_en_bloques_ordenados_con_tildes():
    m = impreso_cuaderno()
    bloques = reconocer(m.imagen)
    texto = "\n".join(b.texto for b in bloques)
    for esperado in ["Derivadas", "razón", "función", "más rápido", "pendiente"]:
        assert esperado in texto, texto
    # Orden de lectura: de arriba abajo
    tops = [b.bbox[1] for b in bloques]
    assert tops == sorted(tops)
    assert bloques[0].texto == "Derivadas" and bloques[0].tipo == "titulo"
    assert all(b.estado in ("reconocido", "incierto", "no_reconocido") for b in bloques)


@requiere_tesseract
def test_ubicacion_verificable():
    m = impreso_cuaderno()
    titulo = reconocer(m.imagen)[0]
    x0, y0, x1, y1 = titulo.bbox
    assert 140 <= x0 <= 160 and 60 <= y0 <= 90 and x1 > x0 and y1 > y0  # se dibujó en (150, 68)


@requiere_tesseract
def test_imagen_sin_texto_devuelve_vacio():
    assert reconocer(np.full((400, 600, 3), 250, np.uint8)) == []


def test_motor_ausente_es_fallo_tecnico_no_texto_vacio():
    with pytest.raises(ErrorOCR) as exc:
        reconocer(np.zeros((10, 10, 3), np.uint8), motor=MotorNinguno())
    assert exc.value.codigo == "OCR_NO_DISPONIBLE"


def test_estados_por_confianza():
    assert estado_por_confianza(0.95) == "reconocido"
    assert estado_por_confianza(0.6) == "incierto"
    assert estado_por_confianza(0.2) == "no_reconocido"


def test_agrupar_por_parrafo_y_linea():
    palabras = [Palabra("mundo", 0.9, (60, 0, 100, 20), 1, 1, 1), Palabra("Hola", 0.9, (0, 0, 50, 20), 1, 1, 1),
                Palabra("otra", 0.4, (0, 30, 40, 50), 1, 1, 2), Palabra("Bloque", 0.95, (0, 100, 60, 120), 2, 1, 1)]
    bloques = agrupar(palabras)
    assert [b.texto for b in bloques] == ["Hola mundo\notra", "Bloque"]
    assert bloques[0].bbox == [0, 0, 100, 50]
    # La confianza del bloque la limita su palabra más dudosa (BACK-14)
    assert bloques[0].confianza == 0.4 and bloques[0].estado == "no_reconocido"


def test_salud_conserva_v1_y_anade_ocr(client):
    datos = client.get("/salud").json()
    assert {"estado", "version", "formatos", "max_mb", "max_megapixeles"} <= set(datos)
    assert set(datos["ocr"]) >= {"disponible", "motor", "idiomas"}
