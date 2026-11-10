"""Banco de evaluación de ApuntIA (FULL-19). Guía: docs/evaluacion.md.

Mide la calidad REAL del producto, de punta a punta y por la API (en proceso, con una
carpeta de datos temporal): cada muestra del corpus sintético etiquetado se sube como un
apunte, se analiza con el flujo de producción y se compara con su verdad de referencia.

    python fullstack/evaluacion/evaluar.py                      # informe en fullstack/evaluacion/resultados/
    python fullstack/evaluacion/evaluar.py --comparar fullstack/evaluacion/linea-base.json
    python fullstack/evaluacion/evaluar.py --guardar-linea-base

Mide: texto (CER, WER, bloques reconocidos/inciertos/sin leer y «reconocidos con errores»),
orden de lectura, fórmulas (exactas, válidas, falsas), varias páginas, comprobaciones del PDF
(páginas, texto seleccionable, Unicode, tabla completa, fórmula visible, enlace de la fuente,
metadatos), robustez ante archivos inválidos o grandes, regresiones de errores ya vistos,
tiempos y memoria. Todas las cifras son CALCULADAS; no hay valores estimados a mano.
Sale con 1 si, comparado con la línea base, algo empeora.
"""

import argparse
import csv
import io
import json
import platform
import resource
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BACKEND = RAIZ / "back" / "motori_magenes"
sys.path.insert(0, str(BACKEND))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from herramientas.claves_prueba import clave_de_prueba  # noqa: E402

TOLERANCIA_CER = 0.02   # empeorar más de 2 puntos de CER en una muestra es una regresión


def png(imagen: np.ndarray) -> bytes:
    return cv2.imencode(".png", imagen)[1].tobytes()


def lineas_exactas(texto: str, lineas: list[str]) -> float | None:
    """Fracción de líneas de referencia que aparecen tal cual en el texto reconocido."""
    return round(sum(l in texto for l in lineas) / len(lineas), 3) if lineas else None


def orden_correcto(texto: str, lineas: list[str]) -> float | None:
    """Entre las líneas encontradas, fracción que está en el orden correcto (subsecuencia creciente).
    Separado de `lineas_exactas` para no mezclar errores de reconocimiento con errores de orden."""
    encontradas = [p for p in (texto.find(l) for l in lineas) if p >= 0]
    if not encontradas:
        return None
    mejor = []  # longitud de la subsecuencia creciente más larga
    for p in encontradas:
        import bisect
        i = bisect.bisect_left(mejor, p)
        mejor[i:i + 1] = [p]
    return round(len(mejor) / len(encontradas), 3)


class Banco:
    def __init__(self):
        from fastapi.testclient import TestClient
        from app.core import contexto
        from app.main import app
        self.tmp = tempfile.TemporaryDirectory(prefix="apuntia-evaluacion-")
        self.ctx = contexto.reiniciar(Path(self.tmp.name))
        self.ctx.trabajos.iniciar()
        self.http = TestClient(app)
        r = self.http.post("/api/v2/auth/registro", json={"email": "evaluacion@example.com", "nombre": "Banco",
                                                           "password": clave_de_prueba("c12")})
        self.csrf = r.json()["csrf"]

    def cerrar(self):
        self.ctx.trabajos.detener()
        self.tmp.cleanup()

    def pedir(self, metodo, ruta, **kw):
        return self.http.request(metodo, ruta, headers={"X-CSRF-Token": self.csrf, **kw.pop("headers", {})}, **kw)

    def esperar(self, tid, limite=180):
        fin = time.time() + limite
        while time.time() < fin:
            t = self.pedir("GET", f"/api/v2/trabajos/{tid}").json()["trabajo"]
            if t["estado"] not in ("pendiente", "procesando"):
                return t
            time.sleep(0.05)
        raise TimeoutError(tid)

    def analizar(self, muestras, titulo="Evaluación"):
        archivos = [("paginas", (f"{m.nombre}.png", png(m.imagen), "image/png")) for m in muestras]
        datos = {"tipos": [m.tipo_fuente for m in muestras], "titulo": titulo}
        inicio = time.perf_counter()
        r = self.pedir("POST", "/api/v2/apuntes", files=archivos, data=datos)
        if r.status_code != 202:
            raise RuntimeError(r.text)
        t = self.esperar(r.json()["trabajo"]["id"])
        ms = (time.perf_counter() - inicio) * 1000
        apunte = self.pedir("GET", f"/api/v2/apuntes/{r.json()['apunte']['id']}").json()["apunte"]
        return apunte, t, ms


