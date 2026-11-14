"""Apunte estructurado a partir del documento editado (BACK-19).

Organiza el contenido del apunte en portada, índice, secciones, resumen,
conceptos clave, ejemplos, fórmulas, tablas y esquemas. Regla de fidelidad: NO
se escribe ningún hecho nuevo. Todo sale del documento:

  - secciones: a partir de los bloques «titulo» (o una sola sección);
  - resumen: frases EXTRAÍDAS del apunte (las más representativas), no
    redactadas;
  - conceptos clave: términos frecuentes del apunte; el glosario solo incluye
    definiciones que el apunte escribe («X: …», «X es …»);
  - tabla comparativa: solo con datos del apunte (sus tablas o su glosario);
  - complementos investigados: SOLO los aceptados, en una sección aparte y
    citados con su fuente.
Es una función pura: se puede regenerar de cualquier versión sin perder nada.
"""

import re
from collections import Counter
from dataclasses import asdict, dataclass, field

from app.services.documento import Documento

STOPWORDS = set("""a al algo algunas algunos ante antes como con contra cual cuando de del desde donde dos el ella
ellas ellos en entre era es esa esas ese eso esos esta estas este esto estos fue fueron ha hay la las le les lo los
mas más me mi muy no nos o otra otro para pero por porque que qué se sea ser si sí sin sobre son su sus también
tiene todo todos tu un una unas uno unos y ya ejemplo entonces cada puede pueden mismo misma así""".split())

PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{4,}")
DEFINICION = re.compile(r"^\s*([A-ZÁÉÍÓÚÑ][\wáéíóúñÁÉÍÓÚÑ ]{2,40}?)\s*(?::|\ses\s|\sson\s)\s*(.{10,300})$")


@dataclass
class Seccion:
    titulo: str
    bloques: list[dict] = field(default_factory=list)


@dataclass
class ApunteEstructurado:
    titulo: str
    paginas: int
    tipo_fuente: str
    secciones: list[Seccion]
    resumen: list[str]
    conceptos: list[str]
    glosario: list[dict]
    ejemplos: list[str]
    formulas: list[dict]
    tablas: list[dict]
    esquemas: list[dict]
    pendientes: int                      # bloques sin texto: se incluyen como imagen
    complementos: list[dict]             # ampliaciones aceptadas, con fuente
    avisos: list[str]

    def a_dict(self) -> dict:
        return asdict(self)


def _frases(texto: str) -> list[str]:
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+|\n", texto) if len(f.strip()) >= 15]


def _palabras(texto: str) -> list[str]:
    return [p.lower() for p in PALABRA.findall(texto) if p.lower() not in STOPWORDS]


def resumen_extractivo(frases: list[str], maximo: int = 3) -> list[str]:
    """Las frases con más términos frecuentes del apunte, en su orden original."""
    if len(frases) <= maximo:
        return frases
    frecuencia = Counter(p for f in frases for p in _palabras(f))
    puntuadas = sorted(range(len(frases)),
                       key=lambda i: -sum(frecuencia[p] for p in _palabras(frases[i])) / (1 + len(_palabras(frases[i])) ** 0.5))
    return [frases[i] for i in sorted(puntuadas[:maximo])]


def es_ia(b) -> bool:
    """El bloque lo propuso el servidor IA (BACK-37): nunca es una transcripción confirmada."""
    return bool(b.procedencia and b.procedencia.motor == "ia_remota")


