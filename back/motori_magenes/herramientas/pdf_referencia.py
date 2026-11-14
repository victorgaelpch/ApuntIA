"""PDFs SINTÉTICOS de referencia para BACK-38 (sin fotos reales: los «recortes» se dibujan aquí).

Uso (desde back/motori_magenes):  python -m herramientas.pdf_referencia ../../fullstack/docs/evidencias
"""
import io
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.services.documento import Ampliacion, Bloque, Documento, Fuente, Pagina, Procedencia, Tabla
from app.services.estructura import estructurar
from app.services.pdf import OpcionesPDF, generar_pdf

SALIDA = Path(sys.argv[1])
SALIDA.mkdir(parents=True, exist_ok=True)


def recorte(texto: str, ancho=520, alto=150) -> bytes:
    img = Image.new("RGB", (ancho, alto), (236, 238, 230))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("arial.ttf", 30)
    except OSError:
        f = ImageFont.load_default()
    for k, linea in enumerate(texto.split("\n")):
        d.text((18, 14 + 40 * k), linea, fill=(40, 40, 120), font=f)
    b = io.BytesIO()
    img.save(b, "PNG")
    return b.getvalue()


IMAGENES = {
    "rT": recorte("Triángulo rectángulo isósceles\n√2/2   √2/2\nIsosceles Right"),
    "rL": recorte("Ley de senos\na/sin(A) = b/sin(B)"),
    "rC": recorte("a² = b² + c² − 2bc·cos(A)"),
    "rD": recorte("Definición: seno = opuesto / hipotenusa"),
    "rO": recorte("(foto original sintética)", 900, 600),
}
IA = Procedencia(motor="ia_remota", version="qwen3-vl:8b-instruct", reconocimiento="documento/opencv")


def ejemplo_ia() -> Documento:
    p = Pagina(id="p1", orden=1, tipo_fuente="pizarron", archivo_original="rO", ancho=900, alto=600)
    n = iter(range(100))

    def b(id_, tipo, texto="", **kw):
        return Bloque(id=id_, pagina="p1", orden=next(n), tipo=tipo, origen="ocr", texto=texto, texto_original=texto, **kw)

    bloques = [
        b("t1", "titulo", "Trigonometría básica"),
        b("p1b1", "texto", "seno: cateto opuesto entre hipotenusa.", recorte="rD", procedencia=IA,
          revision="sin_confirmar", revisado=True),
        # Una región que el servidor IA devolvió con dos fórmulas y un título: dividida en tres partes
        b("p1b2_1", "formula", r"\frac{\sqrt{2}}{2}", latex=r"\frac{\sqrt{2}}{2}", latex_original=r"\frac{\sqrt{2}}{2}",
          latex_valido=True, recorte="rT", procedencia=IA, revision="sin_confirmar"),
        b("p1b2_2", "formula", r"\frac{\sqrt{2}}{2}", latex=r"\frac{\sqrt{2}}{2}", latex_original=r"\frac{\sqrt{2}}{2}",
          latex_valido=True, recorte="rT", procedencia=IA, revision="sin_confirmar"),
        b("p1b2_3", "texto", "Isosceles Right", recorte="rT", procedencia=IA, revision="sin_confirmar"),
        b("p1b3", "formula", r"\frac{a}{\sin(A)} = \frac{b}{\sin(B)}", latex=r"\frac{a}{\sin(A)} = \frac{b}{\sin(B)}",
          latex_original=r"\frac{a}{\sin(A)} = \frac{b}{\sin(B)}", latex_valido=True, recorte="rL", procedencia=IA,
          revision="sin_confirmar", revisado=True),
        # LaTeX que no se puede dibujar: se conserva la imagen, nunca otra expresión
        b("p1b4", "formula", r"a^2 = b^2 + c^2 - 2bc(\cos(A)", latex=r"a^2 = b^2 + c^2 - 2bc(\cos(A)",
          latex_original=r"a^2 = b^2 + c^2 - 2bc(\cos(A)", latex_valido=False, recorte="rC", procedencia=IA,
          revision="sin_confirmar", estado="incierto", palabras_dudosas=["LaTeX con llaves desbalanceadas en la línea 1"]),
        b("t2", "titulo", "Valores notables"),
        Bloque(id="u1", pagina="p1", orden=next(n), tipo="tabla", origen="usuario",
               tabla=Tabla(encabezados=["Ángulo", "sen", "cos", "tan"],
                           filas=[["0°", "0", "1", "0"], ["30°", "1/2", "√3/2", "√3/3"], ["45°", "√2/2", "√2/2", "1"],
                                  ["60°", "√3/2", "1/2", "√3"], ["90°", "1", "0", "—"]])),
    ]
    amp = [Ampliacion(id="a1", concepto="Ley de los senos", estado="aceptada",
                      texto="En trigonometría, la ley de los senos relaciona las longitudes de los lados de un "
                            "triángulo con los senos de sus ángulos opuestos (fragmento de ejemplo).",
                      fuente=Fuente(titulo="Teorema de los senos", url="https://es.wikipedia.org/wiki/Teorema_de_los_senos",
                                    proveedor="wikipedia", consultado="2026-11-14", licencia="CC BY-SA 4.0",
                                    autor="Colaboradores de Wikipedia")),
           Ampliacion(id="a2", concepto="Derivada", estado="aceptada",
                      texto="El resultado de derivar una función es una segunda función que indica el crecimiento "
                            "de la original (fragmento de ejemplo).",
                      fuente=Fuente(titulo="Matemáticas/Bachillerato LOGSE/Derivadas",
                                    url="https://es.wikibooks.org/wiki/Matem%C3%A1ticas%2FBachillerato_LOGSE%2FDerivadas",
                                    proveedor="wikilibros", consultado="2026-11-14", licencia="CC BY-SA 4.0",
                                    autor="Colaboradores de Wikilibros"))]
    return Documento(titulo="Ejemplo sintético: propuestas del servidor IA", paginas=[p], bloques=bloques,
                     ampliaciones=amp)


