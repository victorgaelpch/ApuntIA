"""Contraseñas de PRUEBA generadas al ejecutar: nunca se escriben en el código.

Cada ejecución usa una semilla aleatoria (APUNTIA_SEMILLA_PRUEBAS) que heredan los procesos hijos,
así que el mismo nombre da la misma contraseña al registrarse y al entrar, también entre Python y
Node (fullstack/tests/claves.js hace el mismo cálculo).
"""

import hashlib
import hmac
import os
import secrets

_SEMILLA = "APUNTIA_SEMILLA_PRUEBAS"
os.environ.setdefault(_SEMILLA, secrets.token_hex(16))


def clave_de_prueba(nombre: str) -> str:
    huella = hmac.new(os.environ[_SEMILLA].encode(), nombre.encode(), hashlib.sha256).hexdigest()
    return f"prueba-{huella[:20]}"
