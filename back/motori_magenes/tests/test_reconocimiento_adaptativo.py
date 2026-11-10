"""Reconocimiento adaptativo y recuperación asistida (BACK-28).

Unitarias con un motor de OCR simulado (sin Tesseract) para las reglas de decisión, y de
integración y regresión con Tesseract y el corpus de casos difíciles.
"""

import io
import time

import cv2
import numpy as np
import pytest
from pypdf import PdfReader

from app.core.config import settings
from app.services import adaptativo
from app.services.adaptativo import Lector, Lectura, elegir, intentar_formula, leer_adaptativo, revisar_bloque
from app.services.calidad import diagnosticar
from app.services.documento import Documento, fusionar, validar
from app.services.formulas import es_formula
from app.services.ocr import BloqueOCR, ErrorOCR, MotorNinguno, MotorOCR, MotorTesseract, Palabra
from app.services.preprocesado_ocr import enderezar, estimar_inclinacion
from app.services.reconocimiento import reconocer_pagina
from herramientas.corpus import diagrama, hoja_cuaderno, impreso_cuaderno
from herramientas.corpus_dificil import TEXTOS, foto_borrosa, foto_girada, letra_pequena, tinta_tenue

TESSERACT = MotorTesseract().disponible()
requiere_tesseract = pytest.mark.skipif(not TESSERACT, reason="Tesseract no está instalado")
BASE = {"motor": "simulado", "version": "0", "reconocimiento": adaptativo.VERSION, "psm": 3}


class MotorGuion(MotorOCR):
    """Motor simulado: devuelve, por orden de llamada, las lecturas indicadas (texto, confianza)."""
    nombre = "simulado"

    def __init__(self, lecturas):
        self.lecturas = list(lecturas)
        self.llamadas = 0

    def palabras(self, imagen, idiomas, psm):
        self.llamadas += 1
        if not self.lecturas:
            return []
        texto, conf = self.lecturas.pop(0)
        return [Palabra(p, conf, (10 * i, 0, 10 * i + 8, 10), 1, 1, 1) for i, p in enumerate(texto.split())]


def bloque(texto, conf, minima=None):
    return BloqueOCR(texto, conf, [20, 20, 300, 60], [texto], 20.0, minima=minima if minima is not None else conf)


GRIS = np.full((200, 400), 240, np.uint8)
cv2.putText(GRIS, "texto", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 20, 2)


def lector(motor):
    return Lector(GRIS, "spa", motor)


def lectura(texto, conf, variante):
    return Lectura(texto, conf, conf, [], variante, 7)


# ------------------------------------------------------------------ elegir: cuál lectura gana

def test_la_confianza_inflada_de_una_variante_no_sustituye_a_la_pagina():
    # Medido en BACK-28: «Lasplantasnecesitanluzsolar.» (0,90) frente a la página (0,69)
    pagina = lectura("Las plantas necesitan luzsolar.", 0.69, "pagina")
    elegida, confirmada = elegir(pagina, [pagina, lectura("Lasplantasnecesitanluzsolar.", 0.90, "ampliada_otsu"),
                                          lectura("Lasplantasnecesitanluzsolar.", 0.88, "ampliada")])
    assert elegida is pagina and not confirmada


def test_regla_de_back14_el_recorte_binarizado_gana_si_es_claramente_mejor():
    pagina = lectura("Repasar inte grates", 0.6, "pagina")
    otsu = lectura("Repasar integrales", 0.9, "ampliada_otsu")
    elegida, confirmada = elegir(pagina, [pagina, otsu, lectura("Repasar integrales", 0.88, "ampliada")])
    # Sustituye a la página, pero queda para revisar: las variantes de un recorte no se confirman entre sí
    assert elegida is otsu and not confirmada


def test_pagina_ilegible_se_rescata_con_la_variante_mas_votada_sin_confirmar():
    pagina = lectura("x?", 0.2, "pagina")
    elegida, confirmada = elegir(pagina, [pagina, lectura("Entregar la practica", 0.7, "clahe"),
                                          lectura("Entregar la practica", 0.6, "sin_sombra"),
                                          lectura("Entregar /A practica", 0.8, "ampliada")])
    assert elegida.texto == "Entregar la practica" and not confirmada


# ------------------------------------------------------------------ consenso y alternativas

