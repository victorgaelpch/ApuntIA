"""Análisis de una imagen con el modelo visual local (BACK-35).

Flujo: validar → diagnosticar calidad → esperar turno (máx. IA_MAX_INFERENCIAS a la vez) →
inferencia → validar el JSON (un único reintento pidiendo solo JSON) → respuesta del contrato v1.

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
from ia_servidor.esquemas import ESQUEMA_MODELO, PROMPT_BASE, PROMPT_REPARAR, TAREAS, interpretar
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
            "tareas": sorted(TAREAS), "formatos": list(c.formatos),
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
    def analizar(self, datos: bytes, tarea: str, id_correlacion: str) -> dict:
        inicio = time.perf_counter()
        if tarea not in TAREAS:
            raise ErrorIA("TAREA_INVALIDA", tarea[:40])
        img = validar(datos, self.config.max_mb, self.config.max_megapixeles)
        calidad = compartido.diagnosticar(img.imagen)
        enviada = reducir(img.imagen, self.config.max_lado_modelo)
        ok, png = cv2.imencode(".png", enviada)
        if not ok:
            raise ErrorIA("IMAGEN_CORRUPTA", "no se pudo codificar para el modelo")
        imagen_b64 = base64.b64encode(png.tobytes()).decode("ascii")
        del png

        if not self._turnos.acquire(timeout=self.config.espera_cola_s):
            raise ErrorIA("OCUPADO", "cola llena")
        try:
            modelo, respaldo_usado = self.config.modelo, False
            try:
                salida, stats = self._inferir(modelo, tarea, imagen_b64)
            except ErrorIA as e:
                if e.codigo != "SIN_MEMORIA" or not self.config.modelo_respaldo:
                    raise
                if self.config.modelo_respaldo not in self.ollama.modelos():
                    raise
                logger.warning("ia: sin memoria con %s; se reintenta con %s", modelo, self.config.modelo_respaldo)
                modelo, respaldo_usado = self.config.modelo_respaldo, True
                salida, stats = self._inferir(modelo, tarea, imagen_b64)
        finally:
            self._turnos.release()

        total = round(time.perf_counter() - inicio, 2)
        logger.info("ia: id=%s tarea=%s modelo=%s bytes=%d lado=%d segundos=%s tokens=%s ilegible=%s caracteres=%d",
                    id_correlacion, tarea, modelo, img.bytes, max(enviada.shape[:2]), total,
                    stats.get("tokens_salida"), salida.ilegible, len(salida.texto))  # métricas, nunca contenido
        return {
            "api_version": API_VERSION, "pipeline_version": PIPELINE_VERSION, "id_correlacion": id_correlacion,
            "tarea": tarea,
            "modelo": {"nombre": modelo, "respaldo_usado": respaldo_usado},
            "imagen": {"formato": img.formato, "ancho": img.ancho, "alto": img.alto, "bytes": img.bytes,
                       "lado_enviado_al_modelo": int(max(enviada.shape[:2]))},
            "calidad": calidad,
            "resultado": {
                "estado": "ilegible" if salida.ilegible else "propuesta",
                "revision_requerida": True, "origen": "imagen",
                "texto": salida.texto, "latex": salida.latex, "descripcion": salida.descripcion,
                "dudas": salida.dudas,
            },
            "metricas": {"segundos_total": total, **stats},
        }

    def _inferir(self, modelo: str, tarea: str, imagen_b64: str):
        mensajes = [{"role": "user", "content": PROMPT_BASE + "Tarea: " + TAREAS[tarea], "images": [imagen_b64]}]
        r = self.ollama.chat(modelo, mensajes, ESQUEMA_MODELO, self.config.keep_alive, self.config.timeout_s,
                             self.config.num_ctx, self.config.max_tokens)
        salida = interpretar(r["contenido"])
        if salida is None:  # un único reintento pidiendo solo el JSON; si vuelve a fallar, error técnico
            mensajes += [{"role": "assistant", "content": r["contenido"][:2000]},
                         {"role": "user", "content": PROMPT_REPARAR}]
            r = self.ollama.chat(modelo, mensajes, ESQUEMA_MODELO, self.config.keep_alive, self.config.timeout_s,
                             self.config.num_ctx, self.config.max_tokens)
            salida = interpretar(r["contenido"])
            if salida is None:
                raise ErrorIA("RESPUESTA_INVALIDA", "JSON fuera de contrato tras un reintento")
        stats = {k: v for k, v in r.items() if k != "contenido"}
        return salida, stats
