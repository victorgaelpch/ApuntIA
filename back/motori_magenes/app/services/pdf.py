"""PDF académico del apunte con ReportLab (BACK-20).

Por qué ReportLab (BSD) y no WeasyPrint u otro motor:
  - no interpreta HTML ni CSS del usuario ni descarga recursos remotos: todo el
    contenido entra como texto escapado, así que no hay inyección de HTML ni
    peticiones a URLs internas;
  - es Python puro (sin Pango, Cairo ni GTK), funciona igual en Windows, Linux y
    Docker;
  - las fórmulas se dibujan con mathtext de matplotlib (BACK-15), que solo
    acepta el subconjunto de LaTeX permitido y no ejecuta TeX ni macros;
  - el texto queda seleccionable y con Unicode completo usando DejaVu Sans
    (licencia libre, incluida con matplotlib).

Estructura del PDF:
  portada → índice → «Transcripción del apunte» (secciones con su contenido,
  marcando lo corregido y lo incierto) → resumen, conceptos, glosario y tablas
  (estilo extendido) → «Información complementaria» (solo ampliaciones
  aceptadas, citadas) → «Fuentes» → anexo con las fotos originales (opcional).

Si el apunte no tiene contenido no se genera un PDF vacío: se lanza ErrorPDF.
"""

import io
import os
from dataclasses import dataclass
from datetime import date
from xml.sax.saxutils import escape

import matplotlib
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, LayoutError, ListFlowable, ListItem,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

from app.services.documento import Documento
from app.services.estructura import ApunteEstructurado
from app.services.formulas import renderizar_png

FUENTE, NEGRITA, CURSIVA, MONO = "DejaVuSans", "DejaVuSans-Bold", "DejaVuSans-Oblique", "DejaVuSansMono"
MAX_PIXELES_IMAGEN = 12_000_000
ESTILOS_PDF = ("basico", "extendido")


class ErrorPDF(Exception):
    def __init__(self, codigo: str, mensaje: str):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


@dataclass(frozen=True)
class OpcionesPDF:
    estilo: str = "extendido"            # basico: portada + transcripción + complementos; extendido: + resumen…
    incluir_originales: bool = False     # anexo con las fotos originales
    incluir_complementos: bool = True    # ampliaciones aceptadas (siempre separadas y citadas)
    incluir_recortes_ia: bool = True     # recorte de la foto junto a cada propuesta del servidor IA sin revisar

    @property
    def clave(self) -> str:
        base = f"{self.estilo}|o{int(self.incluir_originales)}|c{int(self.incluir_complementos)}"
        return base if self.incluir_recortes_ia else base + "|r0"   # la clave por defecto no cambia


_fuentes_registradas = False


def registrar_fuentes() -> None:
    global _fuentes_registradas
    if _fuentes_registradas:
        return
    carpeta = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    for nombre, archivo in ((FUENTE, "DejaVuSans.ttf"), (NEGRITA, "DejaVuSans-Bold.ttf"),
                            (CURSIVA, "DejaVuSans-Oblique.ttf"), (MONO, "DejaVuSansMono.ttf")):
        pdfmetrics.registerFont(TTFont(nombre, os.path.join(carpeta, archivo)))
    pdfmetrics.registerFontFamily(FUENTE, normal=FUENTE, bold=NEGRITA, italic=CURSIVA, boldItalic=NEGRITA)
    _fuentes_registradas = True


