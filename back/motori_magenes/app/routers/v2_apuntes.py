"""Rutas de apuntes de la API v2. Contrato: docs/api-v2.md §5."""

from typing import Literal

from fastapi import APIRouter, Body, Depends, File, Form, Header, Query, UploadFile
from fastapi.responses import JSONResponse, Response

from app.core import contexto
from app.core.seguridad import sesion_actual
from app.datos.almacen import ArchivoNoEncontrado
from app.datos.apuntes import RepositorioApuntes
from app.services.cuentas import Sesion
from app.core.errores import ApiError
from app.services import analisis  # noqa: F401 — registra el manejador de trabajos «analisis»
from app.services.documento import fusionar, validar
from app.services.estructura import estructurar
from app.services.entrada import validar_paginas

router = APIRouter(prefix="/api/v2", tags=["v2: apuntes"])


def repositorio() -> RepositorioApuntes:
    ctx = contexto.obtener()
    return RepositorioApuntes(ctx.bd, ctx.almacen)


@router.post("/apuntes", status_code=202)
def crear_apunte(
    paginas: list[UploadFile] | None = File(None, description="Fotos en orden (JPEG, PNG o WEBP)"),
    tipos: list[str] | None = Form(None, description="Un tipo por página: pizarron o cuaderno"),
    titulo: str = Form("", max_length=200),
    idempotency_key: str | None = Header(None, max_length=100),
    sesion: Sesion = Depends(sesion_actual),
):
    recibidas = validar_paginas(paginas, tipos)
    repo = repositorio()
    trabajos = contexto.obtener().trabajos
    apunte, creado = repo.crear(sesion.usuario.id, titulo, recibidas, idempotency_key)
    if not creado:  # misma Idempotency-Key: se devuelve lo ya creado, sin otro análisis
        fila = contexto.obtener().bd.uno("SELECT id FROM trabajos WHERE apunte_id = ? AND tipo = 'analisis' "
                                         "ORDER BY creado DESC LIMIT 1", (apunte["id"],))
        trabajo = trabajos.obtener(sesion.usuario.id, fila["id"]) if fila else None
        return JSONResponse({"apunte": apunte, "trabajo": trabajo}, status_code=200)
    try:
        trabajo = trabajos.encolar(sesion.usuario.id, "analisis", apunte["id"],
                                   {"idiomas": sesion.usuario.preferencias.get("idioma_ocr")})
    except ApiError:
        repo.borrar(sesion.usuario.id, apunte["id"])  # sin trabajo no se deja un apunte huérfano
        raise
    return JSONResponse({"apunte": apunte, "trabajo": trabajo}, status_code=202)


@router.get("/apuntes/{apunte_id}")
def ver_apunte(apunte_id: str, sesion: Sesion = Depends(sesion_actual)):
    apunte = repositorio().obtener(sesion.usuario.id, apunte_id)
    fila = contexto.obtener().bd.uno("SELECT id FROM trabajos WHERE apunte_id = ? ORDER BY creado DESC LIMIT 1",
                                     (apunte_id,))
    apunte["ultimo_trabajo"] = contexto.obtener().trabajos.obtener(sesion.usuario.id, fila["id"]) if fila else None
    return {"apunte": apunte}


