"""PDF académico y exportación idempotente (BACK-20). Se lee con pypdf."""

import io
import time

import numpy as np
import pytest
from PIL import Image
from pypdf import PdfReader

from app.datos.apuntes import RepositorioApuntes
from app.services.documento import Ampliacion, Bloque, Documento, Fuente, Pagina, Tabla
from app.services.entrada import PaginaRecibida
from app.services.estructura import estructurar
from app.services.pdf import ErrorPDF, OpcionesPDF, generar_pdf
from app.services.validacion import ImagenRecibida
from tests.test_estructura import doc_ejemplo


def png(ancho=300, alto=120, color=(220, 220, 200)):
    b = io.BytesIO()
    Image.new("RGB", (ancho, alto), color).save(b, "PNG")
    return b.getvalue()


def leer_png(_archivo):
    return png()


def texto_de(datos: bytes) -> tuple[PdfReader, str]:
    lector = PdfReader(io.BytesIO(datos))
    return lector, "\n".join(p.extract_text() for p in lector.pages)


def pdf(doc=None, opciones=OpcionesPDF(), leer=leer_png):
    doc = doc or doc_ejemplo()
    return generar_pdf(doc, estructurar(doc), 2, leer, opciones)


def test_pdf_legible_con_secciones_y_metadatos():
    doc = doc_ejemplo()
    doc.ampliaciones[0].fuente.licencia = "CC BY-SA 4.0"
    datos, paginas = pdf(doc)
    lector, texto = texto_de(datos)
    assert datos.startswith(b"%PDF-") and len(lector.pages) == paginas >= 3
    for parte in ("Cálculo", "Índice", "Transcripción del apunte", "Derivadas", "Integrales",
                  "La integral acumula el área bajo la curva", "Información complementaria", "Fuentes",
                  "https://es.wikipedia.org/wiki/Derivada", "CC BY-SA 4.0", "versión 2"):
        assert parte in texto, parte
    assert "Rechazada" not in texto  # solo ampliaciones aceptadas
    meta = lector.metadata
    assert meta.title == "Cálculo" and meta.author == "ApuntIA" and "versión 2" in meta.subject


def test_unicode_y_html_no_se_interpretan():
    doc = doc_ejemplo()
    doc.bloques[1].texto = "Ñandú, pingüino: áéíóú ¿¡ ∫ λ → ≤ x²\n<b>no negrita</b> <script>alert(1)</script> & <para>"
    _, texto = texto_de(pdf(doc)[0])
    assert "Ñandú, pingüino: áéíóú ¿¡ ∫ λ → ≤ x²" in texto
    assert "<script>alert(1)</script>" in texto and "<b>no negrita</b>" in texto


def test_etiquetas_corregido_e_incierto():
    doc = doc_ejemplo()
    doc.bloques[1].editado = True
    doc.bloques[5].estado = "incierto"
    _, texto = texto_de(pdf(doc)[0])
    assert "corregido por ti" in texto and "reconocimiento incierto" in texto


def test_tabla_larga_repite_encabezado_en_cada_pagina():
    doc = doc_ejemplo()
    doc.bloques.append(Bloque(id="t9", orden=50, tipo="tabla", origen="usuario", tabla=Tabla(
        encabezados=["Número", "Cuadrado"], filas=[[f"fila{i}", str(i * i)] for i in range(150)])))
    lector, texto = texto_de(pdf(doc, OpcionesPDF(estilo="basico"))[0])
    paginas_con_filas = [p.extract_text() for p in lector.pages if "fila" in p.extract_text()]
    assert len(paginas_con_filas) >= 3
    assert all("Número" in p for p in paginas_con_filas)
    assert all(f"fila{i}" in texto for i in range(150))  # no se pierde ninguna fila


def test_basico_extendido_y_complementos():
    _, extendido = texto_de(pdf()[0])
    _, basico = texto_de(pdf(opciones=OpcionesPDF(estilo="basico"))[0])
    _, sin_comp = texto_de(pdf(opciones=OpcionesPDF(incluir_complementos=False))[0])
    assert "Resumen" in extendido and "Glosario del apunte" in extendido
    assert "Resumen" not in basico and "Glosario del apunte" not in basico
    assert "Información complementaria" not in sin_comp and "wikipedia.org" not in sin_comp


def test_anexo_de_originales():
    _, texto = texto_de(pdf(opciones=OpcionesPDF(incluir_originales=True))[0])
    assert "Anexo: fotos originales" in texto and "Página 1 (Cuaderno)" in texto


