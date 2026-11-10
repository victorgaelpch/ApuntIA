"""Apunte estructurado sin contenido inventado (BACK-19)."""

from app.services.documento import Ampliacion, Bloque, Documento, Fuente, Pagina, Tabla
from app.services.estructura import estructurar


def doc_ejemplo():
    p = Pagina(id="p1", orden=1, tipo_fuente="cuaderno", archivo_original="a1", ancho=10, alto=10)
    b = lambda i, tipo, texto="", **kw: Bloque(id=f"b{i}", pagina="p1", orden=i, tipo=tipo, origen="ocr",
                                              texto=texto, texto_original=texto, confianza=0.9, **kw)
    bloques = [
        b(1, "titulo", "Derivadas"),
        b(2, "texto", "Derivada: mide la razón de cambio de una función.\nLa derivada de una constante es cero."),
        b(3, "formula", "x^2", latex="x^{2}", latex_valido=True, recorte="r1"),
        b(4, "texto", "Ejemplo: la derivada de x al cuadrado es 2x.\nPendiente: inclinación de la recta tangente."),
        b(5, "titulo", "Integrales"),
        b(6, "texto", "La integral acumula el área bajo la curva de una función."),
        b(7, "imagen", recorte="r2"),
        b(8, "manuscrito", recorte="r3", estado="no_reconocido"),
        Bloque(id="b9", pagina="p1", orden=9, tipo="tabla", origen="usuario",
               tabla=Tabla(encabezados=["f", "f'"], filas=[["x^2", "2x"]])),
    ]
    amp = [Ampliacion(id="x1", concepto="Derivada", texto="Texto de Wikipedia", estado="aceptada",
                      fuente=Fuente(titulo="Derivada", url="https://es.wikipedia.org/wiki/Derivada",
                                    proveedor="wikipedia", consultado="2026-11-10")),
           Ampliacion(id="x2", concepto="Integral", texto="Rechazada", estado="rechazada",
                      fuente=Fuente(titulo="Integral", url="https://es.wikipedia.org/wiki/Integral",
                                    proveedor="wikipedia", consultado="2026-11-10"))]
    return Documento(titulo="Cálculo", paginas=[p], bloques=bloques, ampliaciones=amp)


def test_secciones_por_titulos():
    e = estructurar(doc_ejemplo())
    assert [s.titulo for s in e.secciones] == ["Derivadas", "Integrales"]
    assert e.titulo == "Cálculo" and e.paginas == 1 and e.tipo_fuente == "cuaderno"


def test_todo_sale_del_apunte():
    doc = doc_ejemplo()
    e = estructurar(doc)
    texto_apunte = "\n".join(b.texto for b in doc.bloques)
    assert all(frase in texto_apunte for frase in e.resumen)            # resumen extractivo
    assert all(c in texto_apunte.lower() for c in e.conceptos)
    assert {g["concepto"] for g in e.glosario} == {"Derivada", "Pendiente"}
    assert e.ejemplos == ["Ejemplo: la derivada de x al cuadrado es 2x."]
    assert e.formulas[0]["latex"] == "x^{2}"


def test_tablas_solo_con_datos_del_apunte():
    e = estructurar(doc_ejemplo())
    titulos = [t["titulo"] for t in e.tablas]
    assert "Conceptos definidos en el apunte" in titulos  # 2 definiciones → tabla
    assert any(t["filas"] == [["x^2", "2x"]] for t in e.tablas)
    sin_def = Documento(titulo="t", bloques=[Bloque(id="b", orden=0, tipo="texto", origen="usuario",
                                                    texto="Una frase cualquiera sin definir nada aquí.")])
    assert estructurar(sin_def).tablas == []


def test_complementos_solo_aceptados_y_citados():
    e = estructurar(doc_ejemplo())
    assert len(e.complementos) == 1 and e.complementos[0]["fuente"]["url"].startswith("https://")
    assert all("Wikipedia" not in f for f in e.resumen)   # lo investigado no se mezcla


def test_esquemas_y_pendientes_como_imagen():
    e = estructurar(doc_ejemplo())
    assert e.esquemas == [{"recorte": "r2", "seccion": "Integrales"}]
    assert e.pendientes == 1 and any("imagen" in a for a in e.avisos)


def test_formula_invalida_no_se_presenta_como_latex():
    doc = doc_ejemplo()
    doc.bloques[2].latex_valido = False
    assert estructurar(doc).formulas[0]["latex"] is None


def test_documento_vacio_no_rellena():
    e = estructurar(Documento(titulo="Vacío"))
    assert e.resumen == [] and e.conceptos == [] and e.tablas == [] and e.glosario == []



def test_ruta_estructura_por_version(nuevo_cliente, datos_tmp):
    from app.datos.apuntes import RepositorioApuntes
    from app.services.entrada import PaginaRecibida
    from app.services.validacion import ImagenRecibida
    import numpy as np
    c = nuevo_cliente()
    u = c.registrar()
    repo = RepositorioApuntes(datos_tmp.bd, datos_tmp.almacen)
    apunte, _ = repo.crear(u["id"], "Clase", [PaginaRecibida(1, "cuaderno", ImagenRecibida("a", "png", b"x", np.zeros((5, 5, 3), np.uint8)))])
    doc = repo.documento(u["id"], apunte["id"])
    doc.bloques.append(Bloque(id="b1", orden=0, tipo="titulo", origen="usuario", texto="Tema 1"))
    repo.nueva_version(u["id"], apunte["id"], doc, "edicion")
    r = c.get(f"/api/v2/apuntes/{apunte['id']}/estructura").json()
    assert r["version"] == 2 and r["estructura"]["secciones"][0]["titulo"] == "Tema 1"
    r1 = c.get(f"/api/v2/apuntes/{apunte['id']}/estructura?version=1").json()
    assert r1["estructura"]["secciones"] == []
