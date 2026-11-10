"""Modelo intermedio editable de un apunte (BACK-17). Esquema: docs/api-v2.md §3.

Separa tres procedencias que nunca se mezclan:
  - lo que aparece en la foto (bloques con origen "ocr" y su texto_original),
  - lo que corrige o añade el usuario (editado=True / origen "usuario"),
  - lo investigado fuera (ampliaciones con fuente, siempre aparte).

`fusionar()` aplica las reglas de procedencia al guardar una edición: el
cliente puede cambiar texto, LaTeX, tablas y orden, pero no puede reescribir
lo que dijo la foto (texto_original, bbox, confianza…) ni inventar
ampliaciones o cambiar sus fuentes.
"""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.core.errores import ApiError

ESQUEMA = "apuntia.documento/1"
ID = r"^[A-Za-z0-9_-]{1,40}$"

TipoBloque = Literal["titulo", "texto", "manuscrito", "formula", "tabla", "imagen"]
EstadoBloque = Literal["reconocido", "incierto", "no_reconocido"]


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Pagina(Base):
    id: str = Field(pattern=ID)
    orden: int = Field(ge=1, le=500)
    tipo_fuente: Literal["pizarron", "cuaderno"]
    archivo_original: str = Field(pattern=ID)
    archivo_procesado: str | None = Field(default=None, pattern=ID)
    ancho: int = Field(ge=0, le=20000)
    alto: int = Field(ge=0, le=20000)
    advertencias: list[str] = Field(default_factory=list, max_length=20)
    error: str | None = Field(default=None, max_length=300)


class Tabla(Base):
    encabezados: list[str] = Field(min_length=1, max_length=30)
    filas: list[list[str]] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def columnas_consistentes(self):
        for i, fila in enumerate(self.filas):
            if len(fila) != len(self.encabezados):
                raise ValueError(f"la fila {i + 1} tiene {len(fila)} celdas y la tabla {len(self.encabezados)} columnas")
            if any(len(celda) > 2000 for celda in fila):
                raise ValueError("una celda supera los 2000 caracteres")
        return self


class Bloque(Base):
    id: str = Field(pattern=ID)
    pagina: str | None = Field(default=None, pattern=ID)
    orden: int = Field(ge=0, le=100000)
    tipo: TipoBloque
    bbox: list[int] | None = None
    origen: Literal["ocr", "usuario"]
    estado: EstadoBloque = "reconocido"
    confianza: float | None = Field(default=None, ge=0, le=1)
    texto: str = Field(default="", max_length=20000)
    texto_original: str | None = Field(default=None, max_length=20000)
    latex: str | None = Field(default=None, max_length=2000)
    latex_original: str | None = Field(default=None, max_length=2000)
    latex_valido: bool | None = None
    tabla: Tabla | None = None
    recorte: str | None = Field(default=None, pattern=ID)
    palabras_dudosas: list[str] = Field(default_factory=list, max_length=200)
    conservar_imagen: bool = False
    editado: bool = False

    @field_validator("bbox")
    @classmethod
    def bbox_valido(cls, v):
        if v is not None and (len(v) != 4 or v[0] > v[2] or v[1] > v[3] or min(v) < 0):
            raise ValueError("bbox debe ser [x0, y0, x1, y1] con x0<=x1 y y0<=y1")
        return v

    @model_validator(mode="after")
    def coherente(self):
        if self.tipo == "tabla" and self.tabla is None:
            raise ValueError(f"el bloque {self.id} es una tabla sin datos de tabla")
        if self.tipo == "imagen" and not self.recorte:
            raise ValueError(f"el bloque {self.id} es una imagen sin recorte")
        return self


class Fuente(Base):
    titulo: str = Field(max_length=300)
    url: str = Field(max_length=500)
    proveedor: str = Field(max_length=50)
    consultado: str = Field(max_length=40)
    licencia: str | None = Field(default=None, max_length=100)

    @field_validator("url")
    @classmethod
    def https(cls, v):
        if not re.match(r"^https://[^\s<>\"']+$", v):
            raise ValueError("la fuente debe ser una URL https verificable")
        return v


class Ampliacion(Base):
    id: str = Field(pattern=ID)
    concepto: str = Field(max_length=200)
    texto: str = Field(max_length=5000)
    estado: Literal["propuesta", "aceptada", "rechazada"] = "propuesta"
    fuente: Fuente


