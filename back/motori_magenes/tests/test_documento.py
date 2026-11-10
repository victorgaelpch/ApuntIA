"""Modelo intermedio editable (BACK-17)."""

import copy
import json
import re
from pathlib import Path

import pytest

from app.core.errores import ApiError
from app.services.documento import Documento, fusionar, texto_plano, validar

EJEMPLO = json.loads(re.search(r"```json\n(.*?)```",
                               (Path(__file__).resolve().parents[3] / "docs" / "api-v2.md").read_text(), re.S).group(1))


def test_el_ejemplo_del_contrato_es_valido():
    doc = validar(EJEMPLO)
    assert [b.tipo for b in doc.bloques] == ["titulo", "formula", "manuscrito", "tabla"]


def test_ida_y_vuelta_sin_perdidas():
    doc = validar(EJEMPLO)
    otra = validar(json.loads(doc.model_dump_json()))
    assert otra == doc
    assert otra.bloques[1].latex == EJEMPLO["bloques"][1]["latex"]
    assert otra.bloques[3].tabla.filas == [["x^2", "2x"]]


@pytest.mark.parametrize("cambio,mensaje", [
    (lambda d: d["bloques"][0].update(pagina="no-existe"), "página inexistente"),
    (lambda d: d["bloques"].append(copy.deepcopy(d["bloques"][0])), "mismo id"),
    (lambda d: d["bloques"][3]["tabla"]["filas"].append(["solo una"]), "celdas"),
    (lambda d: d["bloques"][0].update(bbox=[10, 10, 5, 5]), "bbox"),
    (lambda d: d["bloques"][0].update(confianza=1.5), "confianza"),
    (lambda d: d["bloques"][0].update(campo_raro=1), "campo_raro"),
    (lambda d: d["ampliaciones"][0]["fuente"].update(url="javascript:alert(1)"), "https"),
    (lambda d: d.update(esquema="otro/9"), "esquema"),
])
def test_esquemas_invalidos_se_rechazan(cambio, mensaje):
    datos = copy.deepcopy(EJEMPLO)
    cambio(datos)
    with pytest.raises(ApiError) as exc:
        validar(datos)
    assert exc.value.codigo == "DOCUMENTO_INVALIDO" and mensaje in exc.value.mensaje


def test_la_edicion_conserva_la_procedencia():
    anterior = validar(EJEMPLO)
    datos = copy.deepcopy(EJEMPLO)
    datos["bloques"][0].update(texto="Derivadas (corregido)", texto_original="HACKEADO", confianza=1.0,
                               bbox=[0, 0, 1, 1])
    nuevo = fusionar(anterior, validar(datos))
    b = nuevo.bloques[0]
    assert b.texto == "Derivadas (corregido)" and b.editado is True
    assert b.texto_original == "Derivadas" and b.confianza == 0.93 and b.bbox == [120, 80, 900, 140]


def test_bloque_sin_cambios_no_queda_marcado_como_editado():
    anterior = validar(EJEMPLO)
    nuevo = fusionar(anterior, validar(copy.deepcopy(EJEMPLO)))
    assert nuevo.bloques[0].editado is False


def test_no_se_pueden_inventar_bloques_de_ocr():
    anterior = validar(EJEMPLO)
    datos = copy.deepcopy(EJEMPLO)
    datos["bloques"].append({"id": "falso", "pagina": "p1", "orden": 9, "tipo": "texto", "origen": "ocr", "texto": "x"})
    with pytest.raises(ApiError, match="origen"):
        fusionar(anterior, validar(datos))


def test_ampliaciones_solo_cambian_de_estado():
    anterior = validar(EJEMPLO)
    datos = copy.deepcopy(EJEMPLO)
    datos["ampliaciones"][0].update(estado="aceptada", texto="Texto inventado",
                                    fuente={**datos["ampliaciones"][0]["fuente"], "url": "https://otra.example"})
    nuevo = fusionar(anterior, validar(datos))
    a = nuevo.ampliaciones[0]
    assert a.estado == "aceptada" and a.texto == "…" and a.fuente.url.startswith("https://es.wikipedia.org")
    datos["ampliaciones"].append({**datos["ampliaciones"][0], "id": "nueva"})
    with pytest.raises(ApiError, match="investigación"):
        fusionar(anterior, validar(datos))


def test_quitar_una_ampliacion_no_la_borra_en_silencio():
    anterior = validar(EJEMPLO)
    datos = copy.deepcopy(EJEMPLO)
    datos["ampliaciones"] = []
    assert len(fusionar(anterior, validar(datos)).ampliaciones) == 1


def test_texto_plano_para_busqueda_excluye_ampliaciones():
    texto = texto_plano(validar(EJEMPLO))
    assert "Derivadas" in texto and "Función" in texto and "lim" in texto
    assert "wikipedia" not in texto