def evaluar_texto(banco: "Banco") -> list[dict]:
    from herramientas.corpus import corpus
    from herramientas.evaluar_ocr import _norm
    from herramientas.metricas import cer, wer
    filas = []
    for m in corpus():
        apunte, trabajo, ms = banco.analizar([m], m.nombre)
        bloques = apunte["documento"]["bloques"]
        texto = "\n".join(b["texto"] for b in bloques if b["texto"])
        real = "\n".join(m.lineas)
        estados = [b["estado"] if b["texto"] else "no_reconocido" for b in bloques]
        reales = [_norm(l) for l in m.lineas]
        con_errores = sum(1 for b in bloques if b["texto"] and b["estado"] == "reconocido"
                          and any(_norm(x) not in reales for x in b["texto"].split("\n")))
        filas.append({
            "muestra": m.nombre, "fuente": m.tipo_fuente, "escritura": m.escritura, "trabajo": trabajo["estado"],
            "cer": round(cer(texto, real), 4), "wer": round(wer(texto, real), 4),
            "reconocidos": estados.count("reconocido"), "inciertos": estados.count("incierto"),
            "sin_leer": estados.count("no_reconocido"), "reconocidos_con_errores": con_errores,
            "conservados_como_imagen": sum(1 for b in bloques if b["recorte"] and not b["texto"]),
            "lineas_exactas": lineas_exactas(texto, m.lineas),
            "orden_lectura": orden_correcto(texto, m.lineas),
            "ms": round(ms),
        })
    return filas


def evaluar_formulas() -> dict:
    from herramientas.corpus import formulas_2d, formulas_pizarron
    from herramientas.evaluar_formulas import _n, evaluar
    total = exactas = falsas = validas = 0
    detalle = []
    for m in (formulas_pizarron(), formulas_2d()):
        resultado, obtenidas = evaluar(m)
        for latex_real, b in resultado:
            total += 1
            exactas += b is not None
            detalle.append({"muestra": m.nombre, "esperada": latex_real, "exacta": b is not None})
        for b in obtenidas:
            if getattr(b, "latex_valido", False):
                validas += 1
                if b.tipo == "formula" and b.estado == "reconocido" and all(_n(getattr(b, "latex", "")) != _n(r) for r, _ in resultado):
                    falsas += 1
    return {"total": total, "exactas": exactas, "latex_validos": validas, "falsas_reconocidas": falsas, "detalle": detalle}


