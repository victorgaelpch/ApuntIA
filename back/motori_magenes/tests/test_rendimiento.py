"""Tiempos y memoria de casos representativos (BACK-25, opt-in).

    pytest -m rendimiento -s

Los límites son holgados (≈ 3× lo medido en el equipo de desarrollo): no son
una prueba de velocidad, sino una alarma ante regresiones fuertes (por ejemplo,
dejar de reducir las imágenes antes de procesarlas o de incrustarlas en el PDF).
La memoria se mide con tracemalloc (asignaciones de Python y NumPy).
"""

import io
import time
import tracemalloc

import cv2
import numpy as np
import pytest
from PIL import Image

pytestmark = pytest.mark.rendimiento

RESULTADOS = []


def medir(nombre, funcion, limite_s, limite_mb):
    tracemalloc.start()
    inicio = time.perf_counter()
    resultado = funcion()
    segundos = time.perf_counter() - inicio
    pico = tracemalloc.get_traced_memory()[1] / 1e6
    tracemalloc.stop()
    RESULTADOS.append((nombre, segundos, pico))
    print(f"\n{nombre}: {segundos:.2f} s, pico {pico:.0f} MB (límites {limite_s} s / {limite_mb} MB)")
    assert segundos <= limite_s, f"{nombre} tardó {segundos:.1f} s"
    assert pico <= limite_mb, f"{nombre} usó {pico:.0f} MB"
    return resultado


def foto_12mp() -> bytes:
    rng = np.random.default_rng(1)
    img = np.full((3000, 4000, 3), 235, np.uint8)
    for _ in range(40):
        y, x = rng.integers(100, 2800), rng.integers(100, 3600)
        cv2.putText(img, "Derivadas e integrales", (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 2, (30, 30, 30), 4)
    return cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()


def test_v1_foto_de_12_megapixeles(client):
    datos = foto_12mp()
    r = medir("v1 /analisis 12 MP", lambda: client.post("/analisis", files={"file": ("a.jpg", datos, "image/jpeg")}),
              limite_s=10, limite_mb=600)
    assert r.status_code == 200


def test_ocr_de_una_pagina():
    from app.services.ocr import MotorTesseract
    if not MotorTesseract().disponible():
        pytest.skip("Tesseract no está instalado")
    from herramientas.corpus import impreso_cuaderno
    from app.services.preprocesado_ocr import preprocesar_para_ocr
    from app.services.ocr import reconocer
    m = impreso_cuaderno()

    def flujo():
        pre = preprocesar_para_ocr(m.imagen, m.tipo_fuente)
        return reconocer(pre.imagen_ocr, psm=pre.psm)

    assert medir("OCR de una página (preprocesado + Tesseract)", flujo, limite_s=6, limite_mb=300)


def test_pdf_de_20_paginas_con_fotos():
    from app.services.documento import Bloque, Documento, Pagina
    from app.services.estructura import estructurar
    from app.services.pdf import OpcionesPDF, generar_pdf
    rng = np.random.default_rng(0)
    b = io.BytesIO()
    Image.fromarray(rng.integers(0, 255, (1800, 2400, 3), dtype=np.uint8)).save(b, "JPEG", quality=85)
    foto = b.getvalue()
    paginas = [Pagina(id=f"p{i}", orden=i, tipo_fuente="cuaderno", archivo_original=f"o{i}", ancho=2400, alto=1800)
               for i in range(1, 21)]
    bloques = [Bloque(id=f"b{i}", pagina=f"p{i % 20 + 1}", orden=i, tipo="texto", origen="ocr", confianza=0.9,
                      bbox=[0, 0, 1, 1], texto="Texto del apunte con tildes áéíóú. " * 8, texto_original="x")
               for i in range(120)]
    doc = Documento(titulo="Grande", paginas=paginas, bloques=bloques)
    datos, n = medir("PDF con 20 fotos de 4 MP en el anexo",
                     lambda: generar_pdf(doc, estructurar(doc), 1, lambda _a: foto, OpcionesPDF(incluir_originales=True)),
                     limite_s=12, limite_mb=400)
    assert n >= 20 and len(datos) < 5_000_000