def ejemplo_largo() -> Documento:
    p = Pagina(id="p1", orden=1, tipo_fuente="cuaderno", archivo_original="rO", ancho=900, alto=600)
    bloques, n = [], 0
    for s in range(1, 13):
        bloques.append(Bloque(id=f"t{s}", pagina="p1", orden=n, tipo="titulo", origen="ocr", texto=f"Tema {s}",
                              texto_original=f"Tema {s}"))
        n += 1
        for k in range(6):
            texto = (f"Párrafo {k + 1} del tema {s}: texto de relleno para comprobar saltos de página, índice y "
                     "numeración sin solapes. " * 3)
            bloques.append(Bloque(id=f"b{s}_{k}", pagina="p1", orden=n, tipo="texto", origen="ocr", texto=texto,
                                  texto_original=texto, confianza=0.9))
            n += 1
        latex = rf"\int_0^{{{s}}} x^{{{s}}}\,dx = \frac{{{s}^{{{s + 1}}}}}{{{s + 1}}}"
        bloques.append(Bloque(id=f"f{s}", pagina="p1", orden=n, tipo="formula", origen="ocr", texto=latex,
                              texto_original=latex, latex=latex, latex_original=latex, latex_valido=True))
        n += 1
    ancha = Tabla(encabezados=[f"Columna {c}" for c in range(1, 9)],
                  filas=[[f"valor {f}.{c} largo" for c in range(1, 9)] for f in range(1, 60)])
    bloques.append(Bloque(id="tab", pagina="p1", orden=n, tipo="tabla", origen="usuario", tabla=ancha))
    return Documento(titulo="Ejemplo sintético largo: 12 temas, fórmulas y tabla ancha", paginas=[p], bloques=bloques)


for nombre, doc, opciones in (("back-38-ejemplo-ia", ejemplo_ia(), OpcionesPDF(incluir_originales=False)),
                              ("back-38-ejemplo-largo", ejemplo_largo(), OpcionesPDF())):
    datos, paginas = generar_pdf(doc, estructurar(doc), 1, lambda a: IMAGENES[a], opciones, fecha=date(2026, 11, 14))
    (SALIDA / f"{nombre}.pdf").write_bytes(datos)
    print(nombre, paginas, "páginas,", len(datos), "bytes")
