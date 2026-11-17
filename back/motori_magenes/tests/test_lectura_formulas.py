"""Cómo se lee una fórmula (PDF): de LaTeX a español, sin IA."""

import pytest

from app.services.lectura_formulas import leer_formula


@pytest.mark.parametrize("latex, frase", [
    (r"v = \frac{dx}{dt}", "v es igual a la derivada de x respecto a t"),
    (r"a = \frac{d^2x}{dt^2}", "a es igual a la segunda derivada de x respecto a t"),
    (r"\frac{\partial f}{\partial x}", "la derivada parcial de f respecto a x"),
    (r"r(t) = x(t)\hat{i} + y(t)\hat{j}", "r de t es igual a x de t i gorro más y de t j gorro"),
    (r"\vec{v}(t) = (80t + 8)\hat{i}", "el vector v de t es igual a (80 t más 8) i gorro"),
    (r"E = mc^2", "E es igual a m c al cuadrado"),
    (r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
     "x es igual a la fracción de numerador menos b más o menos la raíz cuadrada de b al cuadrado menos 4 a c "
     "y denominador 2 a"),
    (r"\int_0^1 x^2 \, dx = \frac{1}{3}", "la integral desde 0 hasta 1 de x al cuadrado d x es igual a 1 entre 3"),
    (r"\lim_{x \to 0} \frac{\sin x}{x} = 1",
     "el límite cuando x tiende a 0 de la fracción de numerador seno de x y denominador x es igual a 1"),
    (r"t = 0 \quad x = 0", "t es igual a 0; x es igual a 0"),
    (r"y = 2\cos 3t", "y es igual a 2 coseno de 3 t"),
    (r"\Delta r = r(\mathrm{cut\ x})", "delta r es igual a r (cut x)"),
])
def test_lee_formulas_frecuentes(latex, frase):
    assert leer_formula(latex) == frase


@pytest.mark.parametrize("latex", [r"\foo{x}", r"\frac{a}", "", None, r"x^", "{" * 5])
def test_lo_que_no_sabe_leer_no_tiene_frase(latex):
    assert leer_formula(latex) is None
