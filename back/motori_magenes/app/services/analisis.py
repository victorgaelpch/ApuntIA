"""Trabajo de análisis de un apunte: fotos → documento editable (BACK-21).

Para cada página, en orden:
  preprocesado por perfil (BACK-12) → OCR por bloques (BACK-13) → respaldo de
  manuscritos (BACK-14) → fórmulas a LaTeX (BACK-15) → recortes privados →
  bloques del documento (BACK-17).

Estados finales:
  - completado: todas las páginas se analizaron;
  - parcial: alguna página falló; el documento tiene las demás y la página
    fallida lleva `error`. Nunca es un «completado» con contenido fingido;
  - fallido: ninguna página se pudo analizar, o el OCR no está disponible
    (OCR_NO_DISPONIBLE): un fallo técnico no se disfraza de «sin texto».
Al cancelar se borran los archivos intermedios (procesadas y recortes).
"""

import logging
import threading

import cv2
import numpy as np

from app.core import contexto
from app.core.config import settings
from app.datos.apuntes import RepositorioApuntes
from app.services.documento import Bloque, Documento
from app.services.formulas import separar_formulas
from app.services.manuscrito import leer_con_respaldo
from app.services.ocr import ErrorOCR, reconocer
from app.services.preprocesado_ocr import preprocesar_para_ocr
from app.services.trabajos import ErrorTrabajo, Resultado, Trabajo

logger = logging.getLogger("apuntia.analisis")

MARGEN_RECORTE = 10
_creados: dict[str, list[tuple[str, str]]] = {}   # trabajo → [(usuario, archivo)] para limpiar al cancelar
_bloqueo = threading.Lock()


