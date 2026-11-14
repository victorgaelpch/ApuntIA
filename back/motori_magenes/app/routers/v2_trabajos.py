"""Rutas de trabajos de la API v2 (BACK-27). Contrato: fullstack/docs/api-v2.md §5."""

from fastapi import APIRouter, Depends

from app.core import contexto
from app.core.seguridad import sesion_actual
from app.services.cuentas import Sesion

router = APIRouter(prefix="/api/v2", tags=["v2: trabajos"])


@router.get("/trabajos/{trabajo_id}")
def ver_trabajo(trabajo_id: str, sesion: Sesion = Depends(sesion_actual)):
    return {"trabajo": contexto.obtener().trabajos.obtener(sesion.usuario.id, trabajo_id)}


@router.delete("/trabajos/{trabajo_id}")
def cancelar_trabajo(trabajo_id: str, sesion: Sesion = Depends(sesion_actual)):
    return {"trabajo": contexto.obtener().trabajos.cancelar(sesion.usuario.id, trabajo_id)}


@router.post("/trabajos/{trabajo_id}/reintentar")
def reintentar_trabajo(trabajo_id: str, sesion: Sesion = Depends(sesion_actual)):
    return {"trabajo": contexto.obtener().trabajos.reintentar(sesion.usuario.id, trabajo_id)}
