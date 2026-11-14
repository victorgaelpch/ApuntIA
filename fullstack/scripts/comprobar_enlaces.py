"""Comprueba que los enlaces internos de la documentación existen (FULL-14, ampliado en FULL-29).

    python fullstack/scripts/comprobar_enlaces.py

Revisa, en todos los .md versionados del repositorio (no los externos http/https/mailto):

- los enlaces relativos [texto](ruta) y [texto](ruta#ancla), y las imágenes ![alt](ruta);
- que cada #ancla corresponda a un título del documento destino (reglas de GitHub);
- que ningún documento de fullstack/docs/, front/docs/ ni fullstack/tickets/ quede huérfano:
  todos deben poder alcanzarse siguiendo enlaces desde el README.md raíz.

Sale con 1 y lista cada ruta rota si algo falla. Ver fullstack/docs/ESTRUCTURA_DOCUMENTAL.md.
"""

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ENLACE = re.compile(r"(!?)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# Carpetas cuya documentación debe ser alcanzable desde el README raíz.
DEBEN_SER_ALCANZABLES = ("fullstack/docs/", "front/docs/", "fullstack/tickets/")


def ancla(titulo: str) -> str:
    """Ancla de un título al estilo de GitHub."""
    t = re.sub(r"[`*_]", "", titulo.strip().lower())
    t = "".join(c for c in t if c.isalnum() or c in " -" or unicodedata.category(c).startswith("L"))
    return t.replace(" ", "-")


def anclas(ruta: Path) -> set[str]:
    return {ancla(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*$", ruta.read_text(encoding="utf-8"), re.M)}


def archivos_md(raiz: Path) -> list[str]:
    salida = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
                            cwd=raiz, capture_output=True, text=True).stdout
    return sorted(set(salida.split()))


def revisar(raiz: Path, archivos: list[str]) -> tuple[list[str], int]:
    """Devuelve (problemas, enlaces revisados)."""
    rotos, total = [], 0
    grafo: dict[str, set[str]] = {}
    for rel in archivos:
        origen = raiz / rel
        texto = re.sub(r"```.*?```", "", origen.read_text(encoding="utf-8"), flags=re.S)  # sin bloques de código
        texto = re.sub(r"`[^`\n]*`", "", texto)  # ni código en línea: `[texto](ruta)` es un ejemplo
        grafo[rel] = set()
        for m in ENLACE.finditer(texto):
            imagen, destino = m.group(1) == "!", m.group(2)
            if re.match(r"^[a-z]+:", destino) or destino.startswith("#") and not destino[1:]:
                continue
            total += 1
            ruta, _, fragmento = destino.partition("#")
            objetivo = (origen.parent / ruta).resolve() if ruta else origen
            tipo = "imagen" if imagen else "enlace"
            if not objetivo.exists():
                rotos.append(f"{rel}: {destino} ({tipo}: no existe)")
                continue
            if fragmento and objetivo.suffix == ".md" and fragmento not in anclas(objetivo):
                rotos.append(f"{rel}: {destino} (no hay ese apartado)")
            if objetivo.suffix == ".md":
                try:
                    grafo[rel].add(objetivo.relative_to(raiz.resolve()).as_posix())
                except ValueError:
                    pass
    # Documentos huérfanos: no alcanzables desde README.md.
    alcanzados, pendientes = set(), ["README.md"] if "README.md" in grafo else []
    while pendientes:
        actual = pendientes.pop()
        if actual in alcanzados:
            continue
        alcanzados.add(actual)
        pendientes.extend(grafo.get(actual, ()))
    for rel in archivos:
        if rel.startswith(DEBEN_SER_ALCANZABLES) and rel not in alcanzados:
            rotos.append(f"{rel}: documento huérfano (ningún enlace lo alcanza desde README.md)")
    return rotos, total


def main(raiz: Path = RAIZ) -> int:
    archivos = archivos_md(raiz)
    rotos, total = revisar(raiz, archivos)
    if rotos:
        print("Enlaces rotos en la documentación:")
        print("\n".join(f"  - {r}" for r in rotos))
        return 1
    print(f"{total} enlaces internos en {len(archivos)} documentos: todos existen y todos los documentos son alcanzables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