def test_formula_peligrosa_o_invalida_no_rompe_y_usa_recorte():
    doc = doc_ejemplo()
    doc.bloques[2].latex = r"\input{/etc/passwd}"
    datos, _ = pdf(doc)
    _, texto = texto_de(datos)
    assert "passwd" not in texto and "Fórmula conservada como imagen" in texto


def test_pie_de_lo_no_transcrito_segun_su_tipo():
    """FULL-24: una fórmula impresa sin leer salía rotulada como «fragmento manuscrito»."""
    antes = texto_de(pdf()[0])[1].count("Fragmento manuscrito no transcrito")
    doc = doc_ejemplo()
    doc.bloques += [Bloque(id="nt1", pagina="p1", orden=50, tipo="texto", origen="ocr", estado="no_reconocido", recorte="r1"),
                    Bloque(id="nt2", pagina="p1", orden=51, tipo="manuscrito", origen="ocr", estado="no_reconocido", recorte="r2")]
    _, texto = texto_de(pdf(doc)[0])
    assert texto.count("Fragmento manuscrito no transcrito") == antes + 1  # solo el manuscrito
    assert "Fragmento no transcrito (imagen original)" in texto
    assert "manuscritos no se pudieron leer" not in texto


def test_imagen_danada_o_enorme_se_sustituye_por_aviso(monkeypatch):
    from app.services import pdf as modulo
    _, texto = texto_de(pdf(leer=lambda _a: b"no es una imagen")[0])
    assert "no está disponible" in texto
    monkeypatch.setattr(modulo, "MAX_PIXELES_IMAGEN", 100)
    _, texto = texto_de(pdf()[0])
    assert "no está disponible" in texto


def test_apunte_vacio_falla_sin_pdf_enganoso():
    with pytest.raises(ErrorPDF) as e:
        pdf(Documento(titulo="Vacío"))
    assert e.value.codigo == "APUNTE_VACIO"


def test_reproducible_para_el_mismo_contenido():
    assert pdf()[0] == pdf()[0]


def test_muchas_paginas_sin_solapes():
    doc = doc_ejemplo()
    for i in range(60):
        doc.bloques.append(Bloque(id=f"x{i}", orden=100 + i, tipo="texto", origen="usuario",
                                  texto=f"Párrafo {i}. " + "Texto de relleno del alumno. " * 25))
    lector, texto = texto_de(pdf(doc, OpcionesPDF(estilo="basico"))[0])
    assert len(lector.pages) >= 8 and all(f"Párrafo {i}." in texto for i in range(60))
    pies = [p.extract_text() for p in lector.pages]
    assert all(f"Página {n}" in pies[n - 1] for n in range(1, len(pies) + 1))


# ------------------------------------------------------------------ API

@pytest.fixture
def apunte(nuevo_cliente, datos_tmp):
    c = nuevo_cliente()
    u = c.registrar()
    repo = RepositorioApuntes(datos_tmp.bd, datos_tmp.almacen)
    pag = PaginaRecibida(1, "cuaderno", ImagenRecibida("a.png", "png", png(), np.zeros((8, 8, 3), np.uint8)))
    a, _ = repo.crear(u["id"], "Física: Óptica", [pag])
    doc = repo.documento(u["id"], a["id"])
    doc.bloques.append(Bloque(id="p1b1", pagina="p1", orden=0, tipo="texto", origen="ocr", confianza=0.95,
                              bbox=[0, 0, 5, 5], texto="La luz se refracta al cambiar de medio.",
                              texto_original="La luz se refracta al cambiar de medio."))
    repo.nueva_version(u["id"], a["id"], doc, "analisis", estado="listo")
    return c, a["id"], repo, u, datos_tmp


def esperar(c, tid, limite=30):
    fin = time.time() + limite
    while time.time() < fin:
        t = c.get(f"/api/v2/trabajos/{tid}").json()["trabajo"]
        if t["estado"] not in ("pendiente", "procesando"):
            return t
        time.sleep(0.05)
    raise AssertionError("no terminó")


