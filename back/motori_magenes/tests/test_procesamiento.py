"""Pruebas unitarias del pipeline, sin HTTP (BACK-08)."""

import cv2
import numpy as np
import pytest

from app.services.mejora import mejorar
from app.services.perspectiva import detectar_pizarron, ordenar_esquinas
from app.services.procesamiento import OpcionesProcesamiento, procesar, redimensionar
from app.services.ruido import METODOS, eliminar_ruido
from app.services.validacion import detectar_formato, nombre_seguro
from herramientas.muestras import foto_inclinada, muestras, pizarron_plano, ruido


def test_el_original_no_se_modifica(pizarron_inclinado):
    foto, _ = pizarron_inclinado
    copia = foto.copy()
    procesar(foto, OpcionesProcesamiento(max_lado=1000))
    assert np.array_equal(foto, copia)


def test_sin_etapas_devuelve_copia():
    img = np.zeros((5, 5, 3), np.uint8)
    res = procesar(img, OpcionesProcesamiento(perspectiva=False, ruido="ninguno", mejorar=False))
    assert res.imagen is not img and np.array_equal(res.imagen, img)


@pytest.mark.parametrize("forma", [(1, 1), (17, 31), (387, 516), (1920, 1080), (5, 5, 4), (40, 60)])
def test_distintas_dimensiones_y_canales(forma):
    img = np.random.default_rng(0).integers(0, 255, forma, dtype=np.uint8)
    res = procesar(img, OpcionesProcesamiento(max_lado=2000))
    assert res.imagen.ndim == 3 and res.imagen.shape[2] == 3
    assert res.tiempo_total_ms >= 0


def test_redimensionar_nunca_amplia():
    img = np.zeros((100, 200, 3), np.uint8)
    assert redimensionar(img, 2000) is img
    assert redimensionar(np.zeros((1000, 4000, 3), np.uint8), 2000).shape == (500, 2000, 3)


def test_ordenar_esquinas():
    desordenadas = np.float32([[10, 90], [90, 10], [10, 10], [90, 90]])
    assert ordenar_esquinas(desordenadas).tolist() == [[10, 10], [90, 10], [90, 90], [10, 90]]


@pytest.mark.parametrize("nombre", ["inclinada", "oscura", "sombra", "ruido"])
def test_detecta_pizarron_en_muestras(nombre):
    assert detectar_pizarron(muestras()[nombre]).esquinas is not None


def test_precision_de_esquinas():
    foto, reales = foto_inclinada()
    det = detectar_pizarron(foto)
    assert np.abs(det.esquinas - reales).max() < 10


@pytest.mark.parametrize("nombre", ["frontal", "sin_pizarron"])
def test_sin_cuadrilatero_fiable_no_detecta(nombre):
    assert detectar_pizarron(muestras()[nombre]).esquinas is None


def test_ruido_mejora_psnr_sin_borrar_texto():
    limpia = pizarron_plano()
    ruidosa = ruido(limpia)
    filtrada = eliminar_ruido(ruidosa, "combinado")
    assert cv2.PSNR(limpia, filtrada) > cv2.PSNR(limpia, ruidosa) + 10
    texto = cv2.cvtColor(limpia, cv2.COLOR_BGR2GRAY) < 120
    assert cv2.cvtColor(filtrada, cv2.COLOR_BGR2GRAY)[texto].mean() < 120


@pytest.mark.parametrize("metodo", METODOS)
def test_filtros_conservan_forma(metodo):
    img = pizarron_plano(300, 200)
    assert eliminar_ruido(img, metodo).shape == img.shape


def test_mejora_aumenta_contraste_en_foto_oscura():
    from herramientas.muestras import oscurecer
    oscura = oscurecer(pizarron_plano())
    antes = cv2.cvtColor(oscura, cv2.COLOR_BGR2GRAY).std()
    despues = cv2.cvtColor(mejorar(oscura, True), cv2.COLOR_BGR2GRAY).std()
    assert despues > antes * 1.5


@pytest.mark.parametrize("datos,esperado", [
    (b"\xff\xd8\xff\xe0", "jpeg"), (b"\x89PNG\r\n\x1a\n", "png"),
    (b"RIFF\x00\x00\x00\x00WEBPVP8 ", "webp"), (b"GIF89a", None), (b"", None),
])
def test_detectar_formato(datos, esperado):
    assert detectar_formato(datos) == esperado


@pytest.mark.parametrize("entrada,salida", [
    ("../../x.png", "x.png"), ("C:\\Users\\a\\b.jpg", "b.jpg"), (None, "imagen"),
    ("", "imagen"), ('a"b\n.png', "ab.png"), ("x" * 300, "x" * 150),
])
def test_nombre_seguro(entrada, salida):
    assert nombre_seguro(entrada) == salida