def test_lecturas_distintas_piden_revision_y_ofrecen_la_otra_como_alternativa():
    b = bloque("Repasar eltema tres", 0.93)
    nuevo = revisar_bloque(lector(MotorGuion([("Repasar el tema tres", 0.9)])), b, BASE)
    assert nuevo.texto == "Repasar eltema tres"            # el texto de la página no se sustituye
    assert nuevo.estado == "incierto" and nuevo.revision == "lecturas_distintas"
    assert [a["texto"] for a in nuevo.alternativas] == ["Repasar el tema tres"]
    assert nuevo.procedencia["lecturas"] == 2 and nuevo.procedencia["motor"] == "simulado"


def test_lecturas_iguales_confirman_el_bloque():
    nuevo = revisar_bloque(lector(MotorGuion([("Entregar la practica", 0.92)])), bloque("Entregar la practica", 0.95), BASE)
    assert nuevo.estado == "reconocido" and nuevo.revision is None and nuevo.alternativas == []


def test_un_bloque_dudoso_no_pasa_a_reconocido_sin_confirmacion():
    motor = MotorGuion([("Estudiar para el lunes", 0.97)] * 4)
    nuevo = revisar_bloque(lector(motor), bloque("Estudiar para ej (unes", 0.7, 0.6), BASE)
    # La variante gana (regla de BACK-14) pero no se da por segura; la lectura de la página queda como alternativa
    assert nuevo.texto == "Estudiar para el lunes" and nuevo.estado == "incierto" and nuevo.revision == "sin_confirmar"
    assert "Estudiar para ej (unes" in [a["texto"] for a in nuevo.alternativas]


def test_como_mucho_tres_alternativas_y_sin_repetidas():
    motor = MotorGuion([("uno", 0.6), ("dos", 0.6), ("tres", 0.6), ("cuatro", 0.6)])
    nuevo = revisar_bloque(lector(motor), bloque("cero", 0.55), BASE)
    assert len(nuevo.alternativas) <= 3 and len({a["texto"] for a in nuevo.alternativas}) == len(nuevo.alternativas)


def test_lo_ilegible_no_se_inventa():
    motor = MotorGuion([])  # ninguna variante lee nada
    salida = leer_adaptativo(GRIS, [bloque("a?7", 0.2)], "spa", motor, BASE)
    ilegible = [b for b in salida if b.bbox == [20, 20, 300, 60]][0]
    assert ilegible.texto == "" and ilegible.recortar and ilegible.alternativas == []


def test_presupuesto_de_tiempo_sin_relecturas(monkeypatch):
    monkeypatch.setattr(settings, "reconocimiento_max_segundos", 0)
    motor = MotorGuion([("otra", 0.99)] * 10)
    salida = leer_adaptativo(GRIS, [bloque("algo dudoso", 0.6), bloque("bien", 0.95)], "spa", motor, BASE)
    assert motor.llamadas == 0 and len([b for b in salida if b.texto]) == 2


def test_limite_de_variantes_por_bloque(monkeypatch):
    monkeypatch.setattr(settings, "reconocimiento_max_variantes", 2)
    motor = MotorGuion([("x", 0.3)] * 10)
    revisar_bloque(lector(motor), bloque("y", 0.3), BASE)
    assert motor.llamadas == 2


# ------------------------------------------------------------------ fórmulas

def test_formula_con_dos_lecturas_iguales_se_reconoce():
    motor = MotorGuion([("v=d/t", 0.95), ("v=d/t", 0.93)])
    f = intentar_formula(lector(motor), bloque("v=d/t", 0.6), BASE, "v=d/t")
    assert f.tipo == "formula" and f.latex == r"v = \frac{d}{t}" and f.estado == "reconocido"


def test_formula_con_una_sola_lectura_queda_para_revisar():
    motor = MotorGuion([("a+b=c", 0.95), ("a+b=e", 0.6)])
    f = intentar_formula(lector(motor), bloque("a+b=c", 0.3), BASE, "a+b=c")
    assert f.estado == "incierto" and f.revision == "formula_sin_confirmar" and f.recortar
    assert [a["latex"] for a in f.alternativas] == ["a + b = e"]


def test_una_formula_muy_dudosa_no_se_acepta_aunque_sea_latex_valido():
    motor = MotorGuion([("aw2+b7*2=c*2", 0.1), ("aw2+b7*2=c*2", 0.1)])
    assert intentar_formula(lector(motor), bloque("aw2+b7*2=c*2", 0.1), BASE, "aw2+b7*2=c*2") is None


def test_igualdades_cortas_son_formulas():
    assert es_formula("F = ma") and es_formula("v=d/t") and es_formula("x = 2")
    assert not es_formula("Nota: la tarea es para el lunes") and not es_formula("Tema = derivadas parciales")


# ------------------------------------------------------------------ calidad e inclinación

