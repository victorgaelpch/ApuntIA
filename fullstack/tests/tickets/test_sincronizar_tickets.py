"""Pruebas del sincronizador de tickets (FULL-29). Sin red: la API de GitHub se simula.

    python -m unittest discover -s fullstack/tests/tickets
"""

import importlib.util
import json
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("sincronizar_tickets", RAIZ / "fullstack/scripts/sincronizar_tickets.py")
st = importlib.util.module_from_spec(_spec)
sys.modules["sincronizar_tickets"] = st  # dataclasses lo necesita
_spec.loader.exec_module(st)

URL = "https://api.github.com/repos/o/r/issues?state=all&per_page=100&sort=created&direction=asc"
PAG2 = "https://api.github.com/repos/o/r/issues?state=all&per_page=100&page=2"


def issue(numero, titulo, estado="open", cerrado=None, etiquetas=(), responsables=(), cuerpo="", pr=None):
    datos = {
        "number": numero, "title": titulo, "html_url": f"https://github.com/o/r/issues/{numero}",
        "state": estado, "state_reason": "completed" if estado == "closed" else None,
        "labels": [{"name": e} for e in etiquetas], "assignees": [{"login": r} for r in responsables],
        "user": {"login": "autor"}, "body": cuerpo,
        "created_at": "2026-11-14T00:33:10Z", "updated_at": "2026-11-14T01:00:00Z", "closed_at": cerrado,
    }
    if pr is not None:
        datos["pull_request"] = {"merged_at": pr or None}  # pr="" → PR sin fusionar
        datos["html_url"] = f"https://github.com/o/r/pull/{numero}"
    return datos


CUERPO_29 = """## Dependencias
Ninguna. Es base para todos los demás Issues.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-11-13 · 18:00–20:00 (America/Mexico_City): Auditoría de rutas.
- [ ] 2026-11-14 · 10:00–12:30 (America/Mexico_City): Migración controlada.
"""

PAGINA1 = [
    issue(93, "[FULL-29] Reorganizar documentación", etiquetas=["fullstack"], responsables=["victor"], cuerpo=CUERPO_29),
    issue(2, "[BACK-01] Revisar backend", estado="closed", cerrado="2026-10-27T03:00:00Z", etiquetas=["backend"]),
    issue(91, "[FULLSTACK][IA] Motor multimodal", estado="closed", cerrado="2026-11-10T20:00:00Z"),  # sin ID ni etiqueta
]
PAGINA2 = [
    issue(92, "[FULL-30] IA multimodal (1/8)", estado="closed", cerrado="2026-11-10T20:00:00Z", pr="",
          cuerpo="Closes #91"),
    issue(94, "[FULL-30] Instalador", etiquetas=["fullstack"]),
    issue(120, "[FULL-29] Duplicado por error", etiquetas=["fullstack"]),
    issue(121, "[BACK-28] Algo", estado="closed", cerrado="2026-11-11T00:00:00Z"),
    issue(122, "fix: PR que cierra", estado="closed", cerrado="2026-11-12T00:00:00Z",
          pr="2026-11-12T00:00:00Z", cuerpo="Closes #121"),
]


class Falso:
    """Transporte HTTP simulado: lista de respuestas por URL; registra las peticiones."""

    def __init__(self, respuestas):
        self.respuestas = {k: list(v) for k, v in respuestas.items()}
        self.peticiones = []

    def __call__(self, url, cabeceras):
        self.peticiones.append((url, dict(cabeceras)))
        r = self.respuestas[url].pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def ok(datos, siguiente=None):
    cab = {"link": f'<{siguiente}>; rel="next", <x>; rel="last"'} if siguiente else {}
    return 200, cab, json.dumps(datos).encode()


def api_normal():
    return Falso({URL: [ok(PAGINA1, PAG2)], PAG2: [ok(PAGINA2)]})


AHORA = lambda: datetime(2026, 11, 14, 3, 40, tzinfo=timezone.utc)  # noqa: E731


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name) / "tickets"
        self.mensajes = []

    def tearDown(self):
        self._tmp.cleanup()

    def sync(self, transporte, **kw):
        return st.sincronizar(self.dir, "o/r", transporte, ahora=AHORA, salida=self.mensajes.append,
                              espera=lambda s: None, **kw)

    def leer(self, nombre):
        return (self.dir / nombre).read_text(encoding="utf-8")

    def instantanea(self):
        return {p.relative_to(self.dir).as_posix(): p.read_bytes() for p in sorted(self.dir.rglob("*")) if p.is_file()}