def estructurar(doc: Documento, tipo_fuente: str = "") -> ApunteEstructurado:
    bloques = sorted(doc.bloques, key=lambda b: b.orden)
    secciones: list[Seccion] = []
    actual = Seccion("Contenido")
    textos, ejemplos, formulas, tablas, esquemas, glosario = [], [], [], [], [], []
    pendientes = 0
    for b in bloques:
        if b.tipo == "titulo" and b.texto.strip():
            if actual.bloques or secciones:
                secciones.append(actual)
            actual = Seccion(b.texto.strip())
            continue
        datos = {"id": b.id, "tipo": b.tipo, "texto": b.texto, "latex": b.latex if b.latex_valido is not False else None,
                 "tabla": b.tabla.model_dump() if b.tabla else None, "recorte": b.recorte,
                 "estado": b.estado, "editado": b.editado, "pagina": b.pagina,
                 "ia": es_ia(b), "revisado": b.revisado}
        actual.bloques.append(datos)
        # BACK-38: lo derivado (resumen, glosario, ejemplos, fórmulas) solo sale de lo confirmado; una
        # propuesta del servidor IA sin revisar ni corregir aparece en la transcripción, marcada, y nada más.
        if es_ia(b) and not b.revisado and not b.editado:
            pendientes += b.tipo == "manuscrito" and not b.texto
            continue
        if b.tipo == "formula":
            formulas.append({"texto": b.texto, "latex": datos["latex"], "recorte": b.recorte})
        elif b.tipo == "tabla" and b.tabla:
            tablas.append({"titulo": actual.titulo, **b.tabla.model_dump()})
        elif b.tipo in ("imagen", "manuscrito") and not b.texto:
            pendientes += b.tipo == "manuscrito"
            if b.tipo == "imagen":
                esquemas.append({"recorte": b.recorte, "seccion": actual.titulo})
        elif b.texto:
            textos.append(b.texto)
            for linea in b.texto.split("\n"):
                limpia = linea.strip()
                if re.match(r"^(ejemplo|ej\.)\b", limpia, re.I):
                    ejemplos.append(limpia)
                m = DEFINICION.match(limpia)
                if m and not re.match(r"^(ejemplo|ej\.|nota|tarea)\b", limpia, re.I):
                    glosario.append({"concepto": m.group(1).strip(), "definicion": m.group(2).strip()})
    secciones.append(actual)
    secciones = [s for s in secciones if s.bloques or s.titulo != "Contenido"]

    frases = [f for t in textos for f in _frases(t)]
    frecuencia = Counter(p for t in textos for p in _palabras(t))
    conceptos = [p for p, n in frecuencia.most_common(12) if n >= 2][:8]
    # Tabla derivada del glosario: solo si el apunte define al menos dos conceptos.
    if len(glosario) >= 2:
        tablas.append({"titulo": "Conceptos definidos en el apunte", "encabezados": ["Concepto", "Definición"],
                       "filas": [[g["concepto"], g["definicion"]] for g in glosario]})
    avisos = []
    inciertos = sum(b.estado == "incierto" for b in bloques)
    if inciertos:
        avisos.append(f"{inciertos} bloque(s) tienen reconocimiento incierto: revísalos antes de compartir el PDF.")
    if pendientes:
        avisos.append(f"{pendientes} fragmento(s) no se pudieron leer y se incluyen como imagen.")
    ia_sin_revisar = sum(es_ia(b) and not b.revisado and not b.editado and bool(b.texto or b.latex) for b in bloques)
    if ia_sin_revisar:
        avisos.append(f"{ia_sin_revisar} bloque(s) son propuestas del servidor IA sin revisar: se incluyen junto a "
                      "su recorte de la foto; compáralos antes de compartir el PDF.")
    complementos = [{"concepto": a.concepto, "texto": a.texto, "fuente": a.fuente.model_dump(),
                     "discrepancia": a.discrepancia}
                    for a in doc.ampliaciones if a.estado == "aceptada"]
    return ApunteEstructurado(
        titulo=doc.titulo, paginas=len(doc.paginas),
        tipo_fuente=tipo_fuente or (doc.paginas[0].tipo_fuente if doc.paginas else ""),
        secciones=secciones, resumen=resumen_extractivo(frases), conceptos=conceptos, glosario=glosario,
        ejemplos=ejemplos, formulas=formulas, tablas=tablas, esquemas=esquemas, pendientes=pendientes,
        complementos=complementos, avisos=avisos)
