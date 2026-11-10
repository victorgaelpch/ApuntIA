"""Trabajo «exportacion»: versión del apunte → PDF privado (BACK-20).

Idempotencia: una exportación es única por (apunte, versión, opciones). Pedir
otra vez lo mismo devuelve la existente (o su trabajo en curso). El PDF se
guarda en el almacén privado con su SHA-256 y solo lo descarga el propietario.
Si la generación falla, la exportación queda «fallido» y no se guarda ningún
PDF (nunca un PDF vacío que parezca bueno). Todo se genera en memoria: no
quedan archivos temporales.
"""

import json
import logging
import secrets
import time

from app.core import contexto
from app.core.errores import ApiError
from app.datos.apuntes import RepositorioApuntes
from app.datos.bd import ahora
from app.services.estructura import estructurar
from app.services.pdf import ErrorPDF, OpcionesPDF, generar_pdf
from app.services.trabajos import ErrorTrabajo, Resultado, Trabajo

logger = logging.getLogger("apuntia.exportacion")


def publica(fila) -> dict:
    return {"id": fila["id"], "apunte_id": fila["apunte_id"], "version": fila["version"],
            "opciones": json.loads(fila["opciones"]), "estado": fila["estado"], "trabajo_id": fila["trabajo_id"],
            "sha256": fila["sha256"], "tamano": fila["tamano"], "paginas": fila["paginas_pdf"],
            "creado": fila["creado"], "actualizado": fila["actualizado"],
            "descarga": f"/api/v2/exportaciones/{fila['id']}/pdf" if fila["estado"] == "completado" else None}


def obtener(usuario_id: str, exportacion_id: str):
    fila = contexto.obtener().bd.uno("SELECT * FROM exportaciones WHERE id = ? AND usuario_id = ?",
                                     (exportacion_id, usuario_id))
    if fila is None:
        raise ApiError(404, "NO_ENCONTRADO", "No encontramos esa exportación.")
    return fila


def solicitar(usuario_id: str, apunte_id: str, version: int | None, opciones: OpcionesPDF) -> tuple[dict, dict | None, bool]:
    """→ (exportación, trabajo, creada). Reutiliza la existente si ya está hecha o en curso."""
    ctx = contexto.obtener()
    repo = RepositorioApuntes(ctx.bd, ctx.almacen)
    apunte = repo.obtener(usuario_id, apunte_id, con_documento=False)
    if apunte["estado"] in ("pendiente", "procesando"):
        raise ApiError(409, "APUNTE_EN_PROCESO", "Espera a que termine el análisis antes de exportar.")
    version = version or apunte["version"]
    repo.documento(usuario_id, apunte_id, version)  # 404 si la versión no existe
    existente = ctx.bd.uno("SELECT * FROM exportaciones WHERE apunte_id = ? AND version = ? AND clave = ?",
                           (apunte_id, version, opciones.clave))
    if existente is not None:
        valida = existente["estado"] == "completado" and existente["archivo_id"]
        en_curso = existente["estado"] == "pendiente"
        if valida or en_curso:
            trabajo = (ctx.trabajos.obtener(usuario_id, existente["trabajo_id"])
                       if existente["trabajo_id"] and en_curso else None)
            return publica(existente), trabajo, False
        # fallida o cancelada: se vuelve a intentar con la misma fila
        ctx.bd.ejecutar("DELETE FROM exportaciones WHERE id = ?", (existente["id"],))
    eid = secrets.token_hex(16)
    ctx.bd.ejecutar("INSERT INTO exportaciones (id, apunte_id, usuario_id, version, opciones, clave, estado, creado, "
                    "actualizado) VALUES (?, ?, ?, ?, ?, ?, 'pendiente', ?, ?)",
                    (eid, apunte_id, usuario_id, version, json.dumps(opciones.__dict__), opciones.clave, ahora(), ahora()))
    try:
        trabajo = ctx.trabajos.encolar(usuario_id, "exportacion", apunte_id, {"exportacion_id": eid})
    except ApiError:
        ctx.bd.ejecutar("DELETE FROM exportaciones WHERE id = ?", (eid,))
        raise
    ctx.bd.ejecutar("UPDATE exportaciones SET trabajo_id = ? WHERE id = ?", (trabajo["id"], eid))
    return publica(obtener(usuario_id, eid)), trabajo, True


def _marcar(eid: str, estado: str, **campos) -> None:
    sets = ", ".join(f"{k} = ?" for k in campos)
    contexto.obtener().bd.ejecutar(f"UPDATE exportaciones SET estado = ?, actualizado = ?{', ' + sets if sets else ''} "
                                   "WHERE id = ?", (estado, ahora(), *campos.values(), eid))


def manejar_exportacion(trabajo: Trabajo) -> Resultado:
    ctx = contexto.obtener()
    eid = trabajo.parametros["exportacion_id"]
    fila = obtener(trabajo.usuario_id, eid)
    repo = RepositorioApuntes(ctx.bd, ctx.almacen)
    trabajo.avance("estructurando", 10)
    doc = repo.documento(trabajo.usuario_id, trabajo.apunte_id, fila["version"])
    opciones = OpcionesPDF(**json.loads(fila["opciones"]))
    trabajo.avance("maquetando", 30)
    inicio = time.monotonic()
    try:
        datos, paginas = generar_pdf(doc, estructurar(doc), fila["version"],
                                     lambda archivo: ctx.almacen.leer(trabajo.usuario_id, archivo), opciones)
    except ErrorPDF as exc:
        _marcar(eid, "fallido")
        raise ErrorTrabajo(exc.codigo, exc.mensaje) from None
    except Exception:
        _marcar(eid, "fallido")
        raise
    trabajo.avance("maquetando", 95)
    archivo = ctx.almacen.guardar(trabajo.usuario_id, datos, "pdf", "application/pdf", trabajo.apunte_id)
    sha = ctx.bd.uno("SELECT sha256 FROM archivos WHERE id = ?", (archivo,))["sha256"]
    _marcar(eid, "completado", archivo_id=archivo, sha256=sha, tamano=len(datos), paginas_pdf=paginas)
    logger.info("PDF generado (exportacion=%s): %d páginas, %d KB, %.0f ms", eid, paginas, len(datos) // 1024,
                (time.monotonic() - inicio) * 1000)
    return Resultado("completado", {"exportacion_id": eid, "paginas": paginas, "tamano": len(datos), "sha256": sha})


def al_cancelar(trabajo: Trabajo) -> None:
    _marcar(trabajo.parametros["exportacion_id"], "cancelado")


@contexto.al_iniciar
def _registrar(ctx) -> None:
    ctx.trabajos.registrar("exportacion", manejar_exportacion, al_cancelar=al_cancelar)