class Sincronizacion(Base):
    def test_pagina_y_separa_issues_de_prs(self):
        t = api_normal()
        self.assertEqual(self.sync(t), 0)
        self.assertEqual([u for u, _ in t.peticiones], [URL, PAG2])
        fichas = sorted(p.name for p in self.dir.glob("*.md") if p.name != "INDICE.md")
        # 92 y 122 son PRs (clave pull_request): no tienen ficha.
        self.assertEqual(fichas, ["BACK-01.md", "BACK-28.md", "FULL-29-issue-120.md", "FULL-29.md", "FULL-30.md", "issue-91.md"])
        indice = self.leer("INDICE.md")
        self.assertIn("[#122](https://github.com/o/r/pull/122)", indice)
        self.assertIn("[#92](https://github.com/o/r/pull/92) | [FULL-30] IA multimodal (1/8) | Cerrado sin fusionar | #91 |", indice)
        self.assertIn("6 Issues (3 abiertos, 3 cerrados) y 2 Pull Requests", indice)
        self.assertIn("[PR #92](https://github.com/o/r/pull/92) usa el prefijo `[FULL-30]`", indice)

    def test_ficha_con_campos_y_fechas_en_cdmx(self):
        self.sync(api_normal())
        f = self.leer("FULL-29.md")
        self.assertIn("| Número en GitHub | [#93](https://github.com/o/r/issues/93) |", f)
        self.assertIn("| Responsable(s) | victor |", f)
        self.assertIn("| Estado | Abierto |", f)
        self.assertIn("2026-11-14 00:33:10 UTC · 2026-11-13 18:33 (CDMX)", f)  # UTC−6
        self.assertIn("| `closed_at` | — (abierto) |", f)
        self.assertIn("| Dependencias | Ninguna. Es base para todos los demás Issues. |", f)
        self.assertIn("| 2026-11-13 | 18:00–20:00 | Auditoría de rutas. |", f)
        self.assertIn("## REGISTRO REAL\n\nno registrada", f)
        cerrado = self.leer("BACK-01.md")
        self.assertIn("Cerrado (completado)", cerrado)
        self.assertIn("2026-10-26 21:00 (CDMX)", cerrado)

    def test_sin_etiqueta_ni_identificador(self):
        self.sync(api_normal())
        f = self.leer("issue-91.md")
        self.assertIn("| Identificador lógico | sin identificador lógico |", f)
        self.assertIn("| Etiquetas | sin etiqueta |", f)
        self.assertIn("sin área", f)

    def test_colision_no_sobrescribe_y_se_registra(self):
        self.sync(api_normal())
        self.assertIn("[#93]", self.leer("FULL-29.md"))
        self.assertIn("[#120]", self.leer("FULL-29-issue-120.md"))
        self.assertIn("`FULL-29` lo usan los Issues #93, #120", self.leer("INDICE.md"))

    def test_el_dueno_previo_conserva_su_archivo(self):
        # Si #120 ya era dueño de FULL-29.md (p. ej. #93 apareció después), no se le quita el archivo.
        self.dir.mkdir(parents=True)
        (self.dir / "FULL-29.md").write_text("| Número en GitHub | [#120](u) |\n", encoding="utf-8")
        self.sync(api_normal())
        self.assertIn("[#120]", self.leer("FULL-29.md"))
        self.assertIn("[#93]", self.leer("FULL-29-issue-93.md"))

    def test_evidencia_de_pr_que_cierra(self):
        self.sync(api_normal())
        self.assertIn("[PR #122](https://github.com/o/r/pull/122) (fusionado 2026-11-11 18:00)", self.leer("BACK-28.md"))
        self.assertIn("ningún PR declara «Closes #93»", self.leer("FULL-29.md"))
        self.assertIn("[PR #92](https://github.com/o/r/pull/92) (sin fusionar)", self.leer("issue-91.md"))

    def test_idempotente(self):
        self.sync(api_normal())
        antes = self.instantanea()
        self.sync(api_normal())
        self.assertEqual(self.instantanea(), antes)
        self.assertIn("0 archivo(s) actualizado(s)", self.mensajes[-1])

    def test_conserva_notas_manuales_y_bitacora(self):
        self.sync(api_normal())
        ficha = self.dir / "FULL-29.md"
        ficha.write_text(ficha.read_text(encoding="utf-8") + "- Decisión humana importante.\n", encoding="utf-8")
        (self.dir / "bitacora").mkdir()
        bit = self.dir / "bitacora" / "FULL-29.md"
        texto_bit = "# Bitácora\n\n- Sesión real: 2026-11-13 21:27–22:40 (America/Mexico_City). Responsable: x.\n"
        bit.write_text(texto_bit, encoding="utf-8")
        self.sync(api_normal())
        f = self.leer("FULL-29.md")
        self.assertIn("- Decisión humana importante.", f)
        self.assertIn("1 sesión(es) real(es) registrada(s)", f)
        self.assertEqual(bit.read_text(encoding="utf-8"), texto_bit)

    def test_ficha_manual_sin_marcas_no_se_pierde(self):
        self.dir.mkdir(parents=True)
        (self.dir / "issue-91.md").write_text("Apuntes a mano\n", encoding="utf-8")
        self.sync(api_normal())
        self.assertIn("## Contenido manual anterior\n\nApuntes a mano", self.leer("issue-91.md"))

    def test_identificador_planificado_sin_issue(self):
        self.dir.mkdir(parents=True)
        (self.dir / "cronograma-planeado.md").write_text("| ID |\n|----|\n| BACK-35 | x |\n| FULL-29 | y |\n", encoding="utf-8")
        self.sync(api_normal())
        indice = self.leer("INDICE.md")
        self.assertIn("`BACK-35`: está en el [cronograma planificado]", indice)
        self.assertNotIn("`FULL-29`: está en el", indice)

    def test_token_solo_en_cabecera_y_nunca_en_archivos(self):
        t = api_normal()
        self.sync(t, token="tok-secreto-123")
        self.assertEqual(t.peticiones[0][1]["Authorization"], "Bearer tok-secreto-123")
        for contenido in self.instantanea().values():
            self.assertNotIn(b"tok-secreto-123", contenido)
        self.assertFalse(any("tok-secreto" in m for m in self.mensajes))