def test_inclinacion_detectada_y_corregida():
    for p, angulo in (("desarrollo", 6.0), ("evaluacion", -7.0)):
        m = foto_girada(p, TEXTOS[p], angulo)
        assert abs(estimar_inclinacion(m.imagen) + angulo) <= 0.5
    assert estimar_inclinacion(impreso_cuaderno().imagen) == 0.0
    assert estimar_inclinacion(diagrama().imagen) == 0.0           # un dibujo no se «endereza»
    assert estimar_inclinacion(np.full((300, 300, 3), 250, np.uint8)) == 0.0
    girada = enderezar(impreso_cuaderno().imagen, 5)
    assert girada.shape == impreso_cuaderno().imagen.shape


def test_diagnostico_de_calidad():
    assert diagnosticar(impreso_cuaderno().imagen).nivel == "buena"
    borrosa = diagnosticar(foto_borrosa("evaluacion", TEXTOS["evaluacion"]).imagen)
    assert borrosa.nivel == "insuficiente" and "REPETIR_FOTO" in borrosa.avisos and "IMAGEN_BORROSA" in borrosa.avisos
    assert "BAJO_CONTRASTE" in diagnosticar(tinta_tenue("evaluacion", TEXTOS["evaluacion"]).imagen).avisos
    assert "TEXTO_PEQUENO" in diagnosticar(letra_pequena("evaluacion", TEXTOS["evaluacion"]).imagen).avisos
    # Las métricas son números o booleanos: se pueden registrar sin exponer la foto
    assert all(v is None or isinstance(v, (int, float, bool)) for v in borrosa.metricas.values())


def test_la_foto_original_no_se_modifica():
    img = foto_girada("evaluacion", TEXTOS["evaluacion"], -7.0).imagen
    copia = img.copy()
    reconocer_pagina(img, "cuaderno", "spa", modo="adaptativo", motor=MotorGuion([]))
    assert np.array_equal(img, copia)


def test_sin_motor_es_un_error_claro_y_no_un_texto_vacio():
    with pytest.raises(ErrorOCR) as e:
        reconocer_pagina(np.array(hoja_cuaderno()), "cuaderno", "spa", modo="adaptativo", motor=MotorNinguno())
    assert e.value.codigo == "OCR_NO_DISPONIBLE"


# ------------------------------------------------------------------ contrato del documento

def doc_ocr(**extra):
    return {"titulo": "T", "paginas": [{"id": "p1", "orden": 1, "tipo_fuente": "cuaderno", "archivo_original": "a1",
                                        "ancho": 10, "alto": 10}],
            "bloques": [{"id": "b1", "pagina": "p1", "orden": 0, "tipo": "texto", "origen": "ocr", "estado": "incierto",
                         "confianza": 0.9, "texto": "Repasar eltema", "texto_original": "Repasar eltema", **extra}]}


def test_documentos_anteriores_siguen_siendo_validos():
    d = validar(doc_ocr())
    assert d.bloques[0].alternativas == [] and d.bloques[0].procedencia is None and d.paginas[0].calidad is None


def test_el_cliente_no_puede_cambiar_alternativas_ni_procedencia():
    extra = {"alternativas": [{"texto": "Repasar el tema", "confianza": 0.88, "variante": "ampliada"}],
             "procedencia": {"motor": "tesseract", "version": "5.3.4", "reconocimiento": "adaptativo/1",
                             "variante": "pagina", "psm": 4, "lecturas": 2},
             "revision": "lecturas_distintas"}
    anterior = validar(doc_ocr(**extra))
    editado = doc_ocr(alternativas=[{"texto": "texto inventado"}], procedencia=None, revision=None)
    editado["bloques"][0]["texto"] = "Repasar el tema"   # el usuario elige la alternativa
    nuevo = fusionar(anterior, Documento.model_validate(editado))
    b = nuevo.bloques[0]
    assert b.texto == "Repasar el tema" and b.texto_original == "Repasar eltema" and b.editado
    assert [a.texto for a in b.alternativas] == ["Repasar el tema"]
    assert b.procedencia.lecturas == 2 and b.revision == "lecturas_distintas"


def test_contrato_rechaza_valores_fuera_de_rango():
    from app.core.errores import ApiError
    with pytest.raises(ApiError):
        validar(doc_ocr(revision="lo_que_sea"))
    with pytest.raises(ApiError):
        validar(doc_ocr(alternativas=[{"texto": str(i)} for i in range(4)]))


def test_modo_clasico_se_conserva_para_comparar():
    r = reconocer_pagina(np.array(hoja_cuaderno()), "cuaderno", "spa", modo="clasico", motor=MotorGuion([]))
    assert r.modo == "clasico" and r.calidad is None


