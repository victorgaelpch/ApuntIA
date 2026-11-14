"""Exportación a PDF (BACK-20). Contrato: fullstack/docs/api-v2.md §5."""

import re
import unicodedata
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.core import contexto
from app.core.errores import ApiError
from app.core.seguridad import sesion_actual
from app.datos.almacen import ArchivoNoEncontrado
from app.routers.v2_apuntes import repositorio
from app.services import exportacion
from app.services.cuentas import Sesion
from app.services.pdf import OpcionesPDF

router = APIRouter(prefix="/api/v2", tags=["v2: exportaciones"])


class PeticionExportacion(BaseModel):
    version: int | None = Field(default=None, ge=1)
    estilo: Literal["basico", "extendido"] = "extendido"
    incluir_originales: bool = False
    incluir_complementos: bool = True
    incluir_recortes_ia: bool = True     # BACK-38: recorte junto a cada propuesta del servidor IA sin revisar


def nombre_descarga(titulo: str, version: int) -> str:
    """Nombre ASCII seguro para Content-Disposition (sin rutas ni comillas)."""
    base = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower()[:60] or "apunte"
    return f"{base}-v{version}.pdf"


@router.post("/apuntes/{apunte_id}/exportaciones", status_code=202)
def exportar(apunte_id: str, datos: PeticionExportacion | None = None, sesion: Sesion = Depends(sesion_actual)):
    datos = datos or PeticionExportacion()
    opciones = OpcionesPDF(datos.estilo, datos.incluir_originales, datos.incluir_complementos,
                           datos.incluir_recortes_ia)
    exp, trabajo, creada = exportacion.solicitar(sesion.usuario.id, apunte_id, datos.version, opciones)
    return JSONResponse({"exportacion": exp, "trabajo": trabajo}, status_code=202 if creada else 200)


@router.get("/apuntes/{apunte_id}/exportaciones")
def listar_exportaciones(apunte_id: str, sesion: Sesion = Depends(sesion_actual)):
    repositorio().obtener(sesion.usuario.id, apunte_id, con_documento=False)
    filas = contexto.obtener().bd.todos("SELECT * FROM exportaciones WHERE apunte_id = ? AND usuario_id = ? "
                                        "ORDER BY version DESC, creado DESC", (apunte_id, sesion.usuario.id))
    return {"exportaciones": [exportacion.publica(f) for f in filas]}


@router.get("/exportaciones/{exportacion_id}")
def ver_exportacion(exportacion_id: str, sesion: Sesion = Depends(sesion_actual)):
    return {"exportacion": exportacion.publica(exportacion.obtener(sesion.usuario.id, exportacion_id))}


@router.get("/exportaciones/{exportacion_id}/pdf")
def descargar_pdf(exportacion_id: str, sesion: Sesion = Depends(sesion_actual)):
    fila = exportacion.obtener(sesion.usuario.id, exportacion_id)
    if fila["estado"] != "completado" or not fila["archivo_id"]:
        raise ApiError(409, "PDF_NO_LISTO", "El PDF todavía no está listo.")
    ctx = contexto.obtener()
    try:
        archivo = ctx.almacen.obtener(sesion.usuario.id, fila["archivo_id"])
    except ArchivoNoEncontrado:
        raise ApiError(404, "NO_ENCONTRADO", "No encontramos ese PDF.") from None
    titulo = ctx.bd.uno("SELECT titulo FROM apuntes WHERE id = ?", (fila["apunte_id"],))["titulo"]
    return Response(archivo.ruta.read_bytes(), media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{nombre_descarga(titulo, fila["version"])}"',
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
        "ETag": f'"{fila["sha256"]}"', "X-ApuntIA-Sha256": fila["sha256"]})