def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    e = {
        "cuerpo": ParagraphStyle("cuerpo", base["BodyText"], fontName=FUENTE, fontSize=10.5, leading=15,
                                 spaceAfter=6),
        "portada": ParagraphStyle("portada", base["Title"], fontName=NEGRITA, fontSize=26, leading=32,
                                  alignment=TA_CENTER, spaceAfter=18),
        "subportada": ParagraphStyle("subportada", fontName=FUENTE, fontSize=12, leading=18, alignment=TA_CENTER,
                                     textColor=colors.HexColor("#444444")),
        "h1": ParagraphStyle("h1", fontName=NEGRITA, fontSize=17, leading=22, spaceBefore=14, spaceAfter=8,
                             keepWithNext=1, textColor=colors.HexColor("#1d3557")),
        "h2": ParagraphStyle("h2", fontName=NEGRITA, fontSize=13, leading=17, spaceBefore=10, spaceAfter=5,
                             keepWithNext=1),
        "etiqueta": ParagraphStyle("etiqueta", fontName=CURSIVA, fontSize=8, leading=10,
                                   textColor=colors.HexColor("#8a5a00"), spaceAfter=1, keepWithNext=1),
        "nota": ParagraphStyle("nota", fontName=CURSIVA, fontSize=9, leading=12, textColor=colors.HexColor("#555555"),
                               spaceAfter=6),
        "celda": ParagraphStyle("celda", fontName=FUENTE, fontSize=9, leading=11),
        "celda_cab": ParagraphStyle("celda_cab", fontName=NEGRITA, fontSize=9, leading=11),
        "mono": ParagraphStyle("mono", fontName=MONO, fontSize=9.5, leading=13, spaceAfter=6),
        "cita": ParagraphStyle("cita", fontName=FUENTE, fontSize=10, leading=14, leftIndent=12,
                               borderPadding=(4, 6, 4, 6), backColor=colors.HexColor("#f1f5fb"), spaceAfter=4),
        "toc1": ParagraphStyle("toc1", fontName=NEGRITA, fontSize=11, leading=16),
        "toc2": ParagraphStyle("toc2", fontName=FUENTE, fontSize=10, leading=14, leftIndent=14),
    }
    return e


def texto_seguro(texto: str) -> str:
    """Texto del usuario → marcado de ReportLab sin etiquetas: se escapa todo."""
    limpio = "".join(c for c in (texto or "") if c in "\n\t" or ord(c) >= 32)
    return escape(limpio).replace("\n", "<br/>")


class _Documento(BaseDocTemplate):
    """Plantilla con encabezado, pie numerado e índice automático."""

    def __init__(self, destino, titulo: str, version: int, **kw):
        super().__init__(destino, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2.4 * cm,
                         bottomMargin=2.2 * cm, title=titulo, author="ApuntIA", creator="ApuntIA",
                         subject=f"Apunte · versión {version}", invariant=1, **kw)
        self.titulo_corto = titulo if len(titulo) <= 70 else titulo[:67] + "…"
        self.version = version
        marco = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates([PageTemplate(id="portada", frames=[marco], onPage=self._pie),
                               PageTemplate(id="contenido", frames=[marco], onPage=self._cabecera_y_pie)])

    def _pie(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(FUENTE, 8)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawCentredString(A4[0] / 2, 1.2 * cm, f"Página {doc.page}")
        canvas.restoreState()

    def _cabecera_y_pie(self, canvas, doc):
        self._pie(canvas, doc)
        canvas.saveState()
        canvas.setFont(FUENTE, 8)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(self.leftMargin, A4[1] - 1.4 * cm, self.titulo_corto)
        canvas.drawRightString(A4[0] - self.rightMargin, A4[1] - 1.4 * cm, f"ApuntIA · versión {self.version}")
        canvas.setStrokeColor(colors.HexColor("#dddddd"))
        canvas.line(self.leftMargin, A4[1] - 1.55 * cm, A4[0] - self.rightMargin, A4[1] - 1.55 * cm)
        canvas.restoreState()

    def afterFlowable(self, flowable):
        nivel = getattr(flowable, "_nivel_indice", None)
        if nivel is not None:
            texto = flowable.getPlainText()
            clave = f"s{id(flowable)}"
            self.canv.bookmarkPage(clave)
            self.canv.addOutlineEntry(texto, clave, level=nivel, closed=nivel > 0)
            self.notify("TOCEntry", (nivel, texto, self.page, clave))


def _titulo(texto: str, estilo: ParagraphStyle, nivel: int) -> Paragraph:
    p = Paragraph(texto_seguro(texto), estilo)
    p._nivel_indice = nivel
    return p


def _imagen(datos: bytes, ancho_max: float, alto_max: float, dpi: float = 150) -> Image | None:
    """Imagen escalada para caber; None si no se puede leer (nunca rompe el PDF).

    Se reduce a la resolución con la que se va a imprimir (`dpi`) antes de
    incrustarla: el PDF pesa menos y la memoria no crece con fotos de 12 MP.
    """
    try:
        with PILImage.open(io.BytesIO(datos)) as im:
            im.verify()
        with PILImage.open(io.BytesIO(datos)) as im:
            ancho, alto = im.size
            if ancho * alto > MAX_PIXELES_IMAGEN:
                return None
            # Tamaño natural a `dpi` (sin ampliar recortes pequeños), limitado al hueco disponible.
            escala = min(ancho_max / ancho, alto_max / alto, 72 / dpi)
            puntos = (ancho * escala, alto * escala)
            objetivo = (max(1, round(puntos[0] * dpi / 72)), max(1, round(puntos[1] * dpi / 72)))
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            if objetivo[0] < ancho:
                im = im.resize(objetivo, PILImage.LANCZOS)
            salida = io.BytesIO()
            im.save(salida, "PNG" if im.mode == "L" or im.format == "PNG" else "JPEG", quality=85)
    except Exception:  # noqa: BLE001 — imagen dañada: se omite con aviso
        return None
    img = Image(io.BytesIO(salida.getvalue()), width=puntos[0], height=puntos[1])
    img.hAlign = "LEFT"
    return img


def _tabla(encabezados: list[str], filas: list[list[str]], ancho: float, estilos) -> Table:
    datos = [[Paragraph(texto_seguro(c), estilos["celda_cab"]) for c in encabezados]]
    datos += [[Paragraph(texto_seguro(c), estilos["celda"]) for c in fila] for fila in filas]
    columnas = max(1, len(encabezados))
    t = Table(datos, colWidths=[ancho / columnas] * columnas, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4d6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbfd")]),
    ]))
    return t


