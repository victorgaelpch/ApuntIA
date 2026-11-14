"""Análisis de una imagen con el modelo visual local (BACK-35).

Flujo: validar → diagnosticar calidad → esperar turno (máx. IA_MAX_INFERENCIAS a la vez) →
inferencia (prompt corto, texto plano) → el servidor construye y valida el resultado → contrato v1.

Ante falta de memoria de la GPU se prueba UNA vez el modelo de respaldo (4B) si está instalado;
si no, el error vuelve como SIN_MEMORIA reintentable. Nada se guarda en disco: la imagen vive
solo en memoria durante la petición.

Lo que devuelve el modelo es siempre una PROPUESTA para revisar (`revision_requerida: true`):
un VLM no da confianza calibrada, así que no se inventa ningún porcentaje.
"""

from __future__ import annotations

import base64
import logging
import shutil
import threading
import time
from pathlib import Path

import cv2

from ia_servidor import API_VERSION, PIPELINE_VERSION, compartido, gpu
from ia_servidor.config import Configuracion
from ia_servidor.errores import ErrorIA
from ia_servidor.esquemas import TAREAS, TAREAS_PUBLICAS, construir, prompt
from ia_servidor.segmentacion import regiones_opencv
from ia_servidor.imagen import reducir, validar
from ia_servidor.ollama import VERSION_MINIMA, ClienteOllama, version_tupla

logger = logging.getLogger("apuntia.ia")