class Documento(Base):
    esquema: Literal["apuntia.documento/1"] = ESQUEMA
    titulo: str = Field(min_length=1, max_length=200)
    paginas: list[Pagina] = Field(default_factory=list, max_length=50)
    bloques: list[Bloque] = Field(default_factory=list, max_length=5000)
    ampliaciones: list[Ampliacion] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def referencias(self):
        ids_pag = [p.id for p in self.paginas]
        if len(set(ids_pag)) != len(ids_pag):
            raise ValueError("hay páginas con el mismo id")
        ids_blo = [b.id for b in self.bloques]
        if len(set(ids_blo)) != len(ids_blo):
            raise ValueError("hay bloques con el mismo id")
        if len({a.id for a in self.ampliaciones}) != len(self.ampliaciones):
            raise ValueError("hay ampliaciones con el mismo id")
        for b in self.bloques:
            if b.pagina is not None and b.pagina not in ids_pag:
                raise ValueError(f"el bloque {b.id} apunta a una página inexistente")
            if b.origen == "ocr" and b.pagina is None:
                raise ValueError(f"el bloque OCR {b.id} debe indicar su página")
        return self


def validar(datos: dict) -> Documento:
    """Valida un documento completo; si no es válido no se guarda nada."""
    try:
        return Documento.model_validate(datos)
    except ValidationError as exc:
        detalles = []
        for e in exc.errors()[:5]:
            ruta = ".".join(str(p) for p in e.get("loc", ()))
            detalles.append(f"{ruta}: {e.get('msg', '')}".strip(": "))
        raise ApiError(400, "DOCUMENTO_INVALIDO", "El documento no es válido: " + "; ".join(detalles)) from None


INMUTABLES_OCR = ("pagina", "bbox", "origen", "confianza", "texto_original", "latex_original", "recorte",
                  "palabras_dudosas")


def fusionar(anterior: Documento, nuevo: Documento) -> Documento:
    """Aplica una edición respetando la procedencia (ver docstring del módulo)."""
    previos = {b.id: b for b in anterior.bloques}
    bloques = []
    for b in nuevo.bloques:
        previo = previos.get(b.id)
        if previo is not None and previo.origen == "ocr":
            datos = b.model_dump()
            for campo in INMUTABLES_OCR:
                datos[campo] = getattr(previo, campo)
            datos["origen"] = "ocr"
            cambio = (datos["texto"] != (previo.texto_original or "")
                      or (datos.get("latex") or None) != (previo.latex_original or None)
                      or datos.get("tabla") != (previo.tabla.model_dump() if previo.tabla else None)
                      or datos["tipo"] != previo.tipo)
            datos["editado"] = bool(previo.editado or cambio)
            bloques.append(Bloque.model_validate(datos))
        else:
            if previo is None and b.origen != "usuario":
                raise ApiError(400, "DOCUMENTO_INVALIDO",
                               f"El bloque nuevo {b.id} debe tener origen «usuario»: no se pueden inventar bloques de OCR.")
            bloques.append(b.model_copy(update={"origen": "usuario", "editado": True}))
    # Ampliaciones: solo cambia su estado; texto y fuente vienen de la investigación.
    previas = {a.id: a for a in anterior.ampliaciones}
    ampliaciones = []
    for a in nuevo.ampliaciones:
        original = previas.get(a.id)
        if original is None:
            raise ApiError(400, "DOCUMENTO_INVALIDO",
                           "Las ampliaciones solo se crean desde la investigación con fuentes.")
        ampliaciones.append(original.model_copy(update={"estado": a.estado}))
    ids_nuevas = {a.id for a in ampliaciones}
    ampliaciones += [a for a in anterior.ampliaciones if a.id not in ids_nuevas]  # no se borran en silencio
    paginas_previas = {p.id: p for p in anterior.paginas}
    paginas = [paginas_previas.get(p.id, p) for p in nuevo.paginas if p.id in paginas_previas]
    return Documento(titulo=nuevo.titulo, paginas=sorted(paginas, key=lambda p: p.orden),
                     bloques=bloques, ampliaciones=ampliaciones)


def texto_plano(doc: Documento) -> str:
    """Texto para la búsqueda: título, bloques y tablas (no las ampliaciones)."""
    partes = [doc.titulo]
    for b in doc.bloques:
        partes.append(b.texto or "")
        if b.latex:
            partes.append(b.latex)
        if b.tabla:
            partes += b.tabla.encabezados + [c for fila in b.tabla.filas for c in fila]
    return "\n".join(p for p in partes if p)[:200000]


def documento_vacio(titulo: str, paginas: list[Pagina]) -> Documento:
    return Documento(titulo=titulo, paginas=paginas)
