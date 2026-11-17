"""Cómo se lee una fórmula: de LaTeX a una frase en español, sin IA.

Va en el PDF debajo de cada fórmula dibujada («Se lee: v es igual a la derivada de x respecto a
t»). Sirve para estudiarla en voz alta y para comprobar de un vistazo que se transcribió bien: si
la frase no coincide con lo que escribiste, la fórmula está mal leída.

Es una traducción mecánica del LaTeX ya validado: no interpreta el tema ni añade ningún hecho
(la regla de fidelidad del apunte). Si la fórmula usa algo que este módulo no sabe leer, devuelve
None y no se escribe nada: mejor ninguna frase que una frase rara.
"""

from __future__ import annotations

import re

GRIEGAS = {"alpha": "alfa", "beta": "beta", "gamma": "gamma", "delta": "delta", "epsilon": "épsilon",
           "varepsilon": "épsilon", "zeta": "zeta", "eta": "eta", "theta": "theta", "iota": "iota", "kappa": "kappa",
           "lambda": "lambda", "mu": "mu", "nu": "nu", "xi": "xi", "pi": "pi", "rho": "rho", "sigma": "sigma",
           "tau": "tau", "upsilon": "ípsilon", "phi": "fi", "varphi": "fi", "chi": "ji", "psi": "psi", "omega": "omega"}
FUNCIONES = {"sin": "seno de", "cos": "coseno de", "tan": "tangente de", "sec": "secante de", "csc": "cosecante de",
             "cot": "cotangente de", "arcsin": "arcoseno de", "arccos": "arcocoseno de", "arctan": "arcotangente de",
             "sinh": "seno hiperbólico de", "cosh": "coseno hiperbólico de", "tanh": "tangente hiperbólica de",
             "ln": "logaritmo natural de", "log": "logaritmo de", "exp": "exponencial de", "max": "máximo de",
             "min": "mínimo de", "det": "determinante de", "deg": "grado de"}
SIMBOLOS = {"cdot": "por", "times": "por", "div": "entre", "pm": "más o menos", "mp": "menos o más",
            "leq": "menor o igual que", "geq": "mayor o igual que", "neq": "distinto de",
            "approx": "aproximadamente igual a", "equiv": "equivalente a", "sim": "semejante a",
            "propto": "proporcional a", "to": "tiende a", "rightarrow": "tiende a", "leftarrow": "viene de",
            "Rightarrow": "implica", "Leftrightarrow": "si y solo si", "infty": "infinito", "nabla": "nabla",
            "in": "pertenece a", "notin": "no pertenece a", "subset": "es subconjunto de", "cup": "unión",
            "cap": "intersección", "forall": "para todo", "exists": "existe", "circ": "grados", "degree": "grados",
            "ldots": "etcétera", "cdots": "etcétera", "prime": "prima", "angle": "ángulo",
            "perp": "perpendicular a", "parallel": "paralelo a", "emptyset": "conjunto vacío", "mid": "tal que",
            "quad": ";", "qquad": ";", "langle": "(", "rangle": ")", "vert": "|", "partial": "parcial"}
OPERADORES = {"=": "es igual a", "+": "más", "-": "menos", "*": "por", "/": "entre", "<": "menor que",
              ">": "mayor que", ",": ",", "!": "factorial", "'": "prima", ";": ";", ":": ":"}
IGNORAR = {"left", "right", "displaystyle", ",", ";", "!", " ", ":"}          # \left( \, \; \! \  …
ENVOLTORIOS = {"mathrm", "mathbf", "mathit", "text", "mathbb", "operatorname"}  # su contenido, tal cual
ACENTOS = {"hat": "{} gorro", "vec": "el vector {}", "bar": "{} barra", "overline": "{} barra", "dot": "{} punto",
           "ddot": "{} dos puntos", "tilde": "{} tilde"}
ORDINALES = {2: "segunda ", 3: "tercera ", 4: "cuarta "}
MAX_FRASE = 400

