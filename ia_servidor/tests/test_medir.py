"""Banco de evaluación del servidor IA (BACK-36): corpus privado y métricas de fórmulas."""

import json

import cv2
import numpy as np
import pytest

from ia_servidor.medir import (cargar_corpus, cobertura, comparar_pagina_y_regiones, fidelidad, normalizar_latex,
                               notacion_equivalente, reevaluar)


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


def test_simbolos_latex_y_unicode_cuentan_igual():
    assert notacion_equivalente(r"\sin(\pi/2) = \text{opposite}") == notacion_equivalente("sin(π/2)=opposite")
    assert notacion_equivalente(r"\sin^{2}(\theta)") == notacion_equivalente("sin²(θ)")
    assert notacion_equivalente(r"\pm\sqrt{1-x}") == notacion_equivalente("±√(1-x)")


def test_cobertura_no_depende_del_orden_ni_de_partir_lineas():
    salida = "Recordatorios\ncos(t) = 1\n\\frac{a}{b} +\n\\frac{c}{d}\nsin(0)=0"
    cob, faltan = cobertura(salida, ["sin(0)=0", r"\frac{a}{b}+\frac{c}{d}", "tan(t)=5"])
    assert round(cob, 2) == 0.67 and faltan == ["tan(t)=5"]


def test_cobertura_tolera_errores_pequenos_pero_no_grandes():
    assert cobertura("Resultant Force Vectr", ["Resultant Force Vector"])[0] == 1.0
    assert cobertura("Half Angle", ["Double Angle Formulas"])[0] == 0.0


def test_comparar_pagina_y_regiones():
    from types import SimpleNamespace as N
    pagina = N(nombre="p", escritura="pagina", archivo="foto.webp", origen=None, lineas=["Titulo"], latex=[])
    r1 = N(nombre="r1", escritura="formula", archivo="r1.png", origen="foto.webp", lineas=[], latex=["a=1", "b=2"])
    salidas = {"p": (pagina, "Titulo\na=1"), "r1": (r1, "a=1\nb=2")}
    [c] = comparar_pagina_y_regiones([pagina, r1], salidas)
    assert (c["cobertura_pagina_completa"], c["cobertura_por_regiones"], c["faltan_en_pagina_completa"]) == (0.5, 1.0, ["b=2"])


TRAMPA = {"descripcion": "sin(π)=-1 tal como está escrito", "literal": r"\sin(\pi)=-1", "corregido": r"\sin(\pi)=0"}


@pytest.mark.parametrize("salida, estado", [
    ("Sin(π) = -1", "fiel"),                 # Unicode, mayúscula y espacios no importan
    (r"\sin(\pi)=0", "corregida"),           # el modelo «arregló» el original: alucinación de fidelidad
    ("cos(0)=1", "no_leida"),
])
def test_fidelidad(salida, estado):
    f = fidelidad(salida, [TRAMPA])
    assert f["detalle"][0]["estado"] == estado and f["fieles"] + f["corregidas"] + f["no_leidas"] == 1


def test_fidelidad_division_entre_uno():
    t = {"descripcion": "/1", "literal": r"\frac{\cos(h)-1}{1}", "corregido": r"\frac{\cos(h)-1}{h}"}
    assert fidelidad("cos(t)(cos(h)-1)/1 - sin(t)", [t])["fieles"] == 1
    assert fidelidad(r"\cos(t)\left(\frac{\cos(h)-1}{h}\right)", [t])["corregidas"] == 1


def test_reevaluar_sin_gpu(tmp_path):
    c = corpus(tmp_path, escritura="formula", lineas=[], latex=[r"\sin(\pi)=-1"], trampas=[TRAMPA])
    informe = tmp_path / "informe.json"
    informe.write_text(json.dumps({"resultados": [{"muestra": "foto1", "http": 200, "texto": r"\sin(\pi)=0",
                                                   "latex": None, "descripcion": None}]}), encoding="utf-8")
    fila = reevaluar(informe, c)["resultados"][0]
    assert fila["fidelidad"]["corregidas"] == 1 and fila["cobertura"] == 1.0  # parecido, pero NO fiel


def test_notacion_equivalente():
    assert notacion_equivalente(r"\frac{a}{b} + \sqrt{x + 1}") == notacion_equivalente("a/b + sqrt(x + 1)")
    assert notacion_equivalente(r"\frac{a+1}{b}") == "(a+1)/b"
    assert notacion_equivalente(r"\frac{a}{b}") != notacion_equivalente(r"\frac{b}{a}")
