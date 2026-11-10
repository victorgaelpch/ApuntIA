"""Datos de DEMOSTRACIÓN de ApuntIA (FULL-22), separados de los datos reales.

Crea en una ApuntIA ya en marcha una cuenta de ejemplo con apuntes hechos a partir de fotos
SINTÉTICAS (el corpus de evaluación, generado por código): ningún dato de una persona real.
Es idempotente: si la cuenta ya existe, no crea nada más. La contraseña se genera la primera vez,
se muestra al terminar y se guarda en clave-demo.txt, junto a los datos de la demostración.

    python fullstack/scripts/demo.py http://localhost:8000

Lo llama `iniciar.sh --demo`, que además arranca ApuntIA con DATA_DIR=fullstack/.demo/datos para que
la demostración nunca se mezcle con los datos reales. Necesita el Python del backend (OpenCV).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2] / "back" / "motori_magenes"
sys.path.insert(0, str(BACKEND))
from herramientas.claves_prueba import clave_de_prueba  # noqa: E402

EMAIL = "demo@example.com"


def clave_demo() -> str:
    """La contraseña de la cuenta de demostración NO está en el código: se genera la primera vez y
    se guarda (solo legible por ti) junto a los datos de la demostración, para reutilizarla."""
    datos = os.environ.get("DATA_DIR")
    carpeta = Path(datos).parent if datos else Path(__file__).resolve().parents[1] / ".demo"
    archivo = carpeta / "clave-demo.txt"
    if archivo.exists():
        return archivo.read_text(encoding="utf-8").strip()
    clave = clave_de_prueba("demo")
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo.write_text(clave + "\n", encoding="utf-8")
    archivo.chmod(0o600)
    return clave


PASSWORD = clave_demo()
APUNTES = [
    ("Demostración: pizarrón", ["impreso_pizarron", "pizarron_con_ruido", "formulas_pizarron"]),
    ("Demostración: cuaderno", ["impreso_cuaderno", "cuaderno_con_sombra", "diagrama"]),
]


def peticion(url: str, metodo: str = "GET", cuerpo: bytes | None = None, cabeceras: dict | None = None):
    req = urllib.request.Request(url, data=cuerpo, method=metodo, headers=cabeceras or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.headers, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, e.headers, json.loads(e.read() or b"{}")


def multipart(campos: list[tuple[str, str]], archivos: list[tuple[str, str, bytes]]) -> tuple[bytes, str]:
    limite = uuid.uuid4().hex
    partes = []
    for nombre, valor in campos:
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n'.encode())
    for nombre, archivo, datos in archivos:
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{nombre}"; filename="{archivo}"\r\n'
                      f"Content-Type: image/png\r\n\r\n".encode() + datos + b"\r\n")
    partes.append(f"--{limite}--\r\n".encode())
    return b"".join(partes), f"multipart/form-data; boundary={limite}"


def main(url: str) -> int:
    import cv2

    from herramientas.corpus import corpus

    json_h = {"Content-Type": "application/json", "Origin": url}
    estado, cab, _ = peticion(f"{url}/api/v2/auth/sesion", "POST", json.dumps({"email": EMAIL, "password": PASSWORD}).encode(), json_h)
    if estado == 200:
        print(f"La demostración ya está preparada. Entra con {EMAIL} / «{PASSWORD}».")
        return 0
    estado, cab, cuerpo = peticion(f"{url}/api/v2/auth/registro", "POST",
                                   json.dumps({"email": EMAIL, "nombre": "Demostración", "password": PASSWORD}).encode(), json_h)
    if estado != 201:
        print(f"No se pudo crear la cuenta de demostración ({estado}): {cuerpo}", file=sys.stderr)
        return 1
    cookie = cab.get("Set-Cookie", "").split(";")[0]
    sesion = {"Cookie": cookie, "X-CSRF-Token": cuerpo["csrf"], "Origin": url}

    muestras = {m.nombre: m for m in corpus()}
    trabajos = []
    for titulo, nombres in APUNTES:
        archivos = [("paginas", f"{n}.png", cv2.imencode(".png", muestras[n].imagen)[1].tobytes()) for n in nombres]
        campos = [("titulo", titulo)] + [("tipos", muestras[n].tipo_fuente) for n in nombres]
        datos, tipo = multipart(campos, archivos)
        estado, _, r = peticion(f"{url}/api/v2/apuntes", "POST", datos, {**sesion, "Content-Type": tipo})
        if estado not in (201, 202):
            print(f"No se pudo crear «{titulo}» ({estado}): {r}", file=sys.stderr)
            return 1
        trabajos.append((titulo, r["trabajo"]["id"]))
        print(f"▶ Analizando «{titulo}» ({len(nombres)} fotos sintéticas)…")

    for titulo, trabajo in trabajos:
        fin = time.monotonic() + 300
        while True:
            _, _, r = peticion(f"{url}/api/v2/trabajos/{trabajo}", cabeceras={"Cookie": cookie})
            if r["trabajo"]["estado"] not in ("pendiente", "procesando"):
                break
            if time.monotonic() > fin:
                print(f"«{titulo}» sigue analizándose; aparecerá terminado en unos minutos.")
                break
            time.sleep(0.5)
        print(f"✔ «{titulo}»: {r['trabajo']['estado']}")
    print(f"\nDemostración lista. Entra en {url}/front/cuenta.html con {EMAIL} / «{PASSWORD}».")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"))
