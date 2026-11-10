"""Validación y vista previa de fórmulas (BACK-15, FRONT-14). Contrato: docs/api-v2.md §5."""

import base64

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.errores import ApiError
from app.core.seguridad import sesion_actual
from app.services.cuentas import Sesion
from app.services.formulas import convertir, renderizar_png

router = APIRouter(prefix="/api/v2", tags=["v2: fórmulas"])


class PeticionFormula(BaseModel):
    latex: str | None = Field(default=None, max_length=2000)
    texto: str | None = Field(default=None, max_length=2000, description="Fórmula en texto lineal, p. ej. x^2 + 1")


@router.post("/formulas/validar")
def validar_formula(datos: PeticionFormula, _sesion: Sesion = Depends(sesion_actual)):
    latex = datos.latex
    if latex is None and datos.texto is not None:
        latex, _ = convertir(datos.texto)
        if latex is None:
            return {"valida": False, "latex": None, "errores": ["No se pudo interpretar la fórmula."], "vista_previa": None}
    if latex is None:
        raise ApiError(400, "DATOS_INVALIDOS", "Envía «latex» o «texto».")
    try:
        png = renderizar_png(latex)
    except ApiError as exc:
        if exc.codigo == "LATEX_NO_PERMITIDO":
            raise
        return {"valida": False, "latex": latex, "errores": [exc.mensaje], "vista_previa": None}
    return {"valida": True, "latex": latex, "errores": [],
            "vista_previa": "data:image/png;base64," + base64.b64encode(png).decode()}