def _png(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise ErrorTrabajo("ERROR_PROCESAMIENTO", "No se pudo guardar una imagen procesada.")
    return buf.tobytes()


def _jpeg(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if not ok:
        raise ErrorTrabajo("ERROR_PROCESAMIENTO", "No se pudo guardar una imagen procesada.")
    return buf.tobytes()


def _recorte(img: np.ndarray, bbox: list[int]) -> np.ndarray:
    alto, ancho = img.shape[:2]
    x0, y0, x1, y1 = bbox
    return img[max(0, y0 - MARGEN_RECORTE):min(alto, y1 + MARGEN_RECORTE),
               max(0, x0 - MARGEN_RECORTE):min(ancho, x1 + MARGEN_RECORTE)]


def _guardar(trabajo: Trabajo, datos: bytes, tipo: str, mime: str) -> str:
    ctx = contexto.obtener()
    archivo = ctx.almacen.guardar(trabajo.usuario_id, datos, tipo, mime, trabajo.apunte_id)
    with _bloqueo:
        _creados.setdefault(trabajo.id, []).append((trabajo.usuario_id, archivo))
    return archivo


def analizar_pagina(trabajo: Trabajo, pagina, idiomas: str) -> tuple[dict, list[Bloque]]:
    ctx = contexto.obtener()
    datos = ctx.almacen.leer(trabajo.usuario_id, pagina.archivo_original)
    imagen = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
    if imagen is None:
        raise ErrorTrabajo("IMAGEN_CORRUPTA", "La foto no se pudo leer.")
    pre = preprocesar_para_ocr(imagen, pagina.tipo_fuente)
    bloques_ocr = reconocer(pre.imagen_ocr, idiomas=idiomas, psm=pre.psm)
    bloques_ocr = leer_con_respaldo(pre.imagen_ocr, bloques_ocr, idiomas)
    bloques_ocr = separar_formulas(bloques_ocr)

    procesada = _guardar(trabajo, _jpeg(pre.imagen_vista), "procesada", "image/jpeg")
    alto, ancho = pre.imagen_vista.shape[:2]
    bloques = []
    for n, b in enumerate(bloques_ocr, start=1):
        recorte = _guardar(trabajo, _png(_recorte(pre.imagen_vista, b.bbox)), "recorte", "image/png") \
            if b.recortar or b.tipo in ("imagen", "manuscrito", "formula") else None
        estado = b.estado if b.texto else "no_reconocido"
        tipo = b.tipo if b.tipo in ("titulo", "texto", "manuscrito", "formula", "imagen") else "texto"
        latex = getattr(b, "latex", None)
        bloques.append(Bloque(
            id=f"{pagina.id}b{n}", pagina=pagina.id, orden=0, tipo=tipo, bbox=b.bbox, origen="ocr",
            estado=estado, confianza=round(b.confianza, 3), texto=b.texto, texto_original=b.texto,
            latex=latex, latex_original=latex, latex_valido=getattr(b, "latex_valido", None),
            recorte=recorte, palabras_dudosas=b.dudosas[:200],
            conservar_imagen=tipo in ("imagen", "manuscrito") and not b.texto))
    cambios = {"archivo_procesado": procesada, "ancho": ancho, "alto": alto,
               "advertencias": pre.advertencias, "error": None}
    return cambios, bloques


def manejar_analisis(trabajo: Trabajo) -> Resultado:
    ctx = contexto.obtener()
    repo = RepositorioApuntes(ctx.bd, ctx.almacen)
    repo.cambiar_estado(trabajo.apunte_id, "procesando")
    doc = repo.documento(trabajo.usuario_id, trabajo.apunte_id)
    idiomas = trabajo.parametros.get("idiomas") or settings.ocr_idiomas
    paginas, bloques, fallidas = [], [], []
    total = len(doc.paginas)
    for i, pagina in enumerate(sorted(doc.paginas, key=lambda p: p.orden)):
        trabajo.avance("ocr", int(5 + 85 * i / max(1, total)))
        try:
            cambios, nuevos = analizar_pagina(trabajo, pagina, idiomas)
            paginas.append(pagina.model_copy(update=cambios))
            bloques += nuevos
        except ErrorOCR as exc:
            if exc.codigo in ("OCR_NO_DISPONIBLE", "OCR_IDIOMA_NO_DISPONIBLE"):
                repo.cambiar_estado(trabajo.apunte_id, "fallido")
                raise ErrorTrabajo(exc.codigo, exc.mensaje) from None
            fallidas.append(pagina.orden)
            paginas.append(pagina.model_copy(update={"error": exc.mensaje}))
        except ErrorTrabajo as exc:
            fallidas.append(pagina.orden)
            paginas.append(pagina.model_copy(update={"error": exc.mensaje}))
        except Exception:  # noqa: BLE001 — una página no debe tumbar las demás
            logger.exception("Falló el análisis de una página (trabajo=%s)", trabajo.id)
            fallidas.append(pagina.orden)
            paginas.append(pagina.model_copy(update={"error": "No se pudo analizar esta página."}))

    trabajo.avance("estructurando", 95)
    for orden, b in enumerate(bloques):
        b.orden = orden
    nuevo = Documento(titulo=doc.titulo, paginas=paginas, bloques=bloques, ampliaciones=doc.ampliaciones)
    if len(fallidas) == total:
        repo.cambiar_estado(trabajo.apunte_id, "fallido")
        raise ErrorTrabajo("ANALISIS_FALLIDO", "No se pudo analizar ninguna página. Prueba con fotos más nítidas.")
    estado = "parcial" if fallidas else "listo"
    version = repo.nueva_version(trabajo.usuario_id, trabajo.apunte_id, nuevo, "analisis", estado=estado)
    with _bloqueo:
        _creados.pop(trabajo.id, None)
    resumen = {"version": version, "bloques": len(bloques), "paginas_fallidas": fallidas,
               "inciertos": sum(b.estado == "incierto" for b in bloques),
               "no_reconocidos": sum(b.estado == "no_reconocido" for b in bloques)}
    if fallidas:
        return Resultado("parcial", resumen,
                         f"No se pudo analizar la página {', '.join(map(str, fallidas))}; el resto está listo.")
    return Resultado("completado", resumen)


def limpiar_cancelado(trabajo: Trabajo) -> None:
    ctx = contexto.obtener()
    with _bloqueo:
        creados = _creados.pop(trabajo.id, [])
    for usuario, archivo in creados:
        try:
            ruta = ctx.almacen.obtener(usuario, archivo).ruta
            ruta.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass
        ctx.bd.ejecutar("DELETE FROM archivos WHERE id = ?", (archivo,))
    RepositorioApuntes(ctx.bd, ctx.almacen).cambiar_estado(trabajo.apunte_id, "cancelado")


@contexto.al_iniciar
def _registrar(ctx) -> None:
    ctx.trabajos.registrar("analisis", manejar_analisis, al_cancelar=limpiar_cancelado)
