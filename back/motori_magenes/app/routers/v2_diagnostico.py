"""Disponibilidad y diagnóstico (FULL-21). Guía: fullstack/docs/diagnostico.md.

- `GET /salud` (v1, sin cambios de contrato): la aplicación está VIVA y responde.
- `GET /api/v2/listo`: sus dependencias están LISTAS. 200 si todas las obligatorias
  funcionan; 503 con cuáles fallan y qué hacer.
- `GET /api/v2/diagnostico`: métricas para quien administra el equipo. Solo responde a
  peticiones desde el propio equipo (127.0.0.1/::1): ni la red local ni el proxy de Docker
  la ven; en Docker se consulta con «docker compose exec backend …».
"""

import platform
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core import diagnostico
from app.core.config import settings
from app.core.errores import ApiError

router = APIRouter(prefix="/api/v2", tags=["v2: diagnóstico"])
LOCALES = {"127.0.0.1", "::1", "localhost"}


@router.get("/listo")
def listo():
    dependencias = diagnostico.comprobar_dependencias()
    fallan = [nombre for nombre, d in dependencias.items() if d["obligatoria"] and not d["ok"]]
    cuerpo = {"listo": not fallan, "dependencias": dependencias}
    if fallan:
        cuerpo["mensaje"] = "No está lista: " + "; ".join(f"{n}: {dependencias[n]['detalle']}" for n in fallan)
    return JSONResponse(cuerpo, status_code=200 if not fallan else 503)


@router.get("/diagnostico")
def diagnostico_local(request: Request):
    if not request.client or request.client.host not in LOCALES:
        raise ApiError(404, "RUTA_NO_ENCONTRADA", "La ruta solicitada no existe.")
    return {
        "version": settings.version, "python": platform.python_version(),
        "activo_desde_s": round(time.time() - diagnostico.INICIO),
        "memoria_maxima_mb": diagnostico.memoria_mb(),
        "datos_mb": diagnostico.tamano_datos_mb(),
        "dependencias": diagnostico.comprobar_dependencias(),
        "peticiones": diagnostico.metricas.resumen(),
        "trabajos": diagnostico.resumen_trabajos(),
        "limites": {"alerta_peticion_ms": settings.alerta_peticion_ms, "alerta_trabajo_s": settings.alerta_trabajo_s,
                    "minimo_disco_mb": settings.minimo_disco_mb, "max_trabajos_simultaneos": settings.max_trabajos_simultaneos},
    }
