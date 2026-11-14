"""Investigación opcional y revisión de ampliaciones (BACK-18). Contrato: fullstack/docs/api-v2.md §5 y §7."""

from typing import Literal

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from app.core import contexto
from app.core.errores import ApiError
from app.core.seguridad import sesion_actual
from app.routers.v2_apuntes import _version_de, repositorio
from app.services import investigacion
from app.services.cuentas import Sesion

router = APIRouter(prefix="/api/v2", tags=["v2: investigación"])


class PeticionInvestigacion(BaseModel):
    consentimiento: bool = False
    conceptos: list[str] = Field(min_length=1, max_length=investigacion.MAX_CONCEPTOS)
    idioma: Literal["es", "en"] = "es"


class CambioAmpliacion(BaseModel):
    estado: Literal["aceptada", "rechazada", "propuesta"]


@router.get("/apuntes/{apunte_id}/conceptos")
def sugerir_conceptos(apunte_id: str, sesion: Sesion = Depends(sesion_actual)):
    """Conceptos del apunte que se podrían investigar. No consulta nada fuera."""
    doc = repositorio().documento(sesion.usuario.id, apunte_id)
    return {"conceptos": investigacion.conceptos_sugeridos(doc),
            "disponible": investigacion.proveedor().disponible(),
            "proveedor": investigacion.proveedor().nombre}


@router.post("/apuntes/{apunte_id}/investigacion", status_code=202)
def investigar(apunte_id: str, datos: PeticionInvestigacion, sesion: Sesion = Depends(sesion_actual)):
    repositorio().obtener(sesion.usuario.id, apunte_id, con_documento=False)  # existe y es suyo
    if not datos.consentimiento:
        raise ApiError(400, "CONSENTIMIENTO_REQUERIDO",
                       "Confirma que aceptas enviar los conceptos elegidos a una fuente externa.")
    if not sesion.usuario.preferencias.get("investigacion_permitida"):
        raise ApiError(400, "CONSENTIMIENTO_REQUERIDO",
                       "Activa «Permitir investigación externa» en tu perfil para usar esta función.")
    if not investigacion.proveedor().disponible():
        raise ApiError(503, "INVESTIGACION_NO_DISPONIBLE",
                       "La investigación externa no está disponible en este servidor. Tu apunte funciona igual sin ella.")
    try:
        conceptos = list(dict.fromkeys(investigacion.concepto_valido(c) for c in datos.conceptos))
    except ValueError as exc:
        raise ApiError(400, "DATOS_INVALIDOS", str(exc)) from None
    trabajo = contexto.obtener().trabajos.encolar(sesion.usuario.id, "investigacion", apunte_id,
                                                  {"conceptos": conceptos, "idioma": datos.idioma})
    return {"trabajo": trabajo}


@router.patch("/apuntes/{apunte_id}/ampliaciones/{ampliacion_id}")
def revisar_ampliacion(apunte_id: str, ampliacion_id: str, datos: CambioAmpliacion,
                       if_match: str | None = Header(None), sesion: Sesion = Depends(sesion_actual)):
    """Acepta o rechaza una ampliación (crea una versión). Solo cambia su estado."""
    repo = repositorio()
    esperada = _version_de(if_match) if if_match else None
    repo.comprobar_editable(sesion.usuario.id, apunte_id)
    doc = repo.documento(sesion.usuario.id, apunte_id)
    if not any(a.id == ampliacion_id for a in doc.ampliaciones):
        raise ApiError(404, "NO_ENCONTRADO", "No encontramos esa ampliación.")
    ampliaciones = [a.model_copy(update={"estado": datos.estado}) if a.id == ampliacion_id else a
                    for a in doc.ampliaciones]
    version = repo.nueva_version(sesion.usuario.id, apunte_id, doc.model_copy(update={"ampliaciones": ampliaciones}),
                                 "ampliacion", version_esperada=esperada)
    return {"apunte": repo.obtener(sesion.usuario.id, apunte_id), "version": version}