def evaluar_paginas_y_pdf(banco: "Banco") -> dict:
    """Dos páginas (cuaderno + pizarrón) → orden y PDF con tabla, fórmula y fuente citada."""
    from pypdf import PdfReader
    from herramientas.corpus import impreso_cuaderno, pizarron_oscuro
    from app.services.documento import Ampliacion, Bloque, Documento, Fuente, Tabla
    from app.services.estructura import estructurar
    from app.services.pdf import OpcionesPDF, generar_pdf
    apunte, trabajo, ms = banco.analizar([impreso_cuaderno(), pizarron_oscuro()], "Dos páginas")
    doc = Documento.model_validate(apunte["documento"])
    paginas_bloques = [b.pagina for b in doc.bloques]
    orden_paginas = paginas_bloques == sorted(paginas_bloques, key=lambda p: int(p[1:]))
    tabla = Tabla(encabezados=["Función", "Derivada"], filas=[["x²", "2x"], ["sen x", "cos x"]])
    doc.bloques += [Bloque(id="eval-t", orden=900, tipo="tabla", origen="usuario", tabla=tabla),
                    Bloque(id="eval-f", orden=901, tipo="formula", origen="usuario", latex="\\frac{a}{b} + \\sqrt{x}", latex_valido=True)]
    doc.ampliaciones.append(Ampliacion(id="aeval", concepto="Derivada", texto="La derivada mide el cambio.", estado="aceptada",
                                       fuente=Fuente(titulo="Derivada", url="https://es.wikipedia.org/wiki/Derivada",
                                                     proveedor="wikipedia", consultado="2026-11-10", licencia="CC BY-SA 4.0")))
    inicio = time.perf_counter()
    datos, n = generar_pdf(doc, estructurar(doc), apunte["version"], lambda a: banco.ctx.almacen.leer(
        banco.ctx.bd.uno("SELECT usuario_id FROM archivos WHERE id = ?", (a,))["usuario_id"], a), OpcionesPDF(incluir_originales=True))
    ms_pdf = (time.perf_counter() - inicio) * 1000
    lector = PdfReader(io.BytesIO(datos))
    texto = "\n".join(p.extract_text() for p in lector.pages)
    enlaces = [a.get_object().get("/A", {}).get("/URI") for p in lector.pages for a in (p.get("/Annots") or [])]
    imagenes = sum(len(p.images) for p in lector.pages)
    comprobaciones = {
        "abre_y_tiene_paginas": len(lector.pages) == n and n > 0,
        "texto_seleccionable": "La derivada mide la razón de cambio" in texto,
        "unicode": all(c in texto for c in ["razón", "Función", "x²", "Información"]),
        "tabla_completa": all(c in texto for c in ["Función", "Derivada", "x²", "2x", "sen x", "cos x"]),
        "formula_e_imagenes_visibles": imagenes >= 3,   # fórmula dibujada + 2 fotos del anexo
        "enlace_de_la_fuente": "https://es.wikipedia.org/wiki/Derivada" in enlaces,
        "metadatos": lector.metadata.title == "Dos páginas" and lector.metadata.author == "ApuntIA",
        "orden_de_las_paginas": orden_paginas and texto.find("razón de cambio") < texto.rfind("Ejemplo"),
    }
    return {"trabajo": trabajo["estado"], "paginas_pdf": n, "kb": round(len(datos) / 1024), "ms_analisis": round(ms),
            "ms_pdf": round(ms_pdf), "comprobaciones": comprobaciones}


def evaluar_robustez(banco: "Banco") -> dict:
    from app.core.config import settings
    casos = {
        "html_disfrazado": b"<html><script>alert(1)</script></html>",
        "vacio": b"",
        "demasiado_grande": b"\x89PNG\r\n\x1a\n" + b"0" * int(settings.max_upload_mb * 1024 * 1024 + 10),
        "png_truncado": png(np.zeros((50, 50, 3), np.uint8))[:60],
    }
    resultado = {}
    for nombre, datos in casos.items():
        inicio = time.perf_counter()
        r = banco.pedir("POST", "/api/v2/apuntes", files=[("paginas", ("foto.png", datos, "image/png"))], data={"tipos": "cuaderno"})
        error = r.json().get("error", {})
        detalle = (error.get("detalles") or [{}])[0].get("codigo") if error.get("detalles") else error.get("codigo")
        resultado[nombre] = {"http": r.status_code, "codigo": detalle, "ms": round((time.perf_counter() - inicio) * 1000)}
    return resultado