def test_exportar_descargar_y_reutilizar(apunte):
    c, aid, repo, u, datos = apunte
    r = c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={})
    assert r.status_code == 202, r.text
    exp, trabajo = r.json()["exportacion"], r.json()["trabajo"]
    assert exp["version"] == 2 and trabajo["tipo"] == "exportacion"
    assert esperar(c, trabajo["id"])["estado"] == "completado"
    exp = c.get(f"/api/v2/exportaciones/{exp['id']}").json()["exportacion"]
    assert exp["estado"] == "completado" and exp["descarga"] and exp["paginas"] >= 3
    d = c.get(exp["descarga"])
    assert d.status_code == 200 and d.headers["content-type"] == "application/pdf"
    assert d.headers["content-disposition"] == 'attachment; filename="fisica-optica-v2.pdf"'
    assert d.headers["cache-control"] == "private, no-store"
    import hashlib
    assert hashlib.sha256(d.content).hexdigest() == exp["sha256"] == d.headers["x-apuntia-sha256"]
    assert "La luz se refracta" in texto_de(d.content)[1]
    # Pedirlo otra vez no crea otro trabajo ni otro PDF
    otra = c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={})
    assert otra.status_code == 200 and otra.json()["exportacion"]["id"] == exp["id"] and otra.json()["trabajo"] is None
    assert datos.bd.uno("SELECT COUNT(*) AS n FROM archivos WHERE tipo = 'pdf'")["n"] == 1
    # Otras opciones u otra versión → otra exportación
    assert c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={"estilo": "basico"}).status_code == 202
    v1 = c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={"version": 1})
    assert v1.status_code == 202 and esperar(c, v1.json()["trabajo"]["id"])["error"]["codigo"] == "APUNTE_VACIO"
    lista = c.get(f"/api/v2/apuntes/{aid}/exportaciones").json()["exportaciones"]
    assert {(e["version"], e["estado"]) for e in lista} >= {(2, "completado"), (1, "fallido")}
    # El PDF no se sirve por la ruta de imágenes
    assert c.get(f"/api/v2/apuntes/{aid}/archivos/{datos.bd.uno('SELECT archivo_id FROM exportaciones WHERE id = ?', (exp['id'],))['archivo_id']}").status_code == 404


def test_fallo_no_guarda_pdf(apunte):
    c, aid, *_ , datos = apunte
    r = c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={"version": 1})
    t = esperar(c, r.json()["trabajo"]["id"])
    assert t["estado"] == "fallido" and t["error"]["codigo"] == "APUNTE_VACIO"
    assert datos.bd.uno("SELECT COUNT(*) AS n FROM archivos WHERE tipo = 'pdf'")["n"] == 0
    assert c.get(f"/api/v2/exportaciones/{r.json()['exportacion']['id']}/pdf").json()["error"]["codigo"] == "PDF_NO_LISTO"
    # Reintentarlo tras arreglar: vuelve a encolar
    assert c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={"version": 1}).status_code == 202


def test_version_inexistente_y_apunte_en_proceso(apunte):
    c, aid, repo, u, datos = apunte
    assert c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={"version": 99}).status_code == 404
    repo.cambiar_estado(aid, "procesando")
    r = c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={})
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "APUNTE_EN_PROCESO"


def test_recorte_ajeno_no_se_filtra_al_pdf(apunte, nuevo_cliente):
    c, aid, repo, u, datos = apunte
    otro = nuevo_cliente()
    ou = otro.registrar("otro@example.com")
    secreto = datos.almacen.guardar(ou["id"], png(color=(255, 0, 0)), "recorte", "image/png")
    doc = c.get(f"/api/v2/apuntes/{aid}").json()["apunte"]
    d = doc["documento"]
    d["bloques"].append({"id": "u1", "orden": 5, "tipo": "imagen", "origen": "usuario", "recorte": secreto})
    assert c.put(f"/api/v2/apuntes/{aid}/documento", json=d, headers={"If-Match": str(doc["version"])}).status_code == 200
    r = c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={})
    assert esperar(c, r.json()["trabajo"]["id"])["estado"] == "completado"
    pdf_bytes = c.get(r.json()["exportacion"]["descarga"] or
                      c.get(f"/api/v2/exportaciones/{r.json()['exportacion']['id']}").json()["exportacion"]["descarga"]).content
    lector, texto = texto_de(pdf_bytes)
    assert "no está disponible" in texto
    assert all(not p.images for p in lector.pages)  # la imagen roja del otro usuario no está


