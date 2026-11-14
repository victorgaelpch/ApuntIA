"""Administración de dispositivos del servidor IA (FULL-31). Solo en la PC del servidor.

    python -m ia_servidor.admin                    # menú interactivo
    python -m ia_servidor.admin pendientes
    python -m ia_servidor.admin aprobar K7Q4-M2XP
    python -m ia_servidor.admin rechazar K7Q4-M2XP
    python -m ia_servidor.admin dispositivos
    python -m ia_servidor.admin revocar <id-del-dispositivo>

Trabaja directamente sobre el registro (IA_DATOS o ia_servidor/.datos), así que funciona con el
servidor encendido o apagado. Antes de aprobar, comprueba que el código y el nombre coinciden
con lo que te dicta la persona: aprobar un código que no esperabas da acceso a la GPU.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from ia_servidor.config import carpeta_datos
from ia_servidor.dispositivos import ErrorVinculacion, Registro


def _fecha(t: float | None) -> str:
    return datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M") if t else "nunca"


def mostrar_pendientes(r: Registro) -> list[dict]:
    p = r.pendientes()
    if not p:
        print("No hay solicitudes pendientes.")
    for s in p:
        print(f"  {s['codigo'][:4]}-{s['codigo'][4:]}  «{s['nombre']}»  (id {s['dispositivo_id'][:12]}…, "
              f"caduca {_fecha(s['expira'])})")
    return p


def mostrar_dispositivos(r: Registro) -> None:
    d = r.dispositivos()
    if not d:
        print("No hay dispositivos vinculados.")
    for x in d:
        estado = f"REVOCADO {_fecha(x['revocado_en'])}" if x["revocado"] else "activo"
        print(f"  {x['id']}  «{x['nombre']}»  vinculado {_fecha(x['creado'])}  último uso {_fecha(x['ultimo_uso'])}  {estado}")


def interactivo(r: Registro) -> int:
    while True:
        print("\n=== Dispositivos del servidor IA ===")
        print("  1. Ver y aprobar solicitudes pendientes\n  2. Ver dispositivos vinculados\n  3. Revocar un dispositivo\n  0. Salir")
        op = input("Opción: ").strip()
        if op == "0":
            return 0
        if op == "1":
            if mostrar_pendientes(r):
                codigo = input("Código a resolver (vacío = volver): ").strip()
                if codigo:
                    accion = input("¿Aprobar (a) o rechazar (r)? ").strip().lower()
                    try:
                        res = r.resolver(codigo, aprobar=accion.startswith("a"))
                        print(f"Solicitud de «{res['nombre']}»: {res['estado']}.")
                    except ErrorVinculacion as e:
                        print(e.mensaje)
        elif op == "2":
            mostrar_dispositivos(r)
        elif op == "3":
            mostrar_dispositivos(r)
            ident = input("Id del dispositivo a revocar (vacío = volver): ").strip()
            if ident and input(f"¿Revocar {ident}? Dejará de poder usar el servidor (s/N): ").strip().lower() == "s":
                print("Revocado." if r.revocar(ident) else "No había ningún dispositivo activo con ese id.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Administración de dispositivos del servidor IA")
    p.add_argument("accion", nargs="?", choices=["pendientes", "aprobar", "rechazar", "dispositivos", "revocar"])
    p.add_argument("valor", nargs="?")
    a = p.parse_args(argv)
    r = Registro(carpeta_datos(os.environ.get("IA_DATOS", "").strip()))
    try:
        if a.accion is None:
            return interactivo(r)
        if a.accion == "pendientes":
            mostrar_pendientes(r)
        elif a.accion == "dispositivos":
            mostrar_dispositivos(r)
        elif a.accion in ("aprobar", "rechazar"):
            if not a.valor:
                print("Indica el código, p. ej.: aprobar K7Q4-M2XP")
                return 1
            res = r.resolver(a.valor, aprobar=a.accion == "aprobar")
            print(f"Solicitud de «{res['nombre']}» ({res['dispositivo_id'][:12]}…): {res['estado']}.")
        elif a.accion == "revocar":
            if not a.valor:
                print("Indica el id del dispositivo (ver: dispositivos)")
                return 1
            n = r.revocar(a.valor)
            print("Revocado: ya no puede usar el servidor." if n else "No había ningún dispositivo activo con ese id.")
            return 0 if n else 1
        return 0
    except ErrorVinculacion as e:
        print(e.mensaje)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