class Servicio:
    def __init__(self, config: Configuracion, ollama: ClienteOllama, leer_gpu=gpu.leer,
                 carpeta_modelos: Path | None = None):
        self.config = config
        self.ollama = ollama
        self.leer_gpu = leer_gpu
        self.carpeta_modelos = carpeta_modelos or Path.home() / ".ollama"
        self._turnos = threading.BoundedSemaphore(config.max_inferencias)

    # ------------------------------------------------------------------ estado
    def capacidades(self) -> dict:
        c = self.config
        return {
            "api_version": API_VERSION, "pipeline_version": PIPELINE_VERSION,
            "tareas": TAREAS_PUBLICAS, "formatos": list(c.formatos),
            "limites": {"max_mb": c.max_mb, "max_megapixeles": c.max_megapixeles,
                        "max_lado_enviado_al_modelo": c.max_lado_modelo, "inferencias_simultaneas": c.max_inferencias,
                        "espera_maxima_en_cola_s": c.espera_cola_s, "timeout_inferencia_s": c.timeout_s},
            "modelo": {"principal": c.modelo, "respaldo": c.modelo_respaldo or None},
            "almacenamiento": "ninguno: las imágenes solo existen en memoria durante la petición",
            "envio": "POST /api/v1/analisis?tarea=<tarea> con el cuerpo binario de la imagen (Content-Type image/*)",
        }

    def listo(self) -> tuple[bool, dict]:
        componentes: dict = {}
        avisos: list[str] = []
        ok = True
        try:
            version = self.ollama.version()
            componentes["ollama"] = {"ok": version_tupla(version) >= VERSION_MINIMA, "version": version}
            if not componentes["ollama"]["ok"]:
                componentes["ollama"]["detalle"] = "se necesita Ollama 0.12.7 o superior para Qwen3-VL"
            instalados = self.ollama.modelos()
            principal = self.config.modelo in instalados
            componentes["modelo"] = {"ok": principal, "nombre": self.config.modelo,
                                     **({"detalle": f"instálalo con «ollama pull {self.config.modelo}»"} if not principal
                                        else instalados[self.config.modelo])}
            if principal and "vision" not in self.ollama.capacidades(self.config.modelo):
                componentes["modelo"].update(ok=False, detalle="el modelo no declara la capacidad «vision»")
            if self.config.modelo_respaldo:
                componentes["modelo_respaldo"] = {"instalado": self.config.modelo_respaldo in instalados,
                                                  "nombre": self.config.modelo_respaldo}
            componentes["en_memoria"] = self.ollama.cargados()
        except ErrorIA as e:
            componentes.setdefault("ollama", {"ok": False, "codigo": e.codigo, "detalle": e.detalle})
        ok = all(c.get("ok") for k, c in componentes.items() if k in ("ollama", "modelo")) and "modelo" in componentes
        libre_mb = self._disco_libre_mb()
        componentes["disco"] = {"ok": libre_mb is None or libre_mb >= self.config.min_disco_mb, "libre_mb": libre_mb}
        ok = ok and componentes["disco"]["ok"]
        componentes["gpu"] = self.leer_gpu()
        if not componentes["gpu"].get("disponible"):
            avisos.append("sin GPU NVIDIA detectada: Ollama usará la CPU y será mucho más lento")
        componentes["cola"] = {"inferencias_simultaneas": self.config.max_inferencias}
        return ok, {"listo": ok, "api_version": API_VERSION, "componentes": componentes, "avisos": avisos}

    def _disco_libre_mb(self) -> int | None:
        carpeta = self.carpeta_modelos if self.carpeta_modelos.exists() else Path.home()
        try:
            return shutil.disk_usage(carpeta).free // (1024 * 1024)
        except OSError:
            return None

    # ------------------------------------------------------------------ análisis
    def _b64(self, imagen) -> tuple[str, int]:
        enviada = reducir(imagen, self.config.max_lado_modelo)
        ok, png = cv2.imencode(".png", enviada)
        if not ok:
            raise ErrorIA("IMAGEN_CORRUPTA", "no se pudo codificar para el modelo")
        return base64.b64encode(png.tobytes()).decode("ascii"), int(max(enviada.shape[:2]))

    def _con_respaldo(self, estado: dict, tarea: str, imagen_b64: str):
        """Inferencia con el modelo vigente; ante falta de VRAM pasa UNA vez al de respaldo y lo
        mantiene para el resto del documento. `estado`: {"modelo", "respaldo_usado"}."""
        try:
            return self._inferir(estado["modelo"], tarea, imagen_b64)
        except ErrorIA as e:
            if (e.codigo != "SIN_MEMORIA" or estado["respaldo_usado"] or not self.config.modelo_respaldo
                    or self.config.modelo_respaldo not in self.ollama.modelos()):
                raise
            logger.warning("ia: sin memoria con %s; se reintenta con %s", estado["modelo"], self.config.modelo_respaldo)
            estado.update(modelo=self.config.modelo_respaldo, respaldo_usado=True)
            return self._inferir(estado["modelo"], tarea, imagen_b64)

    def analizar(self, datos: bytes, tarea: str, id_correlacion: str, progreso=None) -> dict:
        inicio = time.perf_counter()
        if tarea not in TAREAS_PUBLICAS:
            raise ErrorIA("TAREA_INVALIDA", tarea[:40])
        img = validar(datos, self.config.max_mb, self.config.max_megapixeles)
        calidad = compartido.diagnosticar(img.imagen)
        if tarea == "documento":
            return self._documento(img, calidad, id_correlacion, inicio, progreso)
        imagen_b64, lado = self._b64(img.imagen)

        if not self._turnos.acquire(timeout=self.config.espera_cola_s):
            raise ErrorIA("OCUPADO", "cola llena")
        try:
            estado = {"modelo": self.config.modelo, "respaldo_usado": False}
            salida, stats = self._con_respaldo(estado, tarea, imagen_b64)
            modelo, respaldo_usado = estado["modelo"], estado["respaldo_usado"]
        finally:
            self._turnos.release()

        total = round(time.perf_counter() - inicio, 2)
        logger.info("ia: id=%s tarea=%s modelo=%s bytes=%d lado=%d segundos=%s tokens=%s ilegible=%s caracteres=%d",
                    id_correlacion, tarea, modelo, img.bytes, lado, total,
                    stats.get("tokens_salida"), salida.ilegible, len(salida.texto))  # métricas, nunca contenido
        return {
            "api_version": API_VERSION, "pipeline_version": PIPELINE_VERSION, "id_correlacion": id_correlacion,
            "tarea": tarea,
            "modelo": {"nombre": modelo, "respaldo_usado": respaldo_usado},
            "imagen": {"formato": img.formato, "ancho": img.ancho, "alto": img.alto, "bytes": img.bytes,
                       "lado_enviado_al_modelo": lado},
            "calidad": calidad,
            "resultado": {
                "estado": "ilegible" if salida.ilegible else "propuesta",
                "revision_requerida": True, "origen": "imagen",
                "texto": salida.texto, "latex": salida.latex, "descripcion": salida.descripcion,
                "dudas": salida.dudas,
            },
            "metricas": {"segundos_total": total, **stats},
        }

    # ------------------------------------------------------------------ documento por regiones (BACK-36)
    def _documento(self, img, calidad: dict, id_correlacion: str, inicio: float, progreso=None) -> dict:
        """Segmenta la página (OpenCV, sin GPU) y lee cada región por separado: medido, conserva lo
        escrito mucho mejor que enviar la página entera (evaluacion-multimodal.md §5). Devuelve
        bloques compatibles con el editor (id p1bN, orden, tipo, bbox en píxeles del original)."""
        regiones = regiones_opencv(img.imagen, hueco_lineas=self.config.seg_hueco_lineas)[: self.config.max_regiones]
        if not self._turnos.acquire(timeout=self.config.espera_cola_s):
            raise ErrorIA("OCUPADO", "cola llena")
        bloques, tokens, segundos_modelo = [], 0, 0.0
        estado = {"modelo": self.config.modelo, "respaldo_usado": False}
        try:
            for n, r in enumerate(regiones, 1):
                x0, y0, x1, y1 = r.bbox
                b64, _ = self._b64(img.imagen[y0:y1, x0:x1])
                try:
                    salida, stats = self._con_respaldo(estado, "region", b64)
                except ErrorIA as e:
                    # Una región con respuesta inválida (cortada, desbocada) no tumba el documento: queda
                    # «no reconocida» con su recorte para escribirla a mano. Ollama caído, GPU sin
                    # memoria o modelo ausente sí detienen todo (afectarían a las demás regiones).
                    if e.codigo not in ("RESPUESTA_INVALIDA", "IMAGEN_CORRUPTA"):
                        raise
                    logger.warning("ia: id=%s región %d sin respuesta válida (%s)", id_correlacion, n, e.codigo)
                    bloques.append({"id": f"p1b{n}", "pagina": "p1", "orden": n, "tipo": "manuscrito", "bbox": [x0, y0, x1, y1],
                                    "origen": "ocr", "estado": "no_reconocido", "texto": "", "latex": None, "descripcion": None,
                                    "dudas": ["el modelo no dio una respuesta válida para esta región: revísala en el recorte"],
                                    "procedencia": {"motor": "ollama", "version": estado["modelo"],
                                                    "reconocimiento": f"documento/{r.origen}"}})
                    continue
                if progreso:
                    progreso(n, len(regiones))
                tokens += stats.get("tokens_salida") or 0
                segundos_modelo += stats.get("segundos_modelo") or 0
                if salida.ilegible:
                    tipo, estado_b = "manuscrito", "no_reconocido"
                elif salida.descripcion and not salida.texto:
                    tipo, estado_b = "imagen", "reconocido"
                else:
                    tipo = "formula" if salida.latex else "texto"
                    estado_b = "incierto" if salida.dudas else "reconocido"
                bloques.append({"id": f"p1b{n}", "pagina": "p1", "orden": n, "tipo": tipo, "bbox": [x0, y0, x1, y1],
                                "origen": "ocr", "estado": estado_b, "texto": salida.texto, "latex": salida.latex,
                                "descripcion": salida.descripcion, "dudas": salida.dudas,
                                "procedencia": {"motor": "ollama", "version": estado["modelo"],
                                                "reconocimiento": f"documento/{r.origen}"}})
        finally:
            self._turnos.release()
        total = round(time.perf_counter() - inicio, 2)
        logger.info("ia: id=%s tarea=documento modelo=%s bytes=%d regiones=%d segundos=%s tokens=%d",
                    id_correlacion, estado["modelo"], img.bytes, len(bloques), total, tokens)
        texto = "\n".join(b["latex"] or b["texto"] or ("DIBUJO: " + (b["descripcion"] or "")) for b in bloques)
        return {
            "api_version": API_VERSION, "pipeline_version": PIPELINE_VERSION, "id_correlacion": id_correlacion,
            "tarea": "documento", "modelo": {"nombre": estado["modelo"], "respaldo_usado": estado["respaldo_usado"]},
            "imagen": {"formato": img.formato, "ancho": img.ancho, "alto": img.alto, "bytes": img.bytes,
                       "lado_enviado_al_modelo": None},
            "calidad": calidad,
            "resultado": {"estado": "propuesta" if bloques else "ilegible", "revision_requerida": True, "origen": "imagen",
                          "texto": texto, "latex": None, "descripcion": None,
                          "dudas": [d for b in bloques for d in b["dudas"]], "bloques": bloques,
                          "segmentacion": {"metodo": "opencv", "regiones": len(bloques),
                                           "hueco_lineas": self.config.seg_hueco_lineas}},
            "metricas": {"segundos_total": total, "tokens_salida": tokens, "segundos_modelo": round(segundos_modelo, 2)},
        }

    def _inferir(self, modelo: str, tarea: str, imagen_b64: str):
        # Prompt de una línea y respuesta en texto plano: el servidor construye la estructura (§8).
        mensajes = [{"role": "user", "content": prompt(tarea), "images": [imagen_b64]}]
        r = self.ollama.chat(modelo, mensajes, None, self.config.keep_alive, self.config.timeout_s,
                             self.config.num_ctx, self.config.max_tokens)
        salida = construir(tarea, r["contenido"])
        if salida is None:
            raise ErrorIA("RESPUESTA_INVALIDA", "respuesta del modelo fuera de los límites")
        stats = {k: v for k, v in r.items() if k != "contenido"}
        return salida, stats