# Errores reales observados durante el desarrollo, para que no vuelvan (FULL-19).
REGRESIONES = [
    ("BACK-12: la mediana borraba la tilde de «rápido» en el pizarrón de tiza",
     lambda t: "rápido" in t["pizarron_oscuro"]["texto"]),
    ("BACK-21: un símbolo dudoso vaciaba un párrafo bueno entero",
     lambda t: t["impreso_cuaderno"]["sin_leer"] == 0),
    ("BACK-15: fórmulas 2D no se dan por reconocidas (se conservan como imagen)",
     lambda t: t["formulas_2d"]["reconocidos"] == 0),
    ("BACK-14: ningún manuscrito se presenta como reconocido con errores",
     lambda t: all(f["reconocidos_con_errores"] == 0 for f in t.values() if f["escritura"] == "manuscrito")),
    ("FULL-19: la cuadrícula no se convierte en texto",
     lambda t: t["cuaderno_cuadriculado"]["cer"] <= 0.02),
    ("FULL-19: un diagrama se conserva como imagen y no se inventa texto",
     lambda t: t["diagrama"]["conservados_como_imagen"] >= 1 and t["diagrama"]["cer"] <= 0.1),
]


def versiones() -> dict:
    import reportlab
    from app.services.ocr import motor_ocr
    return {"python": platform.python_version(), "opencv": cv2.__version__, "numpy": np.__version__,
            "reportlab": reportlab.Version, "ocr": motor_ocr().info()}


def comparar(actual: dict, base: dict) -> list[str]:
    problemas = []
    previas = {f["muestra"]: f for f in base["texto"]}
    for f in actual["texto"]:
        b = previas.get(f["muestra"])
        if not b:
            continue
        if f["cer"] > b["cer"] + TOLERANCIA_CER:
            problemas.append(f"{f['muestra']}: CER {b['cer']:.3f} → {f['cer']:.3f}")
        if f["reconocidos_con_errores"] > b["reconocidos_con_errores"]:
            problemas.append(f"{f['muestra']}: más bloques reconocidos con errores ({b['reconocidos_con_errores']} → {f['reconocidos_con_errores']})")
    if actual["formulas"]["exactas"] < base["formulas"]["exactas"]:
        problemas.append(f"fórmulas exactas {base['formulas']['exactas']} → {actual['formulas']['exactas']}")
    if actual["formulas"]["falsas_reconocidas"] > base["formulas"]["falsas_reconocidas"]:
        problemas.append("hay fórmulas falsas reconocidas")
    for nombre, ok in actual["pdf"]["comprobaciones"].items():
        if base["pdf"]["comprobaciones"].get(nombre) and not ok:
            problemas.append(f"PDF: falla «{nombre}»")
    for nombre, r in actual["robustez"].items():
        if nombre in base["robustez"] and r["http"] != base["robustez"][nombre]["http"]:
            problemas.append(f"robustez {nombre}: HTTP {base['robustez'][nombre]['http']} → {r['http']}")
    problemas += [f"regresión: {n}" for n, ok in actual["regresiones"].items() if not ok]
    return problemas