def test_borrar_apunte_borra_sus_pdf(apunte):
    c, aid, *_, datos = apunte
    r = c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={})
    esperar(c, r.json()["trabajo"]["id"])
    eid = r.json()["exportacion"]["id"]
    assert c.delete(f"/api/v2/apuntes/{aid}").status_code == 204
    assert c.get(f"/api/v2/exportaciones/{eid}/pdf").status_code == 404
    assert datos.bd.uno("SELECT COUNT(*) AS n FROM archivos WHERE tipo = 'pdf'")["n"] == 0
    assert not any(p.is_file() for p in (datos.data_dir / "tmp").rglob("*")) if (datos.data_dir / "tmp").exists() else True


# ------------------------------------------------------------------ BACK-38: propuestas del servidor IA
def doc_con_ia(revisado=False):
    from app.services.documento import Procedencia
    doc = doc_ejemplo()
    ia = Procedencia(motor="ia_remota", version="qwen3-vl:8b-instruct", reconocimiento="documento/opencv")
    doc.bloques[5] = doc.bloques[5].model_copy(update={"procedencia": ia, "recorte": "rIA", "revisado": revisado,
                                                       "revision": "sin_confirmar"})
    return doc


def test_propuesta_ia_sin_revisar_va_marcada_y_con_su_recorte():
    leidos = []
    datos, _ = pdf(doc_con_ia(), leer=lambda a: leidos.append(a) or png())
    _, texto = texto_de(datos)
    assert "propuesta del servidor IA: sin revisar" in texto
    assert "Recorte de la foto: compáralo con la propuesta del servidor IA" in texto
    assert "1 bloque(s) son propuestas del servidor IA sin revisar" in texto     # aviso en la portada
    assert "rIA" in leidos
    assert "La integral acumula el área bajo la curva" in texto                 # el texto propuesto sigue ahí


def test_propuesta_ia_revisada_no_lleva_recorte_ni_aviso():
    leidos = []
    datos, _ = pdf(doc_con_ia(revisado=True), leer=lambda a: leidos.append(a) or png())
    _, texto = texto_de(datos)
    assert "propuesta del servidor IA: revisada" in texto
    assert "Recorte de la foto" not in texto and "sin revisar" not in texto
    assert "rIA" not in leidos


def test_sin_recortes_ia_si_se_pide_y_la_clave_por_defecto_no_cambia():
    assert OpcionesPDF().clave == "extendido|o0|c1"           # exportaciones ya hechas siguen valiendo
    opciones = OpcionesPDF(incluir_recortes_ia=False)
    assert opciones.clave == "extendido|o0|c1|r0"
    leidos = []
    _, texto = texto_de(pdf(doc_con_ia(), opciones, leer=lambda a: leidos.append(a) or png())[0])
    assert "propuesta del servidor IA: sin revisar" in texto     # la etiqueta nunca se quita
    assert "rIA" not in leidos


def test_documento_sin_ia_no_cambia():
    _, texto = texto_de(pdf()[0])
    assert "servidor IA: " not in texto and "Recorte de la foto" not in texto


def test_region_dividida_muestra_su_recorte_una_sola_vez():
    from app.services.documento import Procedencia
    doc = doc_ejemplo()
    ia = Procedencia(motor="ia_remota", version="m", reconocimiento="documento/opencv")
    parte = lambda i, tipo, texto, latex=None: Bloque(
        id=f"p1b7_{i}", pagina="p1", orden=20 + i, tipo=tipo, origen="ocr", texto=texto, texto_original=texto,
        latex=latex, latex_original=latex, latex_valido=True if latex else None, recorte="rG", procedencia=ia,
        revision="sin_confirmar")
    doc.bloques += [parte(1, "formula", "x^2", "x^{2}"), parte(2, "formula", r"\frac{1}{2", r"\frac{1}{2"),
                    parte(3, "texto", "Isosceles Right")]
    leidos = []
    _, texto = texto_de(pdf(doc, leer=lambda a: leidos.append(a) or png())[0])
    assert leidos.count("rG") == 1                       # la fórmula no dibujable usa el recorte; no se repite
    assert texto.count("Recorte de la foto: compáralo") == 0
    assert "Fórmula conservada como imagen" in texto and "Isosceles Right" in texto


def test_lo_derivado_no_usa_propuestas_de_ia_sin_revisar():
    doc = doc_con_ia()                 # bloque 6 (texto de Integrales) = propuesta IA sin revisar
    e = estructurar(doc)
    assert not any("integral acumula" in f for f in e.resumen)
    assert any(b["id"] == "b6" for s in e.secciones for b in s.bloques)    # pero sí está en la transcripción
    e2 = estructurar(doc_con_ia(revisado=True))
    assert any("integral acumula" in f for f in e2.resumen)