# ------------------------------------------------------------------ integración (Tesseract)

def png(img):
    return cv2.imencode(".png", img)[1].tobytes()


def esperar(c, tid, limite=90):
    fin = time.time() + limite
    while time.time() < fin:
        t = c.get(f"/api/v2/trabajos/{tid}").json()["trabajo"]
        if t["estado"] not in ("pendiente", "procesando"):
            return t
        time.sleep(0.2)
    raise AssertionError("el análisis no terminó")


@requiere_tesseract
def test_de_la_foto_al_pdf_con_revision_y_correccion(nuevo_cliente):
    """Foto girada + foto borrosa → avisos, procedencia y alternativas → corrección → PDF corregido."""
    c = nuevo_cliente()
    c.registrar()
    t = TEXTOS["evaluacion"]
    girada, borrosa = foto_girada("evaluacion", t, -7.0), foto_borrosa("evaluacion", t)
    files = [("paginas", ("girada.png", png(girada.imagen), "image/png")),
             ("paginas", ("borrosa.png", png(borrosa.imagen), "image/png"))]
    r = c.post("/api/v2/apuntes", files=files, data={"tipos": ["cuaderno", "pizarron"], "titulo": "Presión"})
    assert r.status_code == 202, r.text
    aid = r.json()["apunte"]["id"]
    assert esperar(c, r.json()["trabajo"]["id"])["estado"] == "completado"
    apunte = c.get(f"/api/v2/apuntes/{aid}").json()["apunte"]
    doc = apunte["documento"]
    p1, p2 = doc["paginas"]
    assert "IMAGEN_GIRADA" in p1["advertencias"] and p1["calidad"]["metricas"]["inclinacion"] != 0
    assert p2["calidad"]["nivel"] == "insuficiente" and "REPETIR_FOTO" in p2["advertencias"]
    texto_p1 = "\n".join(b["texto"] for b in doc["bloques"] if b["pagina"] == "p1")
    assert "La presión es fuerza por área." in texto_p1          # el texto girado se recupera
    assert not any(b["estado"] == "reconocido" for b in doc["bloques"] if b["pagina"] == "p2")
    for b in doc["bloques"]:
        assert b["procedencia"]["motor"] == "tesseract" and b["procedencia"]["reconocimiento"] == "adaptativo/1"
        assert b["texto"] == b["texto_original"]

    # El usuario corrige un bloque; la procedencia y el original se conservan y el PDF usa la corrección
    objetivo = next(b for b in doc["bloques"] if b["pagina"] == "p1" and b["texto"])
    objetivo["texto"] = "Texto corregido por el usuario"
    r = c.put(f"/api/v2/apuntes/{aid}/documento", json=doc, headers={"If-Match": str(apunte["version"])})
    assert r.status_code == 200, r.text
    guardado = next(b for b in c.get(f"/api/v2/apuntes/{aid}").json()["apunte"]["documento"]["bloques"]
                    if b["id"] == objetivo["id"])
    assert guardado["editado"] and guardado["texto_original"] != guardado["texto"] and guardado["procedencia"]
    exp = c.post(f"/api/v2/apuntes/{aid}/exportaciones", json={}).json()
    assert esperar(c, exp["trabajo"]["id"])["estado"] == "completado"
    pdf = c.get(c.get(f"/api/v2/exportaciones/{exp['exportacion']['id']}").json()["exportacion"]["descarga"]).content
    texto_pdf = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
    assert "Texto corregido por el usuario" in texto_pdf


@requiere_tesseract
def test_regresion_adaptativo_frente_a_clasico():
    """En el corpus difícil, el modo adaptativo no empeora el CER de ninguna muestra (más de 2 puntos)
    ni da más texto falso por seguro que el flujo anterior; y mejora el CER medio."""
    from herramientas.evaluar_dificil import evaluar, resumen
    antes = evaluar("clasico", ["evaluacion"])["muestras"]
    despues = evaluar("adaptativo", ["evaluacion"])["muestras"]
    for a, d in zip(antes, despues):
        if a["cer"] is not None:
            assert d["cer"] <= a["cer"] + 0.02, (a["muestra"], a["cer"], d["cer"])
        assert d["formulas_falsas"] <= a["formulas_falsas"], a["muestra"]
    ra, rd = resumen(antes), resumen(despues)
    assert rd["reconocidos_con_errores"] <= ra["reconocidos_con_errores"]
    assert rd["cer_medio"] < ra["cer_medio"]
