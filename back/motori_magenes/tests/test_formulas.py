"""Fórmulas: detección, LaTeX y seguridad (BACK-15)."""

import os

import pytest

from app.core.errores import ApiError
from app.services.formulas import (a_latex, comprobar_seguridad, convertir, es_formula, renderizar_png,
                                   separar_formulas)
from app.services.ocr import BloqueOCR


@pytest.mark.parametrize("texto,latex", [
    ("x^2 + 2x + 1 = 0", r"x^{2} + 2 x + 1 = 0"),
    ("x² + 1", r"x^{2} + 1"),
    ('x"2+2x+1=-=0', r"x^{2} + 2 x + 1 = 0"),       # confusiones típicas del OCR
    ("x*2+1", r"x^{2} + 1"),
    ("a/b + c/d", r"\frac{a}{b} + \frac{c}{d}"),
    ("(x + 1)/(x - 1)", r"\frac{x + 1}{x - 1}"),
    ("sqrt(x + 1)", r"\sqrt{x + 1}"),
    ("√2", r"\sqrt{2}"),
    ("x_1 + x_2 = 3", r"x_{1} + x_{2} = 3"),
    ("E=mc”2", r"E = m c^{2}"),
    ("sin(x)^2 + cos(x)^2 = 1", r"\sin\left(x\right)^{2} + \cos\left(x\right)^{2} = 1"),
    ("f'(x) = lim (f(x+h) - f(x)) / h", r"f' \left(x\right) = \lim \frac{f\left(x + h\right) - f\left(x\right)}{h}"),
    ("Σ a_i", r"\sum a_{i}"),
    ("∫ f(x) dx", r"\int f\left(x\right) d x"),
    ("x <= 2", r"x \leq 2"),
    ("2π r", r"2 \pi r"),
])
def test_conversion_a_latex_dibujable(texto, latex):
    obtenido, valido = convertir(texto)
    assert obtenido == latex and valido


@pytest.mark.parametrize("texto,esperado", [
    ("x^2 + 2x + 1 = 0", True), ("a/b + c/d", True), ("√2", True), ("Σ a_i", True), ("E=mc”2", True),
    ("La derivada mide la razón de cambio.", False), ("Si f(x) = x², entonces f'(x) = 2x.", False),
    ("Derivadas", False), ("Ejemplo: 2 + 2", False),
])
def test_deteccion(texto, esperado):
    assert es_formula(texto) is esperado


def test_lo_que_no_se_entiende_no_se_inventa():
    assert convertir("x + + ) ( =") == (None, False)


def test_entrada_maliciosa_no_se_ejecuta(monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("se intentó ejecutar algo")
    monkeypatch.setattr(os, "system", prohibido)
    monkeypatch.setattr(os, "popen", prohibido)
    for texto in ["__import__('os').system('rm -rf /')", "eval(1)", "exec('x')", "open('/etc/passwd')"]:
        latex, _ = convertir(texto)  # el analizador solo produce texto LaTeX
        assert latex is None or "import" not in latex.replace(" ", "")


@pytest.mark.parametrize("latex,codigo", [
    (r"\input{/etc/passwd}", "LATEX_NO_PERMITIDO"),
    (r"\write18{rm -rf /}", "LATEX_NO_PERMITIDO"),
    (r"\def\x{1}", "LATEX_NO_PERMITIDO"),
    (r"\href{javascript:alert(1)}{x}", "LATEX_NO_PERMITIDO"),
    (r"$x$", "LATEX_NO_PERMITIDO"),
    ("x % comentario", "LATEX_NO_PERMITIDO"),
    (r"\frac{a}{b", "LATEX_INVALIDO"),
    ("x" * 600, "LATEX_INVALIDO"),
])
def test_latex_peligroso_o_invalido(latex, codigo):
    with pytest.raises(ApiError) as exc:
        renderizar_png(latex)
    assert exc.value.codigo == codigo


def test_render_png():
    png = renderizar_png(r"\frac{a}{b} + \sqrt{x}")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_separar_formulas_conserva_recorte_y_texto():
    b = BloqueOCR("Ejemplo de clase\nx^2 + 2x + 1 = 0\nFin", 0.95, [0, 0, 300, 300], [], 20)
    salida = separar_formulas([b])
    assert [x.tipo for x in salida] == ["texto", "formula", "texto"]
    f = salida[1]
    assert f.latex == r"x^{2} + 2 x + 1 = 0" and f.latex_valido and f.recortar and f.estado == "reconocido"
    assert f.bbox == [0, 100, 300, 200]


def test_formula_dudosa_queda_incierta():
    b = BloqueOCR("x*2+1=0", 0.85, [0, 0, 300, 100], [], 20)
    assert separar_formulas([b])[0].estado == "incierto"


def test_ruta_validar(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    ok = c.post("/api/v2/formulas/validar", json={"latex": r"\frac{1}{2}"}).json()
    assert ok["valida"] and ok["vista_previa"].startswith("data:image/png;base64,")
    malo = c.post("/api/v2/formulas/validar", json={"latex": r"\frac{1}{"}).json()
    assert malo["valida"] is False and malo["errores"]
    texto = c.post("/api/v2/formulas/validar", json={"texto": "a/b"}).json()
    assert texto["latex"] == r"\frac{a}{b}"
    assert c.post("/api/v2/formulas/validar", json={"latex": r"\input{x}"}).json()["error"]["codigo"] == "LATEX_NO_PERMITIDO"
    assert nuevo_cliente().post("/api/v2/formulas/validar", json={"latex": "x"}).status_code == 401
