"""Limpieza de los bloques de la tarea «documento» después de leerlos con el modelo.

Hallazgo real (cuaderno de electrónica, 15/11/2026): de 19 bloques, unos 12 eran la plantilla
impresa del cuaderno («Día Mes Año», «Folio», «Nombre: Tema:») o sus adornos («dos figuras
abstractas, posiblemente animales», «una línea curva marrón»). El modelo los leyó bien: el
problema es que no son apuntes. Aquí se apartan, sin borrarlos en silencio: cada descarte vuelve
en `segmentacion.descartes` con su caja y su motivo, y ApuntIA avisa de cuántos hubo.

Criterios (conservadores: ante la duda, el bloque se queda):
- PLANTILLA: el texto son SOLO palabras de encabezado impreso, sin números. «Tema: Mallas» o
  «Fecha 15/11» se quedan porque llevan algo escrito por el alumno.
- ADORNO: el modelo dijo que es un dibujo o que no se lee, es pequeño (< 2 % de la foto) y está
  en la franja de arriba (encabezado). Un circuito o una gráfica de verdad ocupan más.
Además, los dibujos que se tocan se UNEN en uno solo: la segmentación puede partir un circuito en
la resistencia, la fuente y los cables, y en el PDF deben verse juntos.
"""

from __future__ import annotations

import re
import unicodedata

PLANTILLA = {
    "dia", "mes", "ano", "fecha", "folio", "nombre", "tema", "materia", "asignatura", "grupo", "grado",
    "seccion", "profesor", "profesora", "maestro", "maestra", "alumno", "alumna", "hoja", "pagina",
    "no", "num", "numero", "escuela", "firma",
}
FRANJA_ENCABEZADO = 0.20   # fracción superior de la foto
AREA_ADORNO = 0.02         # fracción de la foto
MARGEN_DIBUJOS = 0.02      # dos dibujos a menos de este hueco (fracción del lado mayor) son uno (medido: 4 circuitos, 4 dibujos)


def _sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def es_plantilla(texto: str) -> bool:
    if not texto or re.search(r"\d", texto):
        return False
    palabras = re.findall(r"[^\W\d_]+", _sin_acentos(texto).lower())
    return bool(palabras) and all(p in PLANTILLA for p in palabras)


def _motivo(b: dict, ancho: int, alto: int) -> str | None:
    if b["tipo"] in ("texto", "manuscrito") and not b.get("latex") and es_plantilla(b.get("texto") or ""):
        return "plantilla impresa del cuaderno"
    x0, y0, x1, y1 = b["bbox"]
    pequeno = (x1 - x0) * (y1 - y0) < AREA_ADORNO * ancho * alto
    arriba = (y0 + y1) / 2 < FRANJA_ENCABEZADO * alto
    # «no se lee» del modelo (no un fallo de la respuesta, que lleva su duda y se conserva)
    ilegible = b["estado"] == "no_reconocido" and not b.get("dudas")
    if (b["tipo"] == "imagen" or ilegible) and pequeno and arriba:
        return "adorno del encabezado del cuaderno"
    return None


def _cerca(a: list[int], b: list[int], margen: float) -> bool:
    return not (a[2] + margen < b[0] or b[2] + margen < a[0] or a[3] + margen < b[1] or b[3] + margen < a[1])


def unir_dibujos(bloques: list[dict], ancho: int, alto: int) -> list[dict]:
    margen = MARGEN_DIBUJOS * max(ancho, alto)
    bloques = list(bloques)
    cambiado = True
    while cambiado:
        cambiado = False
        for i, a in enumerate(bloques):
            if a["tipo"] != "imagen":
                continue
            for j in range(i + 1, len(bloques)):
                b = bloques[j]
                if b["tipo"] == "imagen" and _cerca(a["bbox"], b["bbox"], margen):
                    caja = [min(a["bbox"][0], b["bbox"][0]), min(a["bbox"][1], b["bbox"][1]),
                            max(a["bbox"][2], b["bbox"][2]), max(a["bbox"][3], b["bbox"][3])]
                    descripcion = "; ".join(d.strip().rstrip(".") for d in (a.get("descripcion"), b.get("descripcion")) if d) or None
                    bloques[i] = {**a, "bbox": caja, "descripcion": descripcion, "texto": "",
                                  "dudas": (a.get("dudas") or []) + (b.get("dudas") or [])}
                    del bloques[j]
                    cambiado = True
                    break
            if cambiado:
                break
    return bloques


def depurar(bloques: list[dict], ancho: int, alto: int) -> tuple[list[dict], list[dict]]:
    """(bloques que se quedan, descartes con caja y motivo). Renumera `orden` sin huecos."""
    conservados, descartes = [], []
    for b in bloques:
        motivo = _motivo(b, ancho, alto)
        if motivo:
            descartes.append({"bbox": b["bbox"], "motivo": motivo,
                              "texto": (b.get("texto") or b.get("descripcion") or "")[:80]})
        else:
            conservados.append(b)
    conservados = unir_dibujos(conservados, ancho, alto)
    for n, b in enumerate(conservados, 1):
        b["orden"] = n
    return conservados, descartes
