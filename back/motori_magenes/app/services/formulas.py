"""Fórmulas: detección, conversión a LaTeX y verificación segura (BACK-15).

1. Detección: una línea es fórmula si su densidad de símbolos matemáticos es
   alta y casi no tiene palabras (las fórmulas dentro de una frase se quedan
   como texto).
2. Conversión: analizador sintáctico propio (descenso recursivo) que entiende
   operaciones, fracciones con «/», potencias (^, ², ³), subíndices (x_1), raíces
   (sqrt, √), funciones, sumatorias e integrales simples, y produce LaTeX. NO usa
   eval, sympy.parse_expr ni nada que ejecute la entrada.
3. Verificación: todo LaTeX (generado o escrito por el usuario) pasa por una
   lista blanca de comandos y se dibuja con mathtext de matplotlib, que no es un
   motor TeX (no hay \\input, \\write ni ejecución de órdenes). Si no se puede
   dibujar, la fórmula es inválida y se conserva su imagen.
"""

import io
import re
import threading
import unicodedata

from app.core.errores import ApiError

MAX_LATEX = 500

FUNCIONES = {"sin": r"\sin", "sen": r"\sin", "cos": r"\cos", "tan": r"\tan", "log": r"\log", "ln": r"\ln",
             "exp": r"\exp", "lim": r"\lim"}
GRIEGAS = {"alpha", "beta", "gamma", "delta", "epsilon", "theta", "lambda", "mu", "pi", "rho", "sigma", "tau",
           "phi", "omega", "Delta", "Sigma", "Omega", "Pi", "Theta", "Gamma", "Lambda", "Phi"}
SIMBOLOS_UNICODE = {"π": "pi", "α": "alpha", "β": "beta", "θ": "theta", "Δ": "Delta", "λ": "lambda", "μ": "mu",
                    "σ": "sigma", "ω": "omega", "∞": "infty"}
RELACIONES = {"=": "=", "<": "<", ">": ">", "≤": r"\leq", "≥": r"\geq", "≠": r"\neq", "≈": r"\approx",
              "<=": r"\leq", ">=": r"\geq", "!=": r"\neq"}

COMANDOS_PERMITIDOS = {
    "frac", "sqrt", "sum", "int", "iint", "oint", "lim", "infty", "cdot", "times", "div", "pm", "mp", "leq", "geq",
    "neq", "approx", "equiv", "sim", "propto", "to", "rightarrow", "leftarrow", "Rightarrow", "Leftrightarrow",
    "sin", "cos", "tan", "log", "ln", "exp", "partial", "nabla", "prime", "ldots", "cdots", "left", "right",
    "mathrm", "mathbf", "mathit", "in", "notin", "subset", "cup", "cap", "forall", "exists", "circ", "degree",
    "quad", "qquad", "langle", "rangle", "vert", "lfloor", "rfloor", "lceil", "rceil", "overline", "hat", "vec",
    "bar", "dot", "ddot", "tilde", "prod", "max", "min", "det", "deg", "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh", "mid", "angle", "perp", "parallel", "emptyset", "mathbb",
} | GRIEGAS | {g.lower() for g in GRIEGAS} | {"varepsilon", "varphi", "eta", "zeta", "xi", "chi", "psi", "nu", "kappa",
                                              "iota", "upsilon", "Psi", "Xi", "Upsilon"}


class ErrorFormula(ValueError):
    pass


# ------------------------------------------------------------------ detección

_SIMBOLOS_MAT = set("=+-*/^√∫∑Σ²³<>≤≥≠≈()π_")


_NO_PALABRAS = {"sqrt", "lim", "int", "sum", "dx", "dy", "dt", "dz", "mc", "infty", "inf"}


def es_formula(linea: str) -> bool:
    texto = normalizar(linea)
    if len(texto) < 2:
        return False
    # Palabras de 2+ letras que no son funciones, letras griegas ni diferenciales:
    # dos o más indican una frase con matemáticas dentro, no una fórmula.
    palabras = [p for p in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]{2,}", texto)
                if p.lower() not in FUNCIONES and p.lower() not in _NO_PALABRAS
                and p not in GRIEGAS and p.lower() not in {g.lower() for g in GRIEGAS}]
    if len(palabras) >= 2 or any(len(p) >= 4 for p in palabras):
        return False
    simbolos = sum(c in _SIMBOLOS_MAT for c in texto)
    # Igualdad corta entre variables («F = ma», «v = d/t»): sin palabras de más de 2 letras.
    igualdad_corta = ("=" in texto and len(texto.replace(" ", "")) <= 25
                      and all(len(p) <= 2 for p in palabras) and re.search(r"[A-Za-z0-9]\s*=\s*[A-Za-z0-9(]", texto))
    return bool(simbolos >= 2 and "=" in texto or simbolos >= 3 or igualdad_corta
                or any(s in texto for s in ("√", "∫", "∑", "Σ", "sqrt(")))


