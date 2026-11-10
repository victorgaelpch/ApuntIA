"""Escenarios de aceptación educativos de ApuntIA (FULL-24). Guía: docs/aceptacion.md.

Recorre de punta a punta, por la API y con el análisis de producción, los escenarios de uso real
(pizarrón corto, cuaderno manuscrito, imagen difícil, hoja impresa, fórmulas, tabla, diagrama, varias
páginas; sin y con información complementaria; sin conexión) y aplica los CRITERIOS DE RECHAZO de la
entrega: PDF vacío, fórmula perdida, cita inventada, acceso a apuntes ajenos y texto inventado.

    python fullstack/evaluacion/aceptacion.py            # informe en fullstack/evaluacion/resultados/
    python fullstack/evaluacion/aceptacion.py --salida carpeta

Sale con 1 si se cumple algún criterio de rechazo. Un escenario «parcial» NO es un rechazo: es una
limitación conocida y documentada (p. ej. una tabla fotografiada no se convierte sola en tabla).
Las fotos son sintéticas (herramientas/corpus.py); la fuente externa es una Wikipedia SIMULADA con el
formato real de su API, porque la prueba no puede depender de Internet: se indica así en el informe.
"""

from __future__ import annotations

import argparse
import logging
import io
import json
import sys
import time
import urllib.error
import urllib.parse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluar  # noqa: E402  (añade el backend al path)
from evaluar import RAIZ, Banco, png  # noqa: E402
from herramientas.claves_prueba import clave_de_prueba  # noqa: E402


COMPLETO, PARCIAL = "completo", "parcial"


# ---------------------------------------------------------------- utilidades
def texto_pdf(datos: bytes) -> tuple[str, int, int, list[str]]:
    from pypdf import PdfReader
    lector = PdfReader(io.BytesIO(datos))
    texto = "\n".join(p.extract_text() or "" for p in lector.pages)
    imagenes = sum(len(p.images) for p in lector.pages)
    enlaces = [a.get_object().get("/A", {}).get("/URI") for p in lector.pages for a in (p.get("/Annots") or [])]
    return texto, len(lector.pages), imagenes, [e for e in enlaces if e]


def exportar(banco: Banco, apunte_id: str, **opciones) -> tuple[dict, bytes | None]:
    r = banco.pedir("POST", f"/api/v2/apuntes/{apunte_id}/exportaciones", json=opciones)
    assert r.status_code in (200, 202), r.text
    if r.json().get("trabajo") is None:  # idempotente: ya había un PDF de esta versión con estas opciones
        t = {"estado": "completado"}
    else:
        t = banco.esperar(r.json()["trabajo"]["id"])
    if t["estado"] != "completado":
        return t, None
    return t, banco.pedir("GET", f"/api/v2/exportaciones/{r.json()['exportacion']['id']}/pdf").content


def documento(banco: Banco, apunte_id: str) -> dict:
    return banco.pedir("GET", f"/api/v2/apuntes/{apunte_id}").json()["apunte"]


def hoja_en_blanco():
    from herramientas.corpus import Muestra, _a_bgr, hoja_cuaderno
    return Muestra("hoja_en_blanco", "cuaderno", "vacia", _a_bgr(hoja_cuaderno()), [])


class WikipediaSimulada:
    """Respuestas grabadas con el formato de la API REST de Wikipedia (no hay red en la prueba)."""

    PAGINAS = {"Derivada": {"type": "standard", "title": "Derivada",
                            "extract": "La derivada de una función mide la rapidez con la que cambia su valor."}}

    def __init__(self, caida=False):
        self.caida = caida

    def __call__(self, peticion, timeout=None):
        if self.caida:
            raise urllib.error.URLError("sin conexión")
        partes = urllib.parse.urlsplit(peticion.full_url)
        if partes.path.endswith("/search/page"):
            q = urllib.parse.parse_qs(partes.query)["q"][0]
            return io.BytesIO(json.dumps({"pages": [{"key": k, "title": k} for k in self.PAGINAS if k.lower() == q.lower()]}).encode())
        clave = urllib.parse.unquote(partes.path.rsplit("/", 1)[1])
        if clave not in self.PAGINAS:
            raise urllib.error.HTTPError(peticion.full_url, 404, "no", {}, None)
        return io.BytesIO(json.dumps(self.PAGINAS[clave]).encode())


