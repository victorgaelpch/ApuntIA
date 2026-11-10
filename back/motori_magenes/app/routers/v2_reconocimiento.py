"""Motores y perfiles de reconocimiento (FULL-30). Contrato: docs/api-v2.md §10.

Los trabajos de análisis ya existen (`/api/v2/apuntes`, `/api/v2/trabajos`, BACK-27): aquí solo se
consulta qué motores hay y qué perfil se puede usar, sin duplicar rutas. Sin datos del equipo
(RAM, GPU): eso solo lo ve quien administra, en `/api/v2/diagnostico`.
"""

from fastapi import APIRouter, Depends

from app.core.seguridad import sesion_actual
from app.services.cuentas import Sesion
from app.services.ia import registro as reg

router = APIRouter(prefix="/api/v2/reconocimiento", tags=["v2: reconocimiento"])


@router.get("/motores")
def motores(sesion: Sesion = Depends(sesion_actual)):
    return {"motores": reg.registro().describir()}


@router.get("/perfiles")
def perfiles(sesion: Sesion = Depends(sesion_actual)):
    return reg.perfiles(reg.registro())
