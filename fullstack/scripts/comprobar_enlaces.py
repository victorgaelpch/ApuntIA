"""Comprueba que los enlaces internos de la documentación existen (FULL-14).

    python fullstack/scripts/comprobar_enlaces.py

Revisa los enlaces relativos [texto](ruta) y [texto](ruta#ancla) de todos los .md del
repositorio (no los externos http/https/mailto). Las anclas se comparan con los títulos del
documento destino según las reglas de GitHub. Sale con 1 si alguno no existe.
"""

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ENLACE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def ancla(titulo: str) -> str:
    """Ancla de un título al estilo de GitHub."""
    t = re.sub(r"[`*_]", "", titulo.strip().lower())
    t = "".join(c for c in t if c.isalnum() or c in " -" or unicodedata.category(c).startswith("L"))
    return t.replace(" ", "-")


def anclas(ruta: Path) -> set[str]:
    return {ancla(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*$", ruta.read_text(encoding="utf-8"), re.M)}


def main() -> int:
    archivos = subprocess.run(["git", "ls-files", "*.md"], cwd=RAIZ, capture_output=True, text=True).stdout.split()
    rotos, total = [], 0
    for rel in archivos:
        origen = RAIZ / rel
        texto = re.sub(r"```.*?```", "", origen.read_text(encoding="utf-8"), flags=re.S)  # sin bloques de código
        for m in ENLACE.finditer(texto):
            destino = m.group(1)
            if re.match(r"^[a-z]+:", destino) or destino.startswith("#") and not destino[1:]:
                continue
            total += 1
            ruta, _, fragmento = destino.partition("#")
            objetivo = (origen.parent / ruta).resolve() if ruta else origen
            if not objetivo.exists():
                rotos.append(f"{rel}: {destino} (no existe)")
            elif fragmento and objetivo.suffix == ".md" and fragmento not in anclas(objetivo):
                rotos.append(f"{rel}: {destino} (no hay ese apartado)")
    if rotos:
        print("Enlaces rotos en la documentación:")
        print("\n".join(f"  - {r}" for r in rotos))
        return 1
    print(f"{total} enlaces internos en {len(archivos)} documentos: todos existen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