_TOKEN = re.compile(r"\\[A-Za-z]+|\\.|[{}^_\[\]]|\d+(?:[.,]\d+)?|[A-Za-z]|\S")


class _NoSe(Exception):
    """Algo que no se sabe leer: la fórmula se queda sin frase."""


class _Lector:
    def __init__(self, tokens: list[str]):
        self.t, self.i = tokens, 0

    def ver(self, k: int = 0) -> str | None:
        return self.t[self.i + k] if self.i + k < len(self.t) else None

    def tomar(self) -> str:
        tok = self.ver()
        if tok is None:
            raise _NoSe("fin inesperado")
        self.i += 1
        return tok

    # -------------------------------------------------------------- grupos y secuencias
    def tokens_grupo(self) -> list[str]:
        """Los tokens del siguiente argumento: {…} o un solo símbolo."""
        if self.ver() == "{":
            self.tomar()
            inicio, nivel = self.i, 1
            while nivel:
                tok = self.tomar()
                nivel += (tok == "{") - (tok == "}")
            return self.t[inicio:self.i - 1]
        tok = self.tomar()
        if tok in ("}", "^", "_"):
            raise _NoSe("argumento vacío")
        return [tok]

    def secuencia(self) -> list[str]:
        partes: list[str] = []
        while self.ver() is not None:
            tok = self.ver()
            if tok == "^":
                self.tomar()
                partes.append(_potencia(_frase(self.tokens_grupo())))
            elif tok == "_":
                self.tomar()
                partes.append("sub " + _frase(self.tokens_grupo()))
            else:
                partes.append(self.elemento())
                # x(t), el vector r(t), i gorro(u): una variable aplicada a UN argumento se lee «x de t»
                if (_es_variable(partes[-1]) and self.ver() == "(" and self.ver(2) == ")"
                        and (self.ver(1) or "").isalnum()):
                    partes[-1] += " de " + self.ver(1)
                    self.i += 3
        return partes

    # -------------------------------------------------------------- un elemento
    def elemento(self) -> str:
        tok = self.tomar()
        if tok == "{":
            self.i -= 1
            return _frase(self.tokens_grupo())
        if tok == "}":
            raise _NoSe("llave sin abrir")
        if not tok.startswith("\\"):
            if tok[0].isdigit() or tok.isalpha() or tok in "()[]|":
                return tok
            if tok in OPERADORES:
                return OPERADORES[tok]
            raise _NoSe(tok)
        nombre = tok[1:]
        if nombre in IGNORAR:
            return ""
        if nombre == "frac" or nombre == "dfrac":
            return _fraccion(self.tokens_grupo(), self.tokens_grupo())
        if nombre == "sqrt":
            indice = None
            if self.ver() == "[":
                self.tomar()
                inicio = self.i
                while self.ver() not in ("]", None):
                    self.tomar()
                indice = _frase(self.t[inicio:self.i])
                self.tomar()
            radicando = _frase(self.tokens_grupo())
            tipo = {None: "cuadrada", "2": "cuadrada", "3": "cúbica"}.get(indice)
            return f"la raíz {tipo} de {radicando}" if tipo else f"la raíz de índice {indice} de {radicando}"
        if nombre in ACENTOS:
            return ACENTOS[nombre].format(_frase(self.tokens_grupo()))
        if nombre in ENVOLTORIOS:
            return _frase(self.tokens_grupo(), literal=True)
        if nombre in ("int", "iint", "oint", "sum", "prod", "lim"):
            return self._con_limites(nombre)
        if nombre in FUNCIONES:
            return FUNCIONES[nombre]
        if nombre in GRIEGAS:
            return GRIEGAS[nombre]
        if nombre[:1].isupper() and nombre.lower() in GRIEGAS:
            return "delta" if nombre == "Delta" else GRIEGAS[nombre.lower()] + " mayúscula"
        if nombre in SIMBOLOS:
            return SIMBOLOS[nombre]
        raise _NoSe(nombre)

    def _con_limites(self, nombre: str) -> str:
        abajo = arriba = None
        for _ in range(2):
            if self.ver() == "_":
                self.tomar()
                abajo = _frase(self.tokens_grupo())
            elif self.ver() == "^":
                self.tomar()
                arriba = _frase(self.tokens_grupo())
        if nombre == "lim":
            return f"el límite cuando {abajo} de" if abajo else "el límite de"
        base = {"int": "la integral", "iint": "la integral doble", "oint": "la integral cerrada",
                "sum": "la sumatoria", "prod": "el producto"}[nombre]
        if abajo and arriba:
            return f"{base} desde {abajo} hasta {arriba} de"
        return f"{base} sobre {abajo} de" if abajo else f"{base} de"


