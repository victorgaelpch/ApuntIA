"""Banco de evaluación del servidor IA (BACK-36): corpus privado y métricas de fórmulas."""

import json

import cv2
import numpy as np
import pytest

from ia_servidor.medir import cargar_corpus, normalizar_latex, notacion_equivalente


def corpus(tmp_path, **cambios):
    cv2.imwrite(str(tmp_path / "pizarron 1.jpg"), np.full((60, 80, 3), 255, np.uint8))  # nombre con espacio
    entrada = {"archivo": "pizarron 1.jpg", "tipo_fuente": "pizarron", "escritura": "manuscrito",
               "lineas": ["Derivadas"], "latex": [], "permiso": "autor de la foto, 2026-11-14"}
    entrada.update(cambios)
    (tmp_path / "verdad.json").write_text(json.dumps({"foto1": entrada}), encoding="utf-8")
    return tmp_path


def test_carga_corpus_privado(tmp_path):
    [m] = cargar_corpus(corpus(tmp_path))
    assert (m.nombre, m.escritura, m.lineas, m.imagen.shape) == ("foto1", "manuscrito", ["Derivadas"], (60, 80, 3))


def test_sin_permiso_no_se_evalua(tmp_path):
    with pytest.raises(ValueError, match="permiso"):
        cargar_corpus(corpus(tmp_path, permiso=""))


def test_archivo_fuera_de_la_carpeta(tmp_path):
    (tmp_path / "dentro").mkdir()
    with pytest.raises(ValueError, match="dentro de la carpeta"):
        cargar_corpus(corpus(tmp_path / "dentro", archivo="../fuera.jpg"))


def test_escritura_desconocida(tmp_path):
    with pytest.raises(ValueError, match="escritura"):
        cargar_corpus(corpus(tmp_path, escritura="poema"))


def test_imagen_ilegible(tmp_path):
    c = corpus(tmp_path)
    (c / "pizarron 1.jpg").write_bytes(b"no es una imagen")
    with pytest.raises(ValueError, match="no se puede abrir"):
        cargar_corpus(c)


def test_latex_normalizado_ignora_estilo():
    assert normalizar_latex("x^{2} + 2 x") == normalizar_latex("$x^2+2x$")
    assert normalizar_latex(r"\left( a \right)") == "(a)"


def test_notacion_equivalente():
    assert notacion_equivalente(r"\frac{a}{b} + \sqrt{x + 1}") == notacion_equivalente("a/b + sqrt(x + 1)")
    assert notacion_equivalente(r"\frac{a+1}{b}") == "(a+1)/b"
    assert notacion_equivalente(r"\frac{a}{b}") != notacion_equivalente(r"\frac{b}{a}")