# ---------------------------------------------------------------- escenarios
class Aceptacion:
    def __init__(self):
        self.banco = Banco()
        self.escenarios: list[dict] = []
        self.rechazos: list[str] = []

    def escenario(self, id_, nombre, estado, resultado, comprobaciones: dict, rechazo: dict | None = None, nota=""):
        """`comprobaciones` deben cumplirse para el estado declarado; `rechazo` son criterios de parada."""
        fallos = [k for k, v in comprobaciones.items() if not v]
        for criterio, ok in (rechazo or {}).items():
            if not ok:
                self.rechazos.append(f"{id_} {nombre}: {criterio}")
        self.escenarios.append({"id": id_, "nombre": nombre, "estado": "fallido" if fallos else estado,
                                "resultado": resultado, "comprobaciones": comprobaciones, "fallos": fallos,
                                "rechazo": rechazo or {}, "nota": nota})

    def analizar(self, muestras, titulo):
        apunte, trabajo, ms = self.banco.analizar(muestras, titulo)
        return documento(self.banco, apunte["id"]), trabajo, ms

    def texto_y_errores(self, muestras, titulo):
        """Analiza, exporta y mide: CER, reconocidos con errores y PDF."""
        from herramientas.metricas import cer
        apunte, trabajo, ms = self.analizar(muestras, titulo)
        bloques = apunte["documento"]["bloques"]
        reconocido = "\n".join(b.get("texto") or "" for b in bloques)
        real = "\n".join(l for m in muestras for l in m.lineas)
        lineas_reales = {l.strip() for m in muestras for l in m.lineas}
        inventados = [b["texto"] for b in bloques if b["estado"] == "reconocido" and b.get("texto")
                      and not any(t.strip() in lineas_reales or t.strip() in real for t in b["texto"].splitlines())]
        t_pdf, pdf = exportar(self.banco, apunte["id"])
        texto, paginas, imagenes, enlaces = texto_pdf(pdf) if pdf else ("", 0, 0, [])
        return {"apunte": apunte, "trabajo": trabajo["estado"], "ms": round(ms), "cer": cer(reconocido, real) if real else 0.0,
                "inventados": inventados, "pdf": pdf, "pdf_estado": t_pdf["estado"], "pdf_codigo": (t_pdf.get("error") or {}).get("codigo"),
                "texto_pdf": texto, "paginas_pdf": paginas, "imagenes_pdf": imagenes, "enlaces": enlaces,
                "como_imagen": sum(1 for b in bloques if b.get("recorte") and not b.get("texto")),
                "inciertos": sum(b["estado"] == "incierto" for b in bloques)}

    def resumen(self, r):
        return (f"análisis {r['trabajo']} en {r['ms']} ms · CER {r['cer']:.1%} · {len(r['inventados'])} reconocidos sin estar en la foto · "
                f"{r['inciertos']} inciertos · {r['como_imagen']} como imagen · PDF {r['pdf_estado']} ({r['paginas_pdf']} pág., {r['imagenes_pdf']} imágenes)")

    def ejecutar(self):
        from herramientas import corpus as c
        b = self.banco

        # E1 pizarrón corto (foto inclinada de un pizarrón blanco)
        r = self.texto_y_errores([c.impreso_pizarron()], "E1 Pizarrón")
        self.escenario("E1", "Pizarrón corto", COMPLETO, self.resumen(r),
                       {"análisis completado": r["trabajo"] == "completado", "CER < 5 %": r["cer"] < 0.05,
                        "el texto llega al PDF": "La derivada mide la razón de cambio." in r["texto_pdf"]},
                       {"PDF no vacío": bool(r["pdf"]) and r["paginas_pdf"] > 0})

        # E2 cuaderno manuscrito (claro y difícil)
        for m, id_ in ((c.manuscrito_cuaderno(), "E2a"), (c.manuscrito_dificil(), "E2b")):
            r = self.texto_y_errores([m], f"{id_} Manuscrito")
            self.escenario(id_, f"Cuaderno manuscrito ({'claro' if id_ == 'E2a' else 'difícil'})",
                           PARCIAL, self.resumen(r),
                           {"análisis completado": r["trabajo"] == "completado", "PDF generado": bool(r["pdf"])},
                           {"no se presenta como seguro texto que no está en la foto": not r["inventados"]},
                           "Letra sintética de estilo manuscrito; con letra real de alumnos no se ha medido. "
                           "Lo dudoso queda marcado o como imagen para corregirlo a mano.")

        # E3 imagen difícil (poca luz, sombra, pizarrón verde de tiza)
        for m in (c.pizarron_con_ruido(), c.cuaderno_con_sombra(), c.pizarron_oscuro()):
            r = self.texto_y_errores([m], f"E3 {m.nombre}")
            self.escenario(f"E3-{m.nombre}", f"Imagen difícil: {m.nombre.replace('_', ' ')}", COMPLETO, self.resumen(r),
                           {"análisis completado": r["trabajo"] == "completado", "CER < 5 %": r["cer"] < 0.05},
                           {"PDF no vacío": bool(r["pdf"]) and "Derivadas" in r["texto_pdf"]})

        # E4 hoja impresa en cuaderno rayado y cuadriculado
        for m in (c.impreso_cuaderno(), c.cuaderno_cuadriculado()):
            r = self.texto_y_errores([m], f"E4 {m.nombre}")
            self.escenario(f"E4-{m.nombre}", f"Hoja impresa: {m.nombre.replace('_', ' ')}", COMPLETO, self.resumen(r),
                           {"CER < 5 %": r["cer"] < 0.05, "los renglones no se leen como texto": "____" not in r["texto_pdf"]},
                           {"PDF no vacío": bool(r["pdf"]) and r["paginas_pdf"] > 0})

        # E5 fórmulas: ninguna se pierde (LaTeX válido o imagen), ninguna falsa
        for m in (c.formulas_pizarron(), c.formulas_2d()):
            apunte, trabajo, _ = self.analizar([m], f"E5 {m.nombre}")
            bloques = apunte["documento"]["bloques"]
            latex = [x for x in bloques if x["tipo"] == "formula" and x.get("latex") and x.get("latex_valido")]
            exactas = sum(x["latex"] in m.latex for x in latex)
            sin_nada = [x for x in bloques if not x.get("texto") and not x.get("latex") and not x.get("recorte")]
            falsas = [x["latex"] for x in latex if x["estado"] == "reconocido" and x["latex"] not in m.latex]
            como_imagen = sum(1 for x in bloques if x.get("recorte") and not x.get("latex_valido"))
            _, pdf = exportar(b, apunte["id"])
            _, _, imagenes, _ = texto_pdf(pdf) if pdf else ("", 0, 0, [])
            self.escenario(f"E5-{m.nombre}", "Fórmulas en línea" if m.nombre == "formulas_pizarron" else "Fórmulas en dos dimensiones",
                           PARCIAL, f"{len(m.latex)} fórmulas: {exactas} con LaTeX exacto, {len(latex)} LaTeX válidos, "
                           f"{como_imagen} bloques conservados como imagen, {len(falsas)} falsas; PDF con {imagenes} imágenes",
                           {"PDF generado": bool(pdf)},
                           {"ninguna fórmula desaparece (sin texto, sin LaTeX y sin imagen)": not sin_nada,
                            "ninguna fórmula falsa marcada como reconocida": not falsas,
                            "las conservadas como imagen salen en el PDF": imagenes >= min(como_imagen, 1)},
                           "Las de dos pisos (fracciones apiladas, raíces largas) se conservan como imagen y se escriben en el editor.")

        # E6 tabla: el texto de las celdas se lee; la estructura se crea en el editor
        m, celdas = c.tabla_cuaderno(), c.CELDAS_TABLA
        apunte, trabajo, _ = self.analizar([m], "E6 Tabla")
        leido = "\n".join(x.get("texto") or "" for x in apunte["documento"]["bloques"])
        encontradas = sum(celda in leido for fila in celdas for celda in fila)
        doc = apunte["documento"]
        doc["bloques"].append({"id": "acept-tabla", "pagina": doc["paginas"][0]["id"], "orden": 999, "tipo": "tabla", "origen": "usuario",
                               "tabla": {"encabezados": celdas[0], "filas": celdas[1:]}})
        r = b.pedir("PUT", f"/api/v2/apuntes/{apunte['id']}/documento", json=doc, headers={"If-Match": str(apunte["version"])})
        _, pdf = exportar(b, apunte["id"])
        texto, *_ = texto_pdf(pdf) if pdf else ("",)
        self.escenario("E6", "Tabla fotografiada", PARCIAL,
                       f"{encontradas}/8 celdas leídas como texto; la tabla se crea en el editor (guardado {r.status_code}) y sale completa en el PDF",
                       {"análisis completado": trabajo["estado"] == "completado", "guardado del editor": r.status_code == 200,
                        "el título de fuera de la tabla no se pierde": "Unidades del SI" in leido,
                        "se leen al menos 6 de las 8 celdas": encontradas >= 6,
                        "tabla completa en el PDF": all(celda in texto for fila in celdas for celda in fila)},
                       {"PDF no vacío": bool(pdf)},
                       "El análisis lee las celdas como texto, fila a fila, pero no reconstruye la tabla: la estructura la hace el usuario en el editor.")

        # E7 diagrama: se conserva como imagen, sin inventar texto
        r = self.texto_y_errores([c.diagrama()], "E7 Diagrama")
        self.escenario("E7", "Diagrama", COMPLETO, self.resumen(r),
                       {"el dibujo se conserva como imagen": r["como_imagen"] >= 1, "el título se lee": "Ciclo del agua" in r["texto_pdf"],
                        "la imagen sale en el PDF": r["imagenes_pdf"] >= 1},
                       {"no se inventa texto a partir del dibujo": not r["inventados"]},
                       "El dibujo no se interpreta (no hay descripción automática): se conserva tal cual.")

        # E8 varias páginas: orden respetado en el apunte y en el PDF
        paginas = [c.impreso_cuaderno(), c.diagrama(), c.formulas_pizarron()]
        r = self.texto_y_errores(paginas, "E8 Varias páginas")
        orden_bloques = [x["pagina"] for x in r["apunte"]["documento"]["bloques"]]
        t = r["texto_pdf"]
        self.escenario("E8", "Varias páginas (3)", COMPLETO, self.resumen(r),
                       {"bloques en el orden de las fotos": orden_bloques == sorted(orden_bloques, key=lambda p: int(p[1:])),
                        "orden en el PDF": 0 <= t.find("razón de cambio") < t.find("Ciclo del agua")},
                       {"PDF no vacío": bool(r["pdf"]) and r["paginas_pdf"] > 1})
        varias = r["apunte"]

        # E9 sin investigación: el PDF no trae nada de fuera
        _, pdf = exportar(b, varias["id"])
        texto, _, _, enlaces = texto_pdf(pdf)
        self.escenario("E9", "Recorrido sin información complementaria", COMPLETO,
                       f"PDF de {len(texto)} caracteres sin sección de complementos ni enlaces externos",
                       {"sin enlaces externos": not any("wikipedia" in e for e in enlaces)},
                       {"sin citas que no se pidieron": "wikipedia" not in texto.lower()})

        # E10 con investigación (Wikipedia SIMULADA): solo lo aceptado, con su fuente
        from app.services import investigacion
        investigacion.usar_proveedor(investigacion.ProveedorWikipedia(abrir=WikipediaSimulada()))
        try:
            sin_permiso = b.pedir("POST", f"/api/v2/apuntes/{varias['id']}/investigacion", json={"consentimiento": True, "conceptos": ["Derivada"]})
            b.pedir("PATCH", "/api/v2/perfil", json={"preferencias": {"investigacion_permitida": True}})
            r = b.pedir("POST", f"/api/v2/apuntes/{varias['id']}/investigacion", json={"consentimiento": True, "conceptos": ["Derivada", "Concepto inexistente"]})
            t = b.esperar(r.json()["trabajo"]["id"])
            doc = documento(b, varias["id"])
            propuestas = doc["documento"]["ampliaciones"]
            _, pdf_sin_aceptar = exportar(b, varias["id"])
            texto_sin, *_ = texto_pdf(pdf_sin_aceptar)
            for a in propuestas:
                doc = b.pedir("PATCH", f"/api/v2/apuntes/{varias['id']}/ampliaciones/{a['id']}", json={"estado": "aceptada"},
                              headers={"If-Match": str(doc["version"])}).json()["apunte"]
            _, pdf = exportar(b, varias["id"])
            texto, _, _, enlaces = texto_pdf(pdf)
            fuentes_ok = all(a["fuente"]["url"].startswith("https://es.wikipedia.org/") and a["fuente"]["licencia"] for a in propuestas)
            self.escenario("E10", "Recorrido con información complementaria (Wikipedia simulada)", COMPLETO,
                           f"sin permiso → {sin_permiso.status_code}; trabajo {t['estado']}; {len(propuestas)} propuesta(s) "
                           f"para 2 conceptos; tras aceptarlas, el PDF enlaza {sorted(set(e for e in enlaces if 'wikipedia' in e))}",
                           {"exige el permiso del perfil": sin_permiso.status_code == 400,
                            "el concepto sin página no produce nada": len(propuestas) == 1,
                            "lo propuesto no entra al PDF hasta aceptarlo": "rapidez con la que cambia" not in texto_sin,
                            "lo aceptado entra con su texto": "rapidez con la que cambia" in texto},
                           {"cada complemento lleva fuente real y licencia (sin citas inventadas)": fuentes_ok and bool(propuestas),
                            "el enlace de la fuente está en el PDF": "https://es.wikipedia.org/wiki/Derivada" in enlaces},
                           "Fuente simulada con el formato real de la API: la consulta a Wikipedia real se comprueba a mano (docs/aceptacion.md).")

            # E11 sin conexión: error claro, el apunte sigue igual y no se inventa nada
            investigacion.usar_proveedor(investigacion.ProveedorWikipedia(abrir=WikipediaSimulada(caida=True)))
            antes = documento(b, varias["id"])
            r = b.pedir("POST", f"/api/v2/apuntes/{varias['id']}/investigacion", json={"consentimiento": True, "conceptos": ["Derivada"]})
            t = b.esperar(r.json()["trabajo"]["id"])
            despues = documento(b, varias["id"])
            investigacion.usar_proveedor(investigacion.ProveedorNinguno())
            ninguno = b.pedir("POST", f"/api/v2/apuntes/{varias['id']}/investigacion", json={"consentimiento": True, "conceptos": ["Derivada"]})
            self.escenario("E11", "Sin conexión o sin proveedor (demo sin Internet)", COMPLETO,
                           f"fuente caída → trabajo {t['estado']} ({(t.get('error') or {}).get('codigo')}); sin proveedor → "
                           f"{ninguno.status_code} {ninguno.json().get('error', {}).get('codigo')}",
                           {"el fallo se informa": t["estado"] == "fallido" and ninguno.status_code == 503},
                           {"no aparece información nueva sin fuente": despues["documento"]["ampliaciones"] == antes["documento"]["ampliaciones"]})
        finally:
            investigacion.usar_proveedor(None)

        # R1 PDF vacío: un apunte sin texto NO genera un PDF vacío
        apunte, trabajo, _ = self.analizar([hoja_en_blanco()], "R1 Hoja en blanco")
        t, pdf = exportar(b, apunte["id"])
        self.escenario("R1", "Hoja en blanco: no se genera un PDF vacío", COMPLETO,
                       f"análisis {trabajo['estado']}, {len(apunte['documento']['bloques'])} bloques; exportación {t['estado']} "
                       f"({(t.get('error') or {}).get('codigo')})", {},
                       {"no se entrega un PDF vacío": pdf is None and (t.get("error") or {}).get("codigo") == "APUNTE_VACIO"})

        # R4 apuntes ajenos: otra cuenta no puede ver, editar, exportar ni borrar
        from fastapi.testclient import TestClient
        from app.main import app
        otra = TestClient(app)
        csrf = otra.post("/api/v2/auth/registro", json={"email": "ajena@example.com", "nombre": "Otra", "password": clave_de_prueba("c11")}).json()["csrf"]
        h = {"X-CSRF-Token": csrf}
        intentos = {
            "ver": otra.get(f"/api/v2/apuntes/{varias['id']}").status_code,
            "versiones": otra.get(f"/api/v2/apuntes/{varias['id']}/versiones").status_code,
            "editar": otra.put(f"/api/v2/apuntes/{varias['id']}/documento", json={}, headers={**h, "If-Match": "1"}).status_code,
            "exportar": otra.post(f"/api/v2/apuntes/{varias['id']}/exportaciones", json={}, headers=h).status_code,
            "borrar": otra.delete(f"/api/v2/apuntes/{varias['id']}", headers=h).status_code,
            "listar": len(otra.get("/api/v2/apuntes").json()["elementos"]),
        }
        sigue = b.pedir("GET", f"/api/v2/apuntes/{varias['id']}").status_code
        self.escenario("R4", "Otra cuenta intenta usar el apunte", COMPLETO,
                       ", ".join(f"{k} → {v}" for k, v in intentos.items()) + f"; el dueño lo sigue viendo ({sigue})", {},
                       {"todo lo ajeno responde 404 y no aparece en su lista":
                        all(v == 404 for k, v in intentos.items() if k != "listar") and intentos["listar"] == 0 and sigue == 200})

    def informe(self, carpeta: Path) -> Path:
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "aceptacion.json").write_text(json.dumps({"escenarios": self.escenarios, "rechazos": self.rechazos},
                                                            ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        filas = ["| Id | Escenario | Estado | Resultado medido |", "|---|---|---|---|"]
        for e in self.escenarios:
            icono = {"completo": "✅ completo", "parcial": "⚠️ parcial", "fallido": "❌ fallido"}[e["estado"]]
            filas.append(f"| {e['id']} | {e['nombre']} | {icono} | {e['resultado']}{(' — ' + e['nota']) if e['nota'] else ''} |")
        criterios = [f"- {'✅' if ok else '❌'} {e['id']}: {k}" for e in self.escenarios for k, ok in e["rechazo"].items()]
        md = (f"# Aceptación ({datetime.now():%Y-%m-%d %H:%M})\n\n" + "\n".join(filas) + "\n\n## Criterios de rechazo\n\n"
              + "\n".join(criterios) + f"\n\n**Resultado:** {'RECHAZADA' if self.rechazos else 'sin criterios de rechazo'}.\n")
        (carpeta / "aceptacion.md").write_text(md, encoding="utf-8")
        return carpeta / "aceptacion.md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--salida", type=Path, default=RAIZ / "fullstack" / "evaluacion" / "resultados")
    args = parser.parse_args()
    logging.disable(logging.WARNING)  # el informe es la salida; los registros del servidor sobran aquí
    inicio = time.perf_counter()
    a = Aceptacion()
    try:
        a.ejecutar()
    finally:
        a.banco.cerrar()
    ruta = a.informe(args.salida / datetime.now().strftime("%Y-%m-%d_%H%M%S"))
    print(ruta.read_text(encoding="utf-8"))
    fallidos = [e["id"] for e in a.escenarios if e["estado"] == "fallido"]
    print(f"{len(a.escenarios)} escenarios en {time.perf_counter() - inicio:.1f} s · fallidos: {fallidos or 'ninguno'} · "
          f"criterios de rechazo cumplidos: {len(a.rechazos)}")
    return 1 if a.rechazos or fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
