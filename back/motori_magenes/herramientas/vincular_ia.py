"""Vincular esta instalación de ApuntIA con el servidor IA, desde la consola (FULL-31).

    python -m herramientas.vincular_ia                 # vincular (usa APUNTIA_IA_URL o la URL guardada)
    python -m herramientas.vincular_ia --url https://ia.ejemplo.org
    python -m herramientas.vincular_ia --diagnostico
    python -m herramientas.vincular_ia --probar foto.png [--tarea texto_manuscrito]
    python -m herramientas.vincular_ia --desvincular

Lo usa `iniciar.bat -Modo configurar`. Equivale a las rutas /api/v2/ia de la interfaz y guarda
la credencial en el mismo lugar (DATA_DIR/ia_remota.json, cifrada con DPAPI en Windows).
Nunca muestra el token. Códigos de salida: 0 bien · 1 error · 2 rechazada/caducada · 3 sin respuesta.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

from app.core.config import settings
from app.services.ia_remota import Almacen, ClienteIARemota, ErrorIARemota, SOLUCIONES, url_efectiva, validar_url


def _cliente(url_arg: str | None) -> ClienteIARemota:
    almacen = Almacen(settings.data_dir)
    if url_arg:
        motivo = validar_url(url_arg.rstrip("/"))
        if motivo:
            raise ErrorIARemota("AI_URL_INVALIDA", motivo)
        almacen.actualizar(modo="manual", url=url_arg.rstrip("/"))
    url = url_efectiva(almacen, settings.ia_url)
    return ClienteIARemota(url, almacen, timeout_s=settings.ia_timeout_s, timeout_analisis_s=settings.ia_timeout_analisis_s)


def vincular(c: ClienteIARemota, esperar_s: int) -> int:
    if c.estado()["vinculado"]:
        print(f"Este equipo ya está vinculado con {c.url}. Comprobando la credencial…")
        print(f"OK: el servidor reconoce este equipo como «{c.yo()['nombre']}».")
        return 0
    en_curso = c.estado()["vinculacion_en_curso"]
    if en_curso and (en_curso.get("expira") or 0) > time.time() + 20:  # retomar en vez de pedir otro código
        v = {"codigo": en_curso["codigo"], "expira_en_s": int(en_curso["expira"] - time.time())}
        print("Retomando la solicitud que ya estaba en curso.")
    else:
        v = c.solicitar_vinculacion(f"ApuntIA en {platform.node() or 'este equipo'}")
    print()
    print(f"   CÓDIGO DE VINCULACIÓN:   {v['codigo']}")
    print()
    print("Díctale este código a quien administra la PC del servidor IA. Debe aprobarlo allí con:")
    print("   iniciar.bat -Modo dispositivos      (o: python -m ia_servidor.admin aprobar " + v["codigo"] + ")")
    print(f"El código caduca en {v['expira_en_s'] // 60} minutos. Esperando la aprobación (Ctrl+C para salir)…")
    fin = time.monotonic() + min(esperar_s, v["expira_en_s"])
    while time.monotonic() < fin:
        time.sleep(3)
        r = c.sondear_vinculacion()
        if r["estado"] == "vinculado":
            print(f"OK: equipo vinculado. La credencial se guardó cifrada ({c.estado()['proteccion_credencial']}).")
            return 0
        if r["estado"] in ("rechazada", "expirada", "anulada"):
            print(f"La solicitud quedó {r['estado']}. Pide un código nuevo.")
            return 2
    print("Se acabó la espera sin aprobación. Puedes volver a ejecutar este paso: la solicitud sigue vigente unos minutos.")
    return 3


def diagnostico(c: ClienteIARemota) -> int:
    pasos = c.diagnosticar()
    for p in pasos:
        marca = "OK" if p["ok"] else "X "
        print(f"{marca} {p['paso']:22} {p.get('detalle')}  ({p['ms']} ms)")
        if not p["ok"]:
            print(f"   Código {p['codigo']}. Solución: {p['solucion']}")
    return 0 if all(p["ok"] for p in pasos) else 1


def main(argv: list[str] | None = None) -> int:
    a = argparse.ArgumentParser(description="Vincular ApuntIA con el servidor IA")
    a.add_argument("--url")
    a.add_argument("--diagnostico", action="store_true")
    a.add_argument("--desvincular", action="store_true")
    a.add_argument("--probar", type=Path, help="imagen PNG/JPEG para un análisis de prueba")
    a.add_argument("--tarea", default="pagina")
    a.add_argument("--esperar", type=int, default=600, help="segundos máximos esperando la aprobación")
    args = a.parse_args(argv)
    try:
        c = _cliente(args.url)
        if args.desvincular:
            c.desvincular()
            print("Credencial borrada en este equipo. Pide al administrador que revoque el dispositivo en el servidor.")
            return 0
        if args.diagnostico:
            return diagnostico(c)
        if args.probar:
            tipo = "image/jpeg" if args.probar.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            inicio = time.perf_counter()
            r = c.analizar(args.probar.read_bytes(), args.tarea, tipo)
            print(json.dumps({"segundos": round(time.perf_counter() - inicio, 1), "modelo": r["modelo"],
                              "resultado": r["resultado"]}, ensure_ascii=False, indent=1))
            return 0
        return vincular(c, args.esperar)
    except ErrorIARemota as e:
        print(f"X {e.codigo}: {e.mensaje}")
        if SOLUCIONES.get(e.codigo) and SOLUCIONES[e.codigo] != e.mensaje:
            print(f"  Solución: {SOLUCIONES[e.codigo]}")
        return 1
    except KeyboardInterrupt:
        print("\nCancelado. Si ya diste el código, puedes volver a ejecutar este paso para recoger la aprobación.")
        return 3


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        # line_buffering: el código se ve al momento aunque la salida vaya a una tubería o a un registro
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.exit(main())
