"""Pruebas del comprobador de enlaces de la documentación (FULL-14, FULL-29).

    python -m unittest discover -s fullstack/tests/docs
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("comprobar_enlaces", RAIZ / "fullstack/scripts/comprobar_enlaces.py")
ce = importlib.util.module_from_spec(_spec)
sys.modules["comprobar_enlaces"] = ce
_spec.loader.exec_module(ce)


class Comprobador(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.raiz, check=True)
        self.escribir("README.md", "# Inicio\n\n[docs](fullstack/docs/README.md)\n")
        self.escribir("fullstack/docs/README.md", "# Índice\n\n## Sección uno\n\n[api](api.md) · [ancla](#sección-uno)\n")
        self.escribir("fullstack/docs/api.md", "# API\n\n![captura](evidencias/a.jpg)\n")
        (self.raiz / "fullstack/docs/evidencias").mkdir()
        (self.raiz / "fullstack/docs/evidencias/a.jpg").write_bytes(b"jpg")

    def tearDown(self):
        self._tmp.cleanup()

    def escribir(self, rel, texto):
        ruta = self.raiz / rel
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8")

    def problemas(self):
        return ce.revisar(self.raiz, ce.archivos_md(self.raiz))[0]

    def test_todo_correcto(self):
        self.assertEqual(self.problemas(), [])
        self.assertEqual(ce.main(self.raiz), 0)

    def test_enlace_roto(self):
        self.escribir("fullstack/docs/api.md", "# API\n\n[viejo](../../docs/api.md)\n![captura](evidencias/a.jpg)\n")
        self.assertEqual(self.problemas(), ["fullstack/docs/api.md: ../../docs/api.md (enlace: no existe)"])
        self.assertEqual(ce.main(self.raiz), 1)

    def test_imagen_rota(self):
        self.escribir("fullstack/docs/api.md", "# API\n\n![captura](evidencias/b.jpg)\n")
        self.assertEqual(self.problemas(), ["fullstack/docs/api.md: evidencias/b.jpg (imagen: no existe)"])

    def test_ancla_inexistente(self):
        self.escribir("README.md", "# Inicio\n\n[docs](fullstack/docs/README.md#no-existe)\n")
        self.assertEqual(self.problemas(), ["README.md: fullstack/docs/README.md#no-existe (no hay ese apartado)"])

    def test_documento_huerfano(self):
        self.escribir("front/docs/suelto.md", "# Nadie me enlaza\n")
        self.escribir("fullstack/tickets/FULL-1.md", "# Ficha\n")
        self.assertEqual(self.problemas(), [
            "front/docs/suelto.md: documento huérfano (ningún enlace lo alcanza desde README.md)",
            "fullstack/tickets/FULL-1.md: documento huérfano (ningún enlace lo alcanza desde README.md)",
        ])

    def test_huerfano_fuera_de_las_carpetas_vigiladas_no_falla(self):
        self.escribir("back/NOTAS.md", "# Notas internas\n")
        self.assertEqual(self.problemas(), [])

    def test_ignora_ejemplos_en_codigo(self):
        self.escribir("fullstack/docs/api.md", "# API\n\nSe escribe `[texto](ruta)`.\n\n```\n[x](no-existe.md)\n```\n")
        self.assertEqual(self.problemas(), [])

    def test_ignora_enlaces_externos(self):
        self.escribir("fullstack/docs/api.md", "# API\n\n[gh](https://github.com) [m](mailto:a@b.c)\n")
        self.assertEqual(self.problemas(), [])


if __name__ == "__main__":
    unittest.main()