def informe_md(r: dict, problemas: list[str] | None) -> str:
    v = r["versiones"]
    filas = ["| Muestra | Fuente | Escritura | CER | WER | Reconocidos | Inciertos | Sin leer | Reconocidos con errores | Como imagen | Líneas exactas | Orden | ms |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for f in r["texto"]:
        orden = "—" if f["orden_lectura"] is None else f"{f['orden_lectura']:.0%}"
        exactas = "—" if f["lineas_exactas"] is None else f"{f['lineas_exactas']:.0%}"
        filas.append(f"| {f['muestra']} | {f['fuente']} | {f['escritura']} | {f['cer']:.1%} | {f['wer']:.1%} | {f['reconocidos']} | "
                     f"{f['inciertos']} | {f['sin_leer']} | {f['reconocidos_con_errores']} | {f['conservados_como_imagen']} | "
                     f"{exactas} | {orden} | {f['ms']} |")
    fo = r["formulas"]
    pdf = r["pdf"]
    partes = [f"# Evaluación de ApuntIA — {r['fecha']}", "",
              f"Python {v['python']} · OpenCV {v['opencv']} · ReportLab {v['reportlab']} · OCR {v['ocr'].get('motor')} {v['ocr'].get('version', '')} "
              f"({', '.join(v['ocr'].get('idiomas', []))})", "", "## Texto (una foto por apunte, flujo completo)", "", *filas, "",
              "## Fórmulas", "", f"Exactas: **{fo['exactas']}/{fo['total']}** · LaTeX válidos: {fo['latex_validos']} · Falsas reconocidas: {fo['falsas_reconocidas']}", "",
              "## Dos páginas y PDF", "",
              f"Análisis: {pdf['trabajo']} en {pdf['ms_analisis']} ms · PDF: {pdf['paginas_pdf']} páginas, {pdf['kb']} KB, {pdf['ms_pdf']} ms", "",
              *[f"- {'✔' if ok else '✖'} {n.replace('_', ' ')}" for n, ok in pdf["comprobaciones"].items()], "",
              "## Robustez", "", "| Caso | HTTP | Código | ms |", "|---|---:|---|---:|",
              *[f"| {n} | {x['http']} | {x['codigo']} | {x['ms']} |" for n, x in r["robustez"].items()], "",
              "## Regresiones de errores ya vistos", "", *[f"- {'✔' if ok else '✖'} {n}" for n, ok in r["regresiones"].items()], "",
              f"Tiempo total: {r['segundos']} s · Memoria máxima del proceso: {r['memoria_mb']} MB"]
    if problemas is not None:
        partes += ["", "## Comparación con la línea base", ""] + ([f"- ✖ {p}" for p in problemas] or ["- ✔ Sin regresiones."])
    return "\n".join(partes) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--comparar", type=Path, help="línea base JSON con la que comparar")
    parser.add_argument("--guardar-linea-base", action="store_true", help="guarda el resultado como nueva línea base")
    parser.add_argument("--salida", type=Path, default=RAIZ / "fullstack" / "evaluacion" / "resultados")
    args = parser.parse_args()
    import logging
    logging.disable(logging.WARNING)  # el informe es la salida; los registros de cada petición sobran
    from app.services.ocr import motor_ocr
    if not motor_ocr().disponible():
        print("ERROR: el OCR no está disponible (instala Tesseract). No se generan métricas.", file=sys.stderr)
        return 2
    inicio = time.time()
    banco = Banco()
    try:
        texto = evaluar_texto(banco)
        # Texto completo para las regresiones (no se guarda en el informe: puede ser largo)
        por_muestra = {f["muestra"]: f for f in texto}
        for m in banco.pedir("GET", "/api/v2/apuntes?por_pagina=100").json()["elementos"]:
            doc = banco.pedir("GET", f"/api/v2/apuntes/{m['id']}").json()["apunte"]["documento"]
            if m["titulo"] in por_muestra:
                por_muestra[m["titulo"]]["texto"] = "\n".join(b["texto"] for b in doc["bloques"] if b["texto"])
        resultado = {"fecha": datetime.now().isoformat(timespec="seconds"), "versiones": versiones(),
                     "texto": texto, "formulas": evaluar_formulas(), "pdf": evaluar_paginas_y_pdf(banco),
                     "robustez": evaluar_robustez(banco)}
        resultado["regresiones"] = {n: bool(f(por_muestra)) for n, f in REGRESIONES}
        for f in texto:
            f.pop("texto", None)
        resultado["segundos"] = round(time.time() - inicio, 1)
        resultado["memoria_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    finally:
        banco.cerrar()

    problemas = None
    if args.comparar:
        problemas = comparar(resultado, json.loads(args.comparar.read_text(encoding="utf-8")))
    carpeta = args.salida / datetime.now().strftime("%Y%m%d-%H%M%S")
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "informe.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(carpeta / "informe.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(texto[0].keys()))
        escritor.writeheader()
        escritor.writerows(texto)
    md = informe_md(resultado, problemas)
    (carpeta / "informe.md").write_text(md, encoding="utf-8")
    if args.guardar_linea_base:
        (RAIZ / "fullstack" / "evaluacion" / "linea-base.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(md)
    print(f"Informes en {carpeta.relative_to(RAIZ) if carpeta.is_relative_to(RAIZ) else carpeta}")
    return 1 if problemas or not all(resultado["regresiones"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
