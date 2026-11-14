"""Análisis de páginas con el servidor IA remoto dentro del trabajo «analisis» (BACK-37, BACK-38).

El trabajo durable de siempre (app/services/trabajos.py) sigue siendo la fuente de verdad del
progreso, la cancelación y la recuperación tras reinicio. Para cada página con motor «ia_remota»:

1. Clave idempotente = usuario + apunte + página + foto original + versión del pipeline.
2. Si `ia_resultados` ya tiene el resultado validado → se reutiliza (ni red ni GPU).
3. Si tiene un `trabajo_remoto` de un intento anterior → se retoma por su id.
4. Si no → se envía a la cola del servidor IA y se guarda el id antes de esperar.
5. Los bloques remotos se convierten al modelo del editor: bbox sobre la foto ORIGINAL, recorte de
   cada región (para revisar contra la fuente), LaTeX validado con el mismo motor del editor y
   `revision="sin_confirmar"`: un VLM no da confianza calibrada, todo es una propuesta para revisar.

Errores del servidor IA → códigos públicos AI_* (ia_remota.codigo_publico). Nunca se cambia en
silencio al reconocimiento local: con motor «auto» sin vinculación se usa el local y se AVISA.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone

import cv2
import numpy as np

from app.core import contexto
from app.core.config import settings
from app.datos.bd import ahora
from app.services.documento import Bloque, Procedencia
from app.services.ia_remota import Almacen, ClienteIARemota, ErrorIARemota, codigo_publico
from app.services.trabajos import Cancelado, ErrorTrabajo, Trabajo

logger = logging.getLogger("apuntia.analisis_remoto")
PIPELINE = "documento/1.2"
RETENCION_DIAS = 7


class ErrorIATrabajo(ErrorTrabajo):
    """Fallo del servidor IA: detiene TODO el trabajo (las demás páginas fallarían igual)."""


def cliente() -> ClienteIARemota:
    almacen = Almacen(contexto.obtener().data_dir)
    url = almacen.leer().get("url") or settings.ia_url
    return ClienteIARemota(url, almacen, timeout_s=settings.ia_timeout_s, timeout_analisis_s=settings.ia_timeout_analisis_s)


def resolver_motor(pedido: str) -> tuple[str, str | None]:
    """(motor efectivo, aviso). «auto» usa el servidor IA solo si este equipo está vinculado."""
    if pedido not in ("ia_remota", "auto"):
        return "local", None
    vinculado = cliente().estado()["vinculado"]
    if vinculado:
        return "ia_remota", None
    if pedido == "auto":
        return "local", "Este equipo no está vinculado con el servidor IA: se usó el reconocimiento local."
    codigo, mensaje = codigo_publico(ErrorIARemota("AI_NO_VINCULADO", ""))
    raise ErrorIATrabajo(codigo, mensaje)


def clave(trabajo: Trabajo, pagina) -> str:
    base = f"{trabajo.usuario_id}|{trabajo.apunte_id}|{pagina.id}|{pagina.archivo_original}|{PIPELINE}"
    return hashlib.sha256(base.encode()).hexdigest()[:48]


def purgar(bd, usuario_id: str) -> None:
    limite = (datetime.now(timezone.utc) - timedelta(days=RETENCION_DIAS)).isoformat()
    bd.ejecutar("DELETE FROM ia_resultados WHERE usuario_id = ? AND actualizado < ?", (usuario_id, limite))


def _validar_latex(latex: str) -> bool | None:
    from app.services.formulas import validar_latex
    lineas = [l for l in latex.splitlines() if l.strip()]
    return all(validar_latex(l)[0] for l in lineas) if lineas else None


def obtener_resultado(trabajo: Trabajo, pagina, datos: bytes, c: ClienteIARemota) -> dict:
    ctx = contexto.obtener()
    bd, k = ctx.bd, clave(trabajo, pagina)
    fila = bd.uno("SELECT * FROM ia_resultados WHERE clave = ?", (k,))
    if fila and fila["estado"] == "completado" and fila["resultado"]:
        logger.info("trabajo=%s página=%s: resultado IA reutilizado (sin GPU)", trabajo.id[:8], pagina.id)
        return json.loads(fila["resultado"])

    def guardar_id(tid: str) -> None:
        bd.ejecutar("INSERT INTO ia_resultados (clave, usuario_id, apunte_id, pagina_id, trabajo_remoto, estado, creado, "
                    "actualizado) VALUES (?, ?, ?, ?, ?, 'enviado', ?, ?) ON CONFLICT(clave) DO UPDATE SET "
                    "trabajo_remoto = excluded.trabajo_remoto, actualizado = excluded.actualizado",
                    (k, trabajo.usuario_id, trabajo.apunte_id, pagina.id, tid, ahora(), ahora()))

    def cancelado() -> bool:
        f = bd.uno("SELECT cancelar FROM trabajos WHERE id = ?", (trabajo.id,))
        return f is None or bool(f["cancelar"])

    def al_avance(estado, progreso, posicion) -> None:
        etapa = "ia_en_cola" if estado == "en_cola" else "ia_procesando"
        try:
            trabajo.avance(etapa, int(5 + 0.85 * progreso))
        except Cancelado:
            pass  # lo detecta `cancelado()` en la siguiente consulta y cancela también en el servidor

    try:
        resultado = c.analizar_trabajo(datos, "documento", k, fila["trabajo_remoto"] if fila else None,
                                       guardar_id=guardar_id, cancelado=cancelado, al_avance=al_avance,
                                       max_espera_s=settings.ia_timeout_analisis_s * 4)
    except ErrorIARemota as e:
        if e.codigo == "AI_CANCELADO":
            raise Cancelado() from None
        codigo, mensaje = codigo_publico(e)
        logger.warning("trabajo=%s página=%s: servidor IA %s (%s)", trabajo.id[:8], pagina.id, codigo, e.codigo)
        raise ErrorIATrabajo(codigo, mensaje) from None
    if not isinstance(resultado.get("resultado", {}).get("bloques"), list):
        codigo, mensaje = codigo_publico(ErrorIARemota("AI_RESPUESTA", ""))
        raise ErrorIATrabajo(codigo, mensaje)
    bd.ejecutar("UPDATE ia_resultados SET estado = 'completado', resultado = ?, actualizado = ? WHERE clave = ?",
                (json.dumps(resultado, ensure_ascii=False), ahora(), k))
    return resultado


def analizar_pagina_remota(trabajo: Trabajo, pagina, guardar, c: ClienteIARemota) -> tuple[dict, list[Bloque]]:
    """Igual que analisis.analizar_pagina, pero con el servidor IA. `guardar(datos, tipo, mime)`."""
    ctx = contexto.obtener()
    datos = ctx.almacen.leer(trabajo.usuario_id, pagina.archivo_original)
    imagen = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
    if imagen is None:
        raise ErrorTrabajo("IMAGEN_CORRUPTA", "La foto no se pudo leer.")
    respuesta = obtener_resultado(trabajo, pagina, datos, c)
    alto, ancho = imagen.shape[:2]
    vista = guardar(cv2.imencode(".jpg", imagen, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes(), "procesada", "image/jpeg")
    modelo = str((respuesta.get("modelo") or {}).get("nombre", ""))[:40]
    bloques = []
    for n, b in enumerate(respuesta["resultado"]["bloques"], start=1):
        x0, y0, x1, y1 = (max(0, int(v)) for v in b["bbox"])
        x1, y1 = min(ancho, max(x0 + 1, x1)), min(alto, max(y0 + 1, y1))
        recorte = guardar(cv2.imencode(".png", imagen[y0:y1, x0:x1])[1].tobytes(), "recorte", "image/png")
        tipo = b.get("tipo") if b.get("tipo") in ("titulo", "texto", "manuscrito", "formula", "imagen") else "texto"
        estado = b.get("estado") if b.get("estado") in ("reconocido", "incierto", "no_reconocido") else "incierto"
        texto = (b.get("texto") or b.get("descripcion") or "")[:20000]
        latex = b.get("latex") if b.get("latex") and len(b["latex"]) <= 2000 else None
        if b.get("latex") and latex is None:
            estado = "incierto"  # LaTeX demasiado largo para el editor: queda solo como texto
        bloques.append(Bloque(
            id=f"{pagina.id}b{n}", pagina=pagina.id, orden=0, tipo=tipo, bbox=[x0, y0, x1, y1], origen="ocr",
            estado=estado, confianza=None, texto=texto, texto_original=texto, latex=latex, latex_original=latex,
            latex_valido=_validar_latex(latex) if latex else None, recorte=recorte,
            palabras_dudosas=[d[:200] for d in (b.get("dudas") or [])][:200],
            conservar_imagen=tipo == "imagen" or estado == "no_reconocido",
            procedencia=Procedencia(motor="ia_remota", version=modelo,
                                    reconocimiento=str((b.get("procedencia") or {}).get("reconocimiento", PIPELINE))[:40]),
            revision="sin_confirmar" if estado != "no_reconocido" else None))
    cambios = {"archivo_procesado": vista, "ancho": ancho, "alto": alto, "error": None,
               "advertencias": [f"Transcripción propuesta por el servidor IA ({modelo}): revísala contra cada recorte."]}
    return cambios, bloques