class Fallos(Base):
    def preparar_snapshot(self):
        self.assertEqual(self.sync(api_normal()), 0)
        return self.instantanea()

    def test_red_caida_usa_snapshot(self):
        antes = self.preparar_snapshot()
        codigo = self.sync(Falso({URL: [urllib.error.URLError("sin DNS")]}))
        self.assertEqual(codigo, 3)
        self.assertIn("sin conexión con api.github.com", self.mensajes[-2])
        self.assertEqual(self.instantanea(), antes)

    def test_red_caida_sin_snapshot_no_inventa(self):
        self.assertEqual(self.sync(Falso({URL: [urllib.error.URLError("x")]})), 2)
        self.assertFalse((self.dir / "INDICE.md").exists())

    def test_403_por_limite_usa_snapshot(self):
        self.preparar_snapshot()
        r = (403, {"x-ratelimit-remaining": "0"}, b"{}")
        self.assertEqual(self.sync(Falso({URL: [r]})), 3)
        self.assertIn("límite de peticiones", self.mensajes[-2])

    def test_429_con_espera_corta_reintenta_una_vez(self):
        esperas = []
        t = Falso({URL: [(429, {"retry-after": "2"}, b""), ok(PAGINA1)]})
        codigo = st.sincronizar(self.dir, "o/r", t, ahora=AHORA, salida=self.mensajes.append, espera=esperas.append)
        self.assertEqual((codigo, esperas), (0, [2.0]))

    def test_429_repetido_no_insiste(self):
        self.preparar_snapshot()
        t = Falso({URL: [(429, {"retry-after": "2"}, b""), (429, {"retry-after": "2"}, b"")]})
        self.assertEqual(self.sync(t), 3)
        self.assertEqual(len(t.peticiones), 2)

    def test_json_invalido_y_5xx(self):
        self.preparar_snapshot()
        self.assertEqual(self.sync(Falso({URL: [(200, {}, b"<html>")]})), 3)
        self.assertIn("no es JSON", self.mensajes[-2])
        self.assertEqual(self.sync(Falso({URL: [(502, {}, b"")]})), 3)
        self.assertIn("HTTP 502", self.mensajes[-2])

    def test_offline(self):
        antes = self.preparar_snapshot()
        self.assertEqual(self.sync(None), 0)
        self.assertEqual(self.instantanea(), antes)

    def test_offline_sin_snapshot(self):
        self.assertEqual(self.sync(None), 2)

    def test_paginacion_infinita_se_corta(self):
        bucle = Falso({URL: [ok([], URL) for _ in range(60)]})
        with self.assertRaises(st.FalloAPI):
            st.descargar("o/r", bucle, max_paginas=5)


class Utilidades(unittest.TestCase):
    def test_id_logico(self):
        self.assertEqual(st.id_logico("[FULL-29] x"), "FULL-29")
        self.assertEqual(st.id_logico("[back-01] x"), "BACK-01")
        self.assertIsNone(st.id_logico("[FULLSTACK][IA] x"))
        self.assertIsNone(st.id_logico("Arreglo [FULL-29]"))

    def test_siguiente(self):
        self.assertEqual(st.siguiente('<https://a/2>; rel="next", <https://a/5>; rel="last"'), "https://a/2")
        self.assertIsNone(st.siguiente('<https://a/1>; rel="prev"'))
        self.assertIsNone(st.siguiente(None))

    def test_cdmx(self):
        self.assertEqual(st.a_cdmx("2026-11-14T00:33:10Z"), "2026-11-13 18:33")
        self.assertEqual(st.a_cdmx(None), "—")

    def test_repo_invalido(self):
        self.assertEqual(st.main(["--repo", "https://evil/x", "--offline"]), 1)


if __name__ == "__main__":
    unittest.main()