def _es_variable(parte: str) -> bool:
    return ((len(parte) == 1 and parte.isalpha()) or parte.endswith((" gorro", " barra", " punto", " tilde"))
            or parte.startswith("el vector "))


def _potencia(exponente: str) -> str:
    return {"2": "al cuadrado", "3": "al cubo", "menos 1": "a la menos uno"}.get(exponente, f"elevado a {exponente}")


_DERIVADA_ARRIBA = re.compile(r"^(d|\\partial)(?:\^\{?(\d)\}?)?(.*)$")
_DERIVADA_ABAJO = re.compile(r"^(d|\\partial)(\\?[A-Za-z]+?)(?:\^\{?(\d)\}?)?$")


def _fraccion(arriba: list[str], abajo: list[str]) -> str:
    """dx/dt → derivada; lo demás, una fracción."""
    a, b = "".join(arriba), "".join(abajo)
    ma, mb = _DERIVADA_ARRIBA.match(a), _DERIVADA_ABAJO.match(b)
    if ma and mb and ma.group(1) == mb.group(1):
        orden = int(ma.group(2) or mb.group(3) or 1)
        parcial = "parcial " if ma.group(1) == "\\partial" else ""
        respecto = _frase(_TOKEN.findall(mb.group(2)))
        nombre = f"la {ORDINALES.get(orden, f'derivada de orden {orden} ')}derivada" if orden > 1 else "la derivada"
        if orden > 4:
            nombre = f"la derivada de orden {orden}"
        de = _frase(_TOKEN.findall(ma.group(3))) if ma.group(3) else ""
        return f"{nombre} {parcial}de {de} respecto a {respecto}" if de else f"{nombre} {parcial}respecto a {respecto} de"
    num, den = _frase(arriba), _frase(abajo)
    if " " not in num and " " not in den:
        return f"{num} entre {den}"
    return f"la fracción de numerador {num} y denominador {den}"


def _frase(tokens: list[str], literal: bool = False) -> str:
    if literal:   # \text{…}, \mathrm{…}: el contenido tal cual (con los espacios «\ »)
        return re.sub(r"\s+", " ", "".join(" " if t == "\\ " else t for t in tokens)).strip()
    return " ".join(p for p in _Lector(tokens).secuencia() if p)


def leer_formula(latex: str | None) -> str | None:
    """Frase en español de cómo se lee `latex`, o None si no se sabe leer entera."""
    if not latex or not latex.strip():
        return None
    try:
        frase = _frase(_TOKEN.findall(latex.replace("\\ ", " \\  ")))
    except (_NoSe, RecursionError):
        return None
    frase = re.sub(r"\( ", "(", re.sub(r" \)", ")", frase))
    frase = re.sub(r"\s+([,;:])", r"\1", re.sub(r"\s+", " ", frase)).strip(" ;,")
    frase = re.sub(r"\b(la|el) (la|el) ", r"\2 ", frase)
    if not frase or len(frase) > MAX_FRASE:
        return None
    return frase   # sin mayúscula inicial: «v» y «V» son variables distintas