# ------------------------------------------------------------------ normalización del OCR

def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFC", texto).strip().rstrip(".,;")
    t = re.sub(r"[\"”“’'`]\s*(\d)", r"^\1", t)          # «x"2» o «c”2»: comillas leídas en vez de ^
    t = t.replace("−", "-").replace("×", "*").replace("·", "*").replace("÷", "/")
    t = re.sub(r"=\s*-\s*=", "=", t).replace("-=", "=").replace("==", "=")
    t = t.replace("²", "^2").replace("³", "^3")
    t = re.sub(r"([A-Za-z)])\*(\d)", r"\1^\2", t)  # «x*2» sin espacios: el OCR suele leer ^ como *
    for u, nombre in SIMBOLOS_UNICODE.items():
        t = t.replace(u, f" {nombre} ")
    return t


# ------------------------------------------------------------------ analizador

TOKEN = re.compile(r"\s*(?:(\d+(?:[.,]\d+)?)|([A-Za-z]+)|(<=|>=|!=|[=<>≤≥≠≈])|(.))")


def _tokens(texto: str) -> list[tuple[str, str]]:
    salida, pos = [], 0
    texto = texto.strip()
    while pos < len(texto):
        m = TOKEN.match(texto, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        num, nombre, rel, otro = m.groups()
        if num:
            salida.append(("num", num.replace(",", ".")))
        elif nombre:
            salida.append(("nom", nombre))
        elif rel:
            salida.append(("rel", rel))
        elif otro and not otro.isspace():
            salida.append(("sim", otro))
    return salida


class _Analizador:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def ver(self, n=0):
        return self.t[self.i + n] if self.i + n < len(self.t) else (None, None)

    def tomar(self, tipo=None, valor=None):
        tk = self.ver()
        if tk[0] is None or (tipo and tk[0] != tipo) or (valor and tk[1] != valor):
            raise ErrorFormula(f"se esperaba {valor or tipo}")
        self.i += 1
        return tk

    def ecuacion(self) -> str:
        partes = [self.expresion()]
        while self.ver()[0] == "rel":
            partes.append(RELACIONES[self.tomar()[1]])
            partes.append(self.expresion())
        if self.ver()[0] is not None:
            raise ErrorFormula(f"símbolo inesperado «{self.ver()[1]}»")
        return " ".join(partes)

    def expresion(self) -> str:
        if self.ver() == ("sim", "-"):
            self.tomar()
            salida = "-" + self.termino()
        else:
            salida = self.termino()
        while self.ver() in (("sim", "+"), ("sim", "-")):
            op = self.tomar()[1]
            salida += f" {op} " + self.termino()
        return salida

    def termino(self) -> str:
        factores = [self.potencia()]
        while True:
            tk = self.ver()
            if tk == ("sim", "*"):
                self.tomar()
                factores.append(r"\cdot")
                factores.append(self.potencia())
            elif tk == ("sim", "/"):
                self.tomar()
                denominador = self.potencia()
                numerador = factores.pop()
                factores.append(r"\frac{" + _sin_parentesis(numerador) + "}{" + _sin_parentesis(denominador) + "}")
            elif tk[0] in ("num", "nom") or tk in (("sim", "("), ("sim", "√"), ("sim", "∫"), ("sim", "∑"), ("sim", "Σ")):
                factores.append(self.potencia())  # multiplicación implícita: 2x, mc
            else:
                break
        return " ".join(factores)

    def potencia(self) -> str:
        base = self.primario()
        while self.ver() == ("sim", "'"):
            self.tomar()
            base += "'"
        if self.ver() == ("sim", "_"):
            self.tomar()
            base += "_{" + _sin_parentesis(self.primario()) + "}"
        if self.ver() == ("sim", "^"):
            self.tomar()
            exponente = "-" + self.primario() if self.ver() == ("sim", "-") and self.tomar() else self.primario()
            base += "^{" + _sin_parentesis(exponente) + "}"
        return base

    def argumento(self) -> str:
        self.tomar("sim", "(")
        dentro = self.expresion()
        self.tomar("sim", ")")
        return dentro

    def primario(self) -> str:
        tipo, valor = self.ver()
        if tipo == "num":
            return self.tomar()[1]
        if (tipo, valor) == ("sim", "("):
            return r"\left(" + self.argumento() + r"\right)"
        if (tipo, valor) == ("sim", "√"):
            self.tomar()
            return r"\sqrt{" + _sin_parentesis(self.primario()) + "}"
        if (tipo, valor) in (("sim", "∫"),):
            self.tomar()
            return r"\int"
        if (tipo, valor) in (("sim", "∑"), ("sim", "Σ")):
            self.tomar()
            return r"\sum"
        if tipo == "nom":
            self.tomar()
            bajo = valor.lower()
            if bajo == "sqrt":
                return r"\sqrt{" + self.argumento() + "}"
            if bajo in ("int", "integral"):
                return r"\int"
            if bajo in ("sum", "suma"):
                return r"\sum"
            if bajo == "infty" or bajo == "inf":
                return r"\infty"
            if bajo == "lim":
                # El límite se aplica a todo lo que sigue (p. ej. a una fracción).
                return r"\lim"
            if bajo in FUNCIONES:
                if self.ver() == ("sim", "("):
                    return FUNCIONES[bajo] + r"\left(" + self.argumento() + r"\right)"
                return FUNCIONES[bajo]
            if valor in GRIEGAS or bajo in {g.lower() for g in GRIEGAS}:
                return "\\" + (valor if valor in GRIEGAS else bajo)
            if self.ver() == ("sim", "(") and len(valor) == 1:  # f(x)
                return valor + r"\left(" + self.argumento() + r"\right)"
            if len(valor) > 1:   # «mc» → m c (producto de variables)
                return " ".join(valor)
            return valor
        raise ErrorFormula(f"no se esperaba «{valor}»" if valor else "la fórmula está incompleta")


def _sin_parentesis(latex: str) -> str:
    """Quita un par de paréntesis exteriores si envuelven TODA la expresión."""
    abre, cierra = r"\left(", r"\right)"
    if not (latex.startswith(abre) and latex.endswith(cierra)):
        return latex
    profundidad, i = 0, 0
    while i < len(latex):
        if latex.startswith(abre, i):
            profundidad += 1
            i += len(abre)
        elif latex.startswith(cierra, i):
            profundidad -= 1
            i += len(cierra)
            if profundidad == 0 and i < len(latex):
                return latex  # el primer paréntesis se cierra antes del final: no envuelve todo
        else:
            i += 1
    return latex[len(abre):-len(cierra)]


def a_latex(texto: str) -> str:
    """Convierte una fórmula escrita en texto lineal a LaTeX. Lanza ErrorFormula."""
    tokens = _tokens(normalizar(texto))
    if not tokens:
        raise ErrorFormula("fórmula vacía")
    return _Analizador(tokens).ecuacion()


# ------------------------------------------------------------------ verificación

_COMANDO = re.compile(r"\\([A-Za-z]+)")
_bloqueo_render = threading.Lock()  # matplotlib no es seguro entre hilos


def comprobar_seguridad(latex: str) -> None:
    if len(latex) > MAX_LATEX:
        raise ApiError(400, "LATEX_INVALIDO", f"La fórmula supera los {MAX_LATEX} caracteres.")
    if "$" in latex or "%" in latex or "\n" in latex:
        raise ApiError(400, "LATEX_NO_PERMITIDO", "La fórmula contiene caracteres no permitidos ($, % o saltos de línea).")
    prohibidos = sorted({c for c in _COMANDO.findall(latex) if c not in COMANDOS_PERMITIDOS})
    if prohibidos:
        raise ApiError(400, "LATEX_NO_PERMITIDO",
                       "Comandos no permitidos en la fórmula: " + ", ".join("\\" + c for c in prohibidos[:5]) + ".")
    profundidad = 0
    for c in latex:
        profundidad += (c == "{") - (c == "}")
        if profundidad < 0:
            break
    if profundidad != 0:
        raise ApiError(400, "LATEX_INVALIDO", "Las llaves { } de la fórmula no están equilibradas.")


def renderizar_png(latex: str, dpi: int = 200) -> bytes:
    """Dibuja la fórmula con mathtext (sin motor TeX). Lanza ApiError si no es válida."""
    comprobar_seguridad(latex)
    from matplotlib import mathtext
    from matplotlib.font_manager import FontProperties
    buffer = io.BytesIO()
    try:
        with _bloqueo_render:
            mathtext.math_to_image(f"${latex}$", buffer, dpi=dpi, format="png",
                                   prop=FontProperties(size=14, family="DejaVu Sans"))
    except Exception as exc:  # noqa: BLE001 — mathtext lanza ValueError/ParseException variados
        raise ApiError(400, "LATEX_INVALIDO", "La fórmula no se puede dibujar: revisa su sintaxis.") from exc
    return buffer.getvalue()


def validar_latex(latex: str) -> tuple[bool, list[str]]:
    try:
        renderizar_png(latex, dpi=72)
        return True, []
    except ApiError as exc:
        return False, [exc.mensaje]


def convertir(texto: str) -> tuple[str | None, bool]:
    """(latex, válido) para un texto de fórmula; (None, False) si no se entiende."""
    try:
        latex = a_latex(texto)
    except ErrorFormula:
        return None, False
    valido, _ = validar_latex(latex)
    return latex, valido


# ------------------------------------------------------------------ integración con el OCR

def separar_formulas(bloques):
    """Separa las líneas de fórmula de los bloques del OCR (BloqueOCR).

    Una línea de fórmula se convierte en su propio bloque «formula», con LaTeX si
    se pudo convertir y verificar. Siempre conserva el recorte de la imagen, y su
    estado es «incierto» si la conversión falló o el OCR dudó: una fórmula no se
    da por buena sin poder compararla con la foto.
    """
    from app.services.ocr import BloqueOCR
    salida = []
    for b in bloques:
        if not b.texto or b.tipo in ("imagen", "manuscrito") and not b.texto:
            salida.append(b)
            continue
        if b.tipo == "formula" and getattr(b, "latex", None) is not None:
            salida.append(b)  # ya la leyó el lector de fórmulas (BACK-28): no se vuelve a convertir
            continue
        lineas = b.texto.split("\n")
        marcas = [es_formula(l) for l in lineas]
        if not any(marcas):
            salida.append(b)
            continue
        alto = (b.bbox[3] - b.bbox[1]) / len(lineas)
        grupo, tipo_grupo, inicio = [], None, 0
        for i, (linea, es_f) in enumerate(zip(lineas + [None], marcas + [None])):
            if linea is not None and (tipo_grupo is None or es_f == tipo_grupo) and not (es_f and grupo):
                if tipo_grupo is None:
                    inicio = i
                grupo.append(linea)
                tipo_grupo = es_f
                continue
            if grupo:
                caja = [b.bbox[0], int(b.bbox[1] + inicio * alto), b.bbox[2], int(b.bbox[1] + (inicio + len(grupo)) * alto)]
                texto = "\n".join(grupo)
                if tipo_grupo:
                    latex, valido = convertir(texto)
                    # Solo «reconocida» si se convirtió y el OCR no dudó de ninguna palabra (≥ 0.90):
                    # una fórmula no se da por buena sin poder compararla con la foto.
                    minima = b.minima if b.minima is not None else b.confianza
                    segura = valido and min(b.confianza, minima) >= 0.90
                    conf = b.confianza if segura else min(b.confianza, 0.79)
                    nuevo = BloqueOCR(texto, conf, caja, grupo,
                                      b.altura_linea, "formula", b.dudosas, recortar=True, minima=minima,
                                      procedencia=dict(b.procedencia), revision=b.revision)
                    nuevo.latex, nuevo.latex_valido = latex, valido
                else:
                    nuevo = BloqueOCR(texto, b.confianza, caja, grupo, b.altura_linea,
                                      b.tipo if b.tipo != "formula" else "texto", b.dudosas, b.recortar,
                                      minima=b.minima, procedencia=dict(b.procedencia), revision=b.revision,
                                      alternativas=b.alternativas if len(lineas) == len(grupo) else [])
                salida.append(nuevo)
            if linea is not None:
                grupo, tipo_grupo, inicio = [linea], es_f, i
        # (el centinela None cierra el último grupo)
    return salida
