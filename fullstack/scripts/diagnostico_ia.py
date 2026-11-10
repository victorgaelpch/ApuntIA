"""Diagnóstico de la IA local de ApuntIA (FULL-30). No descarga ni instala nada.

    python fullstack/scripts/diagnostico_ia.py              # equipo, Ollama, modelo y perfiles
    python fullstack/scripts/diagnostico_ia.py --probar     # además, una inferencia de prueba
    python fullstack/scripts/diagnostico_ia.py --json       # salida para máquinas

Usa la misma configuración que el backend (variables de entorno o fullstack/config/.env).
Ejecútalo con el Python del entorno del backend (back/motori_magenes/.venv).

--probar manda al modelo una imagen SINTÉTICA (texto y una fórmula dibujados aquí, ningún apunte
real) y comprueba que devuelve un JSON válido; informa del tiempo. No mide la calidad: para eso
está la evaluación (docs/arquitectura-ia.md §5).

Código de salida: 0 si la IA está lista (o desactivada a propósito), 1 si está activada pero no
se puede usar, 2 si --probar falla.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BACK = RAIZ / "back" / "motori_magenes"
sys.path.insert(0, str(BACK))


def _cargar_env() -> None:
    """Lee fullstack/config/.env sin pisar variables ya definidas (como hacen los scripts de inicio)."""
    archivo = RAIZ / "fullstack" / "config" / ".env"
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, _, valor = linea.partition("=")
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def imagen_prueba():
    import cv2
    import numpy as np
    img = np.full((220, 700, 3), 250, np.uint8)
    cv2.putText(img, "Velocidad media", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (30, 30, 30), 3, cv2.LINE_AA)
    cv2.putText(img, "v = d / t", (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (30, 30, 30), 3, cv2.LINE_AA)
    return img


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--probar", action="store_true", help="hace una inferencia de prueba con una imagen sintética")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    _cargar_env()

    from app.core.config import settings
    from app.services.ia import registro as reg
    from app.services.ia.motores import ErrorMotor, OpcionesReconocimiento

    r = reg.registro()
    equipo = reg.hardware()
    vlm = r.motores["ollama_vlm"]
    ok, info = vlm.estado(refrescar=True)
    informe = {"equipo": equipo, "ia_activada": settings.ia_activada, "ollama_host": settings.ollama_host,
               "modelo": settings.vlm_modelo, "vlm_disponible": ok, "vlm": info.a_dict(),
               "motores": r.describir(), **reg.perfiles(r, equipo)}

    if args.probar:
        if not ok:
            informe["prueba"] = {"ok": False, "error": info.detalle}
        else:
            inicio = time.perf_counter()
            try:
                res = vlm.reconocer(imagen_prueba(), OpcionesReconocimiento(tarea="texto_impreso"))
                informe["prueba"] = {"ok": True, "segundos": round(time.perf_counter() - inicio, 1),
                                     "texto": res.texto, "ilegible": res.ilegible,
                                     "esperado": "Velocidad media\nv = d / t"}
            except ErrorMotor as exc:
                informe["prueba"] = {"ok": False, "codigo": exc.codigo, "error": exc.mensaje}

    if args.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    else:
        ram = f"{equipo['ram_gb']} GB ({equipo['ram_disponible_gb']} libres)" if equipo["ram_gb"] else "desconocida"
        gpus = ", ".join(f"{g['nombre']} {g['vram_gb']} GB" for g in equipo["gpus"]) or "ninguna NVIDIA detectada"
        print(f"Equipo: {equipo['sistema']} · {equipo['cpus']} CPU · RAM {ram} · GPU: {gpus}")
        print(f"IA local: {'activada' if settings.ia_activada else 'desactivada (IA_ACTIVADA=false)'}"
              f" · {settings.ollama_host} · modelo {settings.vlm_modelo}")
        print(f"Modelo visual: {'LISTO' if ok else 'no disponible'}"
              + (f" (Ollama {info.version})" if ok else f": {info.detalle}"))
        print(f"Memoria para el modelo: {informe['memoria_vlm']}")
        for nombre, p in informe["perfiles"].items():
            extra = f" → {p['elige']}" if nombre == "automatico" and p.get("elige") else ""
            print(f"  perfil {nombre:<12} {'sí' if p['disponible'] else 'no'}{extra}"
                  + (f"  ({p['detalle']})" if p.get("detalle") else ""))
        if "prueba" in informe:
            pr = informe["prueba"]
            print("Prueba: " + (f"JSON válido en {pr['segundos']} s; leyó {pr['texto']!r} (esperado {pr['esperado']!r})"
                                if pr["ok"] else f"FALLÓ: {pr.get('error')}"))
    if args.probar and not informe["prueba"]["ok"]:
        return 2
    return 1 if settings.ia_activada and not ok else 0


if __name__ == "__main__":
    sys.exit(main())