@router.get("/apuntes/{apunte_id}/archivos/{archivo_id}")
def ver_archivo(apunte_id: str, archivo_id: str, sesion: Sesion = Depends(sesion_actual)):
    repositorio().obtener(sesion.usuario.id, apunte_id, con_documento=False)  # el apunte es suyo
    try:
        archivo = contexto.obtener().almacen.obtener(sesion.usuario.id, archivo_id)
    except ArchivoNoEncontrado:
        raise ApiError(404, "NO_ENCONTRADO", "No encontramos ese archivo.") from None
    if archivo.apunte_id != apunte_id or archivo.tipo == "pdf":
        raise ApiError(404, "NO_ENCONTRADO", "No encontramos ese archivo.")
    return Response(archivo.ruta.read_bytes(), media_type=archivo.mime,
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


# ---------------------------------------------------------------- historial (BACK-26)

@router.get("/apuntes")
def listar_apuntes(
    q: str = Query("", max_length=200, description="Busca en el título y en el texto del apunte"),
    estado: Literal["pendiente", "procesando", "listo", "parcial", "fallido", "cancelado"] | None = None,
    tipo_fuente: Literal["pizarron", "cuaderno", "mixto"] | None = None,
    pagina: int = Query(1, ge=1, le=10000),
    por_pagina: int = Query(20, ge=1, le=100),
    orden: Literal["reciente", "antiguo", "titulo"] = "reciente",
    sesion: Sesion = Depends(sesion_actual),
):
    return repositorio().listar(sesion.usuario.id, q.strip(), estado, tipo_fuente, pagina, por_pagina, orden)


def _version_de(if_match: str | None) -> int:
    if not if_match:
        raise ApiError(428, "VERSION_REQUERIDA", "Falta la cabecera If-Match con la versión que editaste.")
    try:
        return int(if_match.strip().strip('"').removeprefix("W/").strip('"'))
    except ValueError:
        raise ApiError(400, "DATOS_INVALIDOS", "If-Match debe ser el número de versión.") from None


@router.put("/apuntes/{apunte_id}/documento")
def guardar_documento(apunte_id: str, documento: dict = Body(...), if_match: str | None = Header(None),
                      sesion: Sesion = Depends(sesion_actual)):
    esperada = _version_de(if_match)
    repo = repositorio()
    repo.comprobar_editable(sesion.usuario.id, apunte_id)
    nuevo = validar(documento)  # si no valida, no se toca la versión anterior
    anterior = repo.documento(sesion.usuario.id, apunte_id)
    version = repo.nueva_version(sesion.usuario.id, apunte_id, fusionar(anterior, nuevo), "edicion",
                                 version_esperada=esperada)
    return {"apunte": repo.obtener(sesion.usuario.id, apunte_id), "version": version}


@router.get("/apuntes/{apunte_id}/versiones")
def listar_versiones(apunte_id: str, sesion: Sesion = Depends(sesion_actual)):
    return {"versiones": repositorio().versiones(sesion.usuario.id, apunte_id)}


@router.get("/apuntes/{apunte_id}/versiones/{numero}")
def ver_version(apunte_id: str, numero: int, sesion: Sesion = Depends(sesion_actual)):
    doc = repositorio().documento(sesion.usuario.id, apunte_id, numero)
    return {"version": numero, "documento": doc.model_dump()}


@router.post("/apuntes/{apunte_id}/versiones/{numero}/restaurar")
def restaurar_version(apunte_id: str, numero: int, sesion: Sesion = Depends(sesion_actual)):
    repo = repositorio()
    repo.comprobar_editable(sesion.usuario.id, apunte_id)
    doc = repo.documento(sesion.usuario.id, apunte_id, numero)
    version = repo.nueva_version(sesion.usuario.id, apunte_id, doc, "restauracion")
    return {"apunte": repo.obtener(sesion.usuario.id, apunte_id), "version": version}


@router.delete("/apuntes/{apunte_id}", status_code=204)
def borrar_apunte(apunte_id: str, sesion: Sesion = Depends(sesion_actual)):
    repo = repositorio()
    trabajos = contexto.obtener().trabajos
    for fila in contexto.obtener().bd.todos("SELECT id FROM trabajos WHERE apunte_id = ? AND estado IN "
                                            "('pendiente', 'procesando')", (apunte_id,)):
        trabajos.cancelar(sesion.usuario.id, fila["id"])  # no deja trabajos sobre un apunte borrado
    repo.borrar(sesion.usuario.id, apunte_id)


@router.get("/apuntes/{apunte_id}/estructura")
def ver_estructura(apunte_id: str, version: int | None = Query(None, ge=1), sesion: Sesion = Depends(sesion_actual)):
    """Apunte estructurado (secciones, resumen extraído, conceptos, glosario…) de una versión (BACK-19)."""
    repo = repositorio()
    doc = repo.documento(sesion.usuario.id, apunte_id, version)
    numero = version or repo.obtener(sesion.usuario.id, apunte_id, con_documento=False)["version"]
    return {"version": numero, "estructura": estructurar(doc).a_dict()}
