"""Busca secretos en el repositorio y en TODO su historial de Git (FULL-20).

    python fullstack/scripts/buscar_secretos.py

Patrones: claves privadas, tokens de GitHub/Slack/AWS/OpenAI/Anthropic, URL con credenciales,
asignaciones de password/secret/token con valores largos y archivos que no deben subirse
(.env, bases de datos, copias). Ignora los valores de ejemplo y de prueba conocidos.
Sale con 1 si encuentra algo.
"""

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PATRONES = {
    "clave privada": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----"),
    "token de GitHub": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "token de Slack": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    "clave de AWS": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "clave de API (sk-)": re.compile(r"\bsk-(ant-)?[A-Za-z0-9_-]{30,}\b"),
    "URL con credenciales": re.compile(r"\b[a-z]+://[^/\s:@]+:[^/\s:@]{6,}@[^\s]+"),
    "asignación de secreto": re.compile(r"(?i)\b(secret|api_?key|token|passwd|password)\s*[:=]\s*['\"][A-Za-z0-9_\-+/]{16,}['\"]"),
}
PERMITIDOS = re.compile(r"(?i)example|ejemplo|prueba|test|contraseña-|frase|apuntia|xxxx|\*\*\*|<|\$\{")
ARCHIVOS_PROHIBIDOS = re.compile(r"(^|/)(\.env|.*\.sqlite3|.*\.db|.*\.pem|.*\.key|id_rsa.*|respaldos/.*|.*\.tar\.gz)$")


def main() -> int:
    hallazgos = []
    historial = subprocess.run(["git", "log", "--all", "-p", "--no-color", "--pretty=format:@@commit %h"],
                               cwd=RAIZ, capture_output=True, text=True, errors="replace").stdout
    commit = "?"
    for linea in historial.splitlines():
        if linea.startswith("@@commit "):
            commit = linea.split()[1]
            continue
        if not linea.startswith("+") or linea.startswith("+++"):
            continue
        for nombre, patron in PATRONES.items():
            m = patron.search(linea)
            if m and not PERMITIDOS.search(m.group(0)):
                hallazgos.append(f"{commit}: {nombre}: {m.group(0)[:12]}…")
    nombres = subprocess.run(["git", "log", "--all", "--name-only", "--pretty=format:"], cwd=RAIZ,
                             capture_output=True, text=True).stdout.splitlines()
    for n in sorted(set(nombres)):
        if n and ARCHIVOS_PROHIBIDOS.search(n) and not n.endswith(".env.example"):
            hallazgos.append(f"archivo que no debe estar en Git: {n}")
    if hallazgos:
        print("Posibles secretos o archivos privados en el repositorio:")
        print("\n".join(f"  - {h}" for h in hallazgos))
        print("Si alguno es real: rótalo YA (cámbialo en el servicio) y elimínalo del historial.")
        return 1
    print(f"Sin secretos ni archivos privados en el árbol ni en el historial ({len(set(nombres))} rutas revisadas).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