def generar_pdf(doc: Documento, estructura: ApunteEstructurado, version: int, leer_archivo,
                opciones: OpcionesPDF = OpcionesPDF(), fecha: date | None = None) -> tuple[bytes, int]:
    """Devuelve (bytes del PDF, número de páginas). `leer_archivo(id) -> bytes` lee imágenes privadas."""
    registrar_fuentes()
    if not any(b.texto.strip() or b.recorte or b.tabla or b.latex for b in doc.bloques):
        raise ErrorPDF("APUNTE_VACIO", "El apunte no tiene contenido para exportar. Revisa el análisis o edítalo.")
    e = _estilos()
    salida = io.BytesIO()
    plantilla = _Documento(salida, doc.titulo, version)
    ancho, alto = plantilla.width, plantilla.height
    fecha = fecha or date.today()
    fuentes_vistas: dict[str, dict] = {}

    def leer(archivo_id: str | None) -> bytes | None:
        if not archivo_id:
            return None
        try:
            return leer_archivo(archivo_id)
        except Exception:  # noqa: BLE001
            return None

    def imagen_o_aviso(archivo_id: str | None, pie: str, alto_max: float = 0.45) -> list:
        datos = leer(archivo_id)
        img = _imagen(datos, ancho, alto * alto_max) if datos else None
        if img is None:
            return [Paragraph("[La imagen original de este fragmento no está disponible.]", e["nota"])]
        return [KeepTogether([img, Paragraph(texto_seguro(pie), e["nota"])])]

    h = []
    # ---------------------------------------------------------------- portada
    tipos = {"pizarron": "Pizarrón", "cuaderno": "Cuaderno"}
    h += [Spacer(1, 5 * cm), Paragraph(texto_seguro(doc.titulo), e["portada"]),
          Paragraph(f"Apunte digitalizado · {fecha.strftime('%d/%m/%Y')}", e["subportada"]),
          Paragraph(f"Origen: {tipos.get(estructura.tipo_fuente, 'fotos')} · {estructura.paginas} página(s) · "
                    f"versión {version}", e["subportada"]), Spacer(1, 1.2 * cm)]
    for aviso in estructura.avisos:
        h.append(Paragraph(texto_seguro("⚠ " + aviso), e["subportada"]))
    h.append(Spacer(1, 1.5 * cm))
    h.append(Paragraph("La transcripción proviene de tus fotos. Las partes corregidas por ti, las inciertas y las "
                       "propuestas por el servidor IA van marcadas; la información de fuentes externas aparece "
                       "aparte y citada.", e["nota"]))
    from reportlab.platypus.doctemplate import NextPageTemplate
    h += [NextPageTemplate("contenido"), PageBreak()]

    # ---------------------------------------------------------------- índice
    indice = TableOfContents()
    indice.levelStyles = [e["toc1"], e["toc2"]]
    h += [Paragraph("Índice", e["h1"]), indice, PageBreak()]

    # ---------------------------------------------------------------- transcripción
    h.append(_titulo("Transcripción del apunte", e["h1"], 0))
    for seccion in estructura.secciones:
        if seccion.titulo != "Contenido" or len(estructura.secciones) > 1:
            h.append(_titulo(seccion.titulo, e["h2"], 1))
        # Una región que el servidor IA dividió en varias partes (BACK-38) comparte recorte: se
        # muestra una sola vez, al final del grupo, para que el PDF no repita la misma foto.
        mostrados: set[str] = set()
        pendiente: str | None = None
        bloques = seccion.bloques
        for i, b in enumerate(bloques):
            if i == 0 or bloques[i - 1]["recorte"] != b["recorte"]:
                mostrados.clear()            # «ya mostrado» vale solo dentro del grupo de la misma región
            etiquetas = []
            if b.get("ia"):
                etiquetas.append("propuesta del servidor IA: " + ("revisada" if b.get("revisado") else "sin revisar"))
            if b["editado"]:
                etiquetas.append("corregido por ti")
            if b["estado"] == "incierto":
                etiquetas.append("reconocimiento incierto: revisar")
            if etiquetas:
                h.append(Paragraph(" · ".join(etiquetas), e["etiqueta"]))
            # Una propuesta de IA sin revisar nunca va sola: se acompaña del recorte de la foto para compararla.
            if (b.get("ia") and not b.get("revisado") and not b["editado"] and opciones.incluir_recortes_ia
                    and b["recorte"] and (b["texto"].strip() or b["latex"])):
                pendiente = b["recorte"]
            if b["tipo"] == "formula":
                png = None
                if b["latex"]:
                    try:
                        png = renderizar_png(b["latex"], dpi=220)
                    except Exception:  # noqa: BLE001
                        png = None
                img = _imagen(png, ancho, alto * 0.3, dpi=220) if png else None
                if img is not None:
                    img.hAlign = "CENTER"
                    h.append(img)
                    h.append(Spacer(1, 4))
                elif b["recorte"] and b["recorte"] not in mostrados:
                    h += imagen_o_aviso(b["recorte"], "Fórmula conservada como imagen (no se pudo verificar)", 0.25)
                    mostrados.add(b["recorte"])
                elif b["texto"]:
                    # Sin dibujo y con el recorte ya puesto: LaTeX literal y aviso, nunca otra expresión.
                    h.append(Paragraph(texto_seguro(b["texto"]), e["mono"]))
                    h.append(Paragraph("Fórmula que no se pudo dibujar: compárala con el recorte de esta región.",
                                       e["nota"]))
            elif b["tipo"] == "tabla" and b["tabla"]:
                h += [_tabla(b["tabla"]["encabezados"], b["tabla"]["filas"], ancho, e), Spacer(1, 8)]
            elif b["texto"].strip():
                h.append(Paragraph(texto_seguro(b["texto"]), e["cuerpo"]))
            elif b["recorte"] and b["recorte"] not in mostrados:
                pie = {"imagen": "Esquema o dibujo del apunte",
                       "manuscrito": "Fragmento manuscrito no transcrito (imagen original)"}.get(
                    b["tipo"], "Fragmento no transcrito (imagen original)")
                h += imagen_o_aviso(b["recorte"], pie)
                mostrados.add(b["recorte"])
            sigue_region = i + 1 < len(bloques) and b["recorte"] and bloques[i + 1]["recorte"] == b["recorte"]
            if pendiente and not sigue_region:
                if pendiente not in mostrados:
                    h += imagen_o_aviso(pendiente, "Recorte de la foto: compáralo con la propuesta del servidor IA",
                                        0.25)
                    mostrados.add(pendiente)
                pendiente = None

    # ---------------------------------------------------------------- extendido (todo sale del apunte)
    if opciones.estilo == "extendido":
        if estructura.resumen:
            h.append(_titulo("Resumen", e["h1"], 0))
            h.append(Paragraph("Frases tomadas de tu apunte.", e["nota"]))
            h.append(ListFlowable([ListItem(Paragraph(texto_seguro(f), e["cuerpo"])) for f in estructura.resumen],
                                  bulletType="bullet", bulletFontName=FUENTE))
        if estructura.conceptos:
            h.append(_titulo("Conceptos clave", e["h1"], 0))
            h.append(Paragraph(texto_seguro(", ".join(estructura.conceptos)), e["cuerpo"]))
        if estructura.glosario:
            h.append(_titulo("Glosario del apunte", e["h1"], 0))
            for g in estructura.glosario:
                h.append(Paragraph(f"<b>{texto_seguro(g['concepto'])}</b>: {texto_seguro(g['definicion'])}",
                                   e["cuerpo"]))
        derivadas = [t for t in estructura.tablas if t["titulo"] == "Conceptos definidos en el apunte"]
        if derivadas:
            h.append(_titulo("Tabla comparativa", e["h1"], 0))
            h.append(_tabla(derivadas[0]["encabezados"], derivadas[0]["filas"], ancho, e))
        if estructura.ejemplos:
            h.append(_titulo("Ejemplos", e["h1"], 0))
            h.append(ListFlowable([ListItem(Paragraph(texto_seguro(x), e["cuerpo"])) for x in estructura.ejemplos],
                                  bulletType="bullet", bulletFontName=FUENTE))

    # ---------------------------------------------------------------- complementos citados
    if opciones.incluir_complementos and estructura.complementos:
        h.append(_titulo("Información complementaria", e["h1"], 0))
        h.append(Paragraph("No forma parte de tu apunte: proviene de las fuentes citadas y la aceptaste al revisarla.",
                           e["nota"]))
        for c in estructura.complementos:
            f = c["fuente"]
            n = fuentes_vistas.setdefault(f["url"], {**f, "n": len(fuentes_vistas) + 1})["n"]
            bloque = [Paragraph(f"<b>{texto_seguro(c['concepto'])}</b> [{n}]", e["h2"]),
                      Paragraph(texto_seguro(c["texto"]), e["cita"])]
            if c.get("discrepancia"):
                bloque.append(Paragraph(texto_seguro("Atención: " + c["discrepancia"]), e["etiqueta"]))
            h += bloque
        h.append(_titulo("Fuentes", e["h1"], 0))
        for f in sorted(fuentes_vistas.values(), key=lambda x: x["n"]):
            autor = f"{texto_seguro(f['autor'])}. " if f.get("autor") else ""
            licencia = f" Licencia {texto_seguro(f['licencia'])}." if f.get("licencia") else ""
            url = texto_seguro(f["url"])
            h.append(Paragraph(f"[{f['n']}] {autor}«{texto_seguro(f['titulo'])}». {texto_seguro(f['proveedor'])}. "
                               f'<link href="{url}" color="blue">{url}</link> (consultado el '
                               f"{texto_seguro(f['consultado'])}).{licencia}", e["cuerpo"]))

    # ---------------------------------------------------------------- anexo
    if opciones.incluir_originales and doc.paginas:
        h += [PageBreak(), _titulo("Anexo: fotos originales", e["h1"], 0)]
        for p in sorted(doc.paginas, key=lambda x: x.orden):
            h += imagen_o_aviso(p.archivo_original, f"Página {p.orden} ({tipos.get(p.tipo_fuente, '')})", 0.8)

    try:
        plantilla.multiBuild(h, maxPasses=6)
    except LayoutError as exc:
        raise ErrorPDF("PDF_MAQUETACION", "Un elemento del apunte no cabe en la página; revisa tablas o "
                                          "imágenes muy grandes.") from exc
    datos = salida.getvalue()
    if not datos.startswith(b"%PDF-"):
        raise ErrorPDF("PDF_FALLO", "No se pudo generar el PDF.")
    return datos, plantilla.page
