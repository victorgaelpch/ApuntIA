"""Cliente del servidor IA remoto, usado por el backend de la laptop (FULL-31).

Reglas de seguridad (fullstack/docs/conexion-remota.md, seguridad-servidor-ia.md):
- La URL del servidor es PÚBLICA y no autoriza nada. Solo se aceptan `https://<nombre>` o
  `http://127.0.0.1|localhost` (pruebas o túnel local). Sin usuario, contraseña ni parámetros.
- La credencial es INDIVIDUAL de esta instalación: se obtiene con una vinculación aprobada
  por el administrador del servidor y se guarda cifrada con DPAPI de Windows (ligada a la cuenta
  del usuario) o, fuera de Windows, en un archivo solo legible por el usuario.
- La credencial se envía SOLO al mismo origen (esquema + host + puerto) con el que se vinculó:
  cambiar la URL a mano nunca filtra el token a otro servidor; exige vincular de nuevo.
- No se siguen redirecciones (evita que un servidor desvíe la petición y su credencial) y se
  verifica el certificado TLS. El navegador nunca ve el token: todas las llamadas las hace el backend.
- Robustez: tiempo máximo, reintentos acotados con espera creciente (solo en fallos
  reintentables), respeto de Retry-After y un «circuit breaker» que deja de insistir unos
  segundos tras varios fallos seguidos, para no colgar la aplicación si la PC de casa está apagada.

Códigos de error (para la interfaz y el log, sin secretos): AI_NO_CONFIGURADO, AI_URL_INVALIDA,
AI_NO_VINCULADO, AI_NET_DNS, AI_NET_TLS, AI_NET_TIMEOUT, AI_NET_CONEXION, AI_REDIRECCION,
AI_AUTH (401), AI_REVOCADO (403), AI_LIMITE (429), AI_SERVIDOR (5xx), AI_RESPUESTA,
AI_VERSION, AI_CIRCUITO_ABIERTO, AI_VINCULACION.
"""

from __future__ import annotations

import base64
import ctypes
import random
import json
import logging
import os
import secrets
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

logger = logging.getLogger("apuntia.ia_remota")
VERSION_COMPATIBLE = "1"  # mayor del contrato del servidor IA (fullstack/docs/servidor-ia.md §3)
LOCALES = {"127.0.0.1", "localhost", "::1"}


class ErrorIARemota(Exception):
    def __init__(self, codigo: str, mensaje: str, reintentable: bool = False, estado_http: int | None = None,
                 espera_s: float | None = None, codigo_servidor: str | None = None):
        super().__init__(mensaje)
        self.codigo, self.mensaje, self.reintentable = codigo, mensaje, reintentable
        self.estado_http, self.espera_s = estado_http, espera_s
        self.codigo_servidor = codigo_servidor  # código del servidor IA (p. ej. MODELO_NO_INSTALADO)

    def a_dict(self) -> dict:
        return {"codigo": self.codigo, "mensaje": self.mensaje, "reintentable": self.reintentable}


SOLUCIONES = {
    "AI_NO_CONFIGURADO": "Configura la URL del servidor IA (iniciar.bat -Modo configurar). Mientras tanto se usa el modo local.",
    "AI_URL_INVALIDA": "Usa https://<nombre-del-servidor> sin usuario, contraseña ni parámetros.",
    "AI_NO_VINCULADO": "Vincula este equipo: pide el código y que el administrador lo apruebe en la PC del servidor.",
    "AI_NET_DNS": "No se encuentra el nombre del servidor: revisa la URL y la conexión a Internet, o el túnel.",
    "AI_NET_TLS": "El certificado del servidor no es válido: no se envía nada. Revisa la URL o el túnel (nunca desactives la verificación).",
    "AI_NET_TIMEOUT": "El servidor no respondió a tiempo: puede estar apagado, dormido o muy ocupado. Reintenta más tarde.",
    "AI_NET_CONEXION": "No hay conexión con el servidor: la PC de casa puede estar apagada o el túnel caído.",
    "AI_REDIRECCION": "El servidor intentó redirigir la petición: no se sigue por seguridad. Revisa la URL.",
    "AI_AUTH": "La credencial ya no es válida: vincula este equipo de nuevo.",
    "AI_REVOCADO": "El administrador revocó este equipo: pide una nueva vinculación.",
    "AI_LIMITE": "Demasiadas peticiones seguidas: espera el tiempo indicado y reintenta.",
    "AI_SERVIDOR": "El servidor IA tuvo un problema (modelo ausente, GPU sin memoria…). Reintenta o usa el modo local.",
    "AI_RESPUESTA": "El servidor respondió algo inesperado. Reintenta; si persiste, avisa al administrador.",
    "AI_VERSION": "El servidor IA usa una versión de la API incompatible: actualiza ApuntIA en ambos equipos.",
    "AI_CIRCUITO_ABIERTO": "Varios fallos seguidos: se espera unos segundos antes de reintentar. ApuntIA sigue en modo local.",
    "AI_VINCULACION": "La solicitud de vinculación caducó, fue rechazada o anulada: pide un código nuevo.",
}


# Códigos PÚBLICOS para la interfaz y los trabajos (BACK-37), con la acción manual sugerida.
PUBLICOS = {
    "AI_NO_DISPONIBLE": "El servidor IA no está disponible (PC apagada, túnel o Internet caídos). La foto se conservó: reintenta más tarde o analiza en modo local.",
    "AI_NO_AUTORIZADA": "Este equipo no está autorizado en el servidor IA. Vincúlalo de nuevo desde «Servidor IA».",
    "AI_MODELO_AUSENTE": "El servidor IA no tiene instalado el modelo. Avisa al administrador (iniciar.bat -Modo instalar-ia).",
    "AI_MEMORIA_INSUFICIENTE": "La GPU del servidor no tiene memoria libre (quizá un juego u otro programa). Reintenta más tarde.",
    "AI_TIEMPO_AGOTADO": "El servidor IA tardó demasiado. El trabajo puede seguir allí: reintenta para recogerlo sin repetirlo.",
    "AI_RESPUESTA_INVALIDA": "El servidor IA respondió algo fuera de contrato; no se guardó nada. Reintenta o analiza en modo local.",
    "AI_COLA_LLENA": "El servidor IA está ocupado con otros trabajos. Espera unos minutos y reintenta.",
    "AI_CONTRATO_INCOMPATIBLE": "Las versiones de ApuntIA y del servidor IA no son compatibles. Actualiza ambos equipos.",
    "AI_CANCELADO": "Cancelado por el usuario.",
}


def codigo_publico(e: "ErrorIARemota") -> tuple[str, str]:
    """ErrorIARemota → (código público AI_*, mensaje con la acción manual)."""
    servidor = {"MODELO_NO_INSTALADO": "AI_MODELO_AUSENTE", "SIN_MEMORIA": "AI_MEMORIA_INSUFICIENTE",
                "TIEMPO_AGOTADO": "AI_TIEMPO_AGOTADO", "RESPUESTA_INVALIDA": "AI_RESPUESTA_INVALIDA",
                "OCUPADO": "AI_COLA_LLENA", "CANCELADO": "AI_CANCELADO"}
    directo = {"AI_AUTH": "AI_NO_AUTORIZADA", "AI_REVOCADO": "AI_NO_AUTORIZADA", "AI_NO_VINCULADO": "AI_NO_AUTORIZADA",
               "AI_NET_TIMEOUT": "AI_TIEMPO_AGOTADO", "AI_RESPUESTA": "AI_RESPUESTA_INVALIDA", "AI_LIMITE": "AI_COLA_LLENA",
               "AI_VERSION": "AI_CONTRATO_INCOMPATIBLE", "AI_CANCELADO": "AI_CANCELADO"}
    codigo = servidor.get(e.codigo_servidor or "") or directo.get(e.codigo) or "AI_NO_DISPONIBLE"
    return codigo, PUBLICOS[codigo]


# ============================================================================== URL

def validar_url(url: str | None) -> str | None:
    """None si es aceptable; si no, el motivo."""
    if not url:
        return "No hay URL configurada."
    try:
        p = urllib.parse.urlsplit(url)
    except ValueError:
        return "No es una URL válida."
    if p.username or p.password:
        return "La URL no puede llevar usuario ni contraseña."
    if p.query or p.fragment:
        return "La URL no puede llevar parámetros ni fragmentos."
    if p.path not in ("", "/"):
        return "La URL debe ser solo el servidor, sin ruta."
    host = (p.hostname or "").lower()
    if p.scheme == "https" and host and any(c.isalpha() for c in host):
        return None
    if p.scheme == "http" and host in LOCALES:
        return None
    return "Usa https://<nombre-del-servidor> (o http://127.0.0.1:<puerto> en el mismo equipo)."


def origen(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    puerto = p.port or (443 if p.scheme == "https" else 80)
    return f"{p.scheme}://{(p.hostname or '').lower()}:{puerto}"


# ============================================================================== protección de la credencial

class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi(datos: bytes, cifrar: bool) -> bytes:
    """CryptProtectData/CryptUnprotectData de Windows (ámbito: el usuario actual). Sin dependencias."""
    entrada = _Blob(len(datos), ctypes.cast(ctypes.create_string_buffer(datos, len(datos)), ctypes.POINTER(ctypes.c_char)))
    salida = _Blob()
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    funcion = crypt32.CryptProtectData if cifrar else crypt32.CryptUnprotectData
    ok = funcion(ctypes.byref(entrada), None, None, None, None, 0x1, ctypes.byref(salida))  # 0x1: sin interfaz
    if not ok:
        raise OSError("DPAPI no pudo procesar la credencial")
    try:
        return ctypes.string_at(salida.pbData, salida.cbData)
    finally:
        kernel32.LocalFree(salida.pbData)


def proteger(texto: str) -> tuple[str, str]:
    if sys.platform == "win32":
        return base64.b64encode(_dpapi(texto.encode("utf-8"), True)).decode("ascii"), "dpapi"
    return base64.b64encode(texto.encode("utf-8")).decode("ascii"), "archivo-0600"


def desproteger(valor: str, proteccion: str) -> str:
    datos = base64.b64decode(valor)
    if proteccion == "dpapi":
        return _dpapi(datos, False).decode("utf-8")
    return datos.decode("utf-8")


# ============================================================================== almacén local

class Almacen:
    """data_dir/ia_remota.json: URL manual, id de esta instalación, vinculación en curso y credencial.
    Nunca contiene tokens ni secretos en claro (salvo fuera de Windows, protegido por permisos 0600)."""

    def __init__(self, carpeta: Path):
        self.archivo = Path(carpeta) / "ia_remota.json"
        self._cerrojo = threading.Lock()

    def leer(self) -> dict:
        try:
            return json.loads(self.archivo.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def escribir(self, datos: dict) -> None:
        with self._cerrojo:
            self.archivo.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.archivo.with_suffix(".tmp")
            tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
            os.replace(tmp, self.archivo)

    def actualizar(self, **cambios) -> dict:
        datos = self.leer()
        for k, v in cambios.items():
            if v is None:
                datos.pop(k, None)
            else:
                datos[k] = v
        self.escribir(datos)
        return datos

    def dispositivo_id(self) -> str:
        datos = self.leer()
        if not datos.get("dispositivo_id"):
            datos = self.actualizar(dispositivo_id="apuntia-" + secrets.token_hex(12))
        return datos["dispositivo_id"]

    def token_para(self, url: str) -> str | None:
        """El token SOLO si la credencial se obtuvo con este mismo origen."""
        cred = self.leer().get("credencial")
        if not cred or cred.get("origen") != origen(url):
            return None
        try:
            return desproteger(cred["token"], cred["proteccion"])
        except (OSError, ValueError, KeyError):
            logger.warning("ia_remota: la credencial guardada no se puede descifrar (¿otra cuenta de Windows?)")
            return None


# ============================================================================== circuit breaker

@dataclass
class Circuito:
    umbral: int = 3          # fallos de red seguidos para abrir
    enfriamiento_s: float = 30.0
    reloj: Callable[[], float] = time.monotonic
    fallos: int = 0
    abierto_hasta: float = 0.0
    _cerrojo: threading.Lock = field(default_factory=threading.Lock)

    def comprobar(self) -> None:
        with self._cerrojo:
            restante = self.abierto_hasta - self.reloj()
        if restante > 0:
            raise ErrorIARemota("AI_CIRCUITO_ABIERTO", SOLUCIONES["AI_CIRCUITO_ABIERTO"], True, espera_s=restante)

    def exito(self) -> None:
        with self._cerrojo:
            self.fallos, self.abierto_hasta = 0, 0.0

    def fallo(self) -> None:
        with self._cerrojo:
            self.fallos += 1
            if self.fallos >= self.umbral:
                self.abierto_hasta = self.reloj() + self.enfriamiento_s
                logger.warning("ia_remota: circuito abierto %.0f s tras %d fallos", self.enfriamiento_s, self.fallos)


# ============================================================================== transporte

class _SinRedirecciones(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ErrorIARemota("AI_REDIRECCION", SOLUCIONES["AI_REDIRECCION"], False, estado_http=code)


def transporte_urllib(metodo: str, url: str, cuerpo: bytes | None, cabeceras: dict, timeout: float):
    abridor = urllib.request.build_opener(_SinRedirecciones(),
                                          urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    peticion = urllib.request.Request(url, data=cuerpo, method=metodo, headers=cabeceras)
    try:
        with abridor.open(peticion, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read(2_000_000)
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read(200_000) or b""


def _clasificar(exc: BaseException) -> ErrorIARemota:
    raiz = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(raiz, ErrorIARemota):
        return raiz
    if isinstance(raiz, socket.gaierror):
        return ErrorIARemota("AI_NET_DNS", SOLUCIONES["AI_NET_DNS"], True)
    if isinstance(raiz, ssl.SSLError):
        return ErrorIARemota("AI_NET_TLS", SOLUCIONES["AI_NET_TLS"], False)
    if isinstance(raiz, (TimeoutError, socket.timeout)):
        return ErrorIARemota("AI_NET_TIMEOUT", SOLUCIONES["AI_NET_TIMEOUT"], True)
    return ErrorIARemota("AI_NET_CONEXION", SOLUCIONES["AI_NET_CONEXION"], True)


_CIRCUITOS: dict[str, Circuito] = {}


# ============================================================================== cliente

class ClienteIARemota:
    def __init__(self, url: str | None, almacen: Almacen, transporte=None, timeout_s: float = 10.0,
                 timeout_analisis_s: float = 240.0, reintentos: int = 2, espera=time.sleep, circuito: Circuito | None = None):
        self.url = (url or "").rstrip("/")
        self.almacen = almacen
        # Se resuelve al llamar (las pruebas sustituyen transporte_urllib sin red).
        self.transporte = transporte or (lambda *a: transporte_urllib(*a))
        self.timeout_s, self.timeout_analisis_s, self.reintentos = timeout_s, timeout_analisis_s, reintentos
        self.espera = espera
        if circuito is None and self.url and not validar_url(self.url):
            circuito = _CIRCUITOS.setdefault(origen(self.url), Circuito())
        self.circuito = circuito or Circuito()

    # ------------------------------------------------------------------ base
    def _comprobar_url(self) -> None:
        if not self.url:
            raise ErrorIARemota("AI_NO_CONFIGURADO", SOLUCIONES["AI_NO_CONFIGURADO"])
        motivo = validar_url(self.url)
        if motivo:
            raise ErrorIARemota("AI_URL_INVALIDA", motivo)

    def _token(self) -> str:
        token = self.almacen.token_para(self.url)
        if not token:
            raise ErrorIARemota("AI_NO_VINCULADO", SOLUCIONES["AI_NO_VINCULADO"])
        return token

    def _peticion(self, metodo: str, ruta: str, cuerpo: bytes | None = None, tipo: str = "application/json",
                  con_token: bool = False, timeout: float | None = None, reintentar: bool = True,
                  extra: dict | None = None) -> dict:
        self._comprobar_url()
        cabeceras = {"Accept": "application/json", "User-Agent": "ApuntIA-cliente", **(extra or {})}
        if cuerpo is not None:
            cabeceras["Content-Type"] = tipo
        if con_token:
            cabeceras["Authorization"] = "Bearer " + self._token()
        intentos = 1 + (self.reintentos if reintentar else 0)
        ultimo: ErrorIARemota | None = None
        for intento in range(intentos):
            self.circuito.comprobar()
            try:
                estado, cab, datos = self.transporte(metodo, self.url + ruta, cuerpo, cabeceras, timeout or self.timeout_s)
            except ErrorIARemota as e:          # redirección rechazada
                self.circuito.exito()
                raise e
            except (urllib.error.URLError, OSError, ssl.SSLError) as e:
                ultimo = _clasificar(e)
                self.circuito.fallo()
            else:
                self.circuito.exito()  # el servidor respondió: la red funciona
                if 200 <= estado < 300:
                    try:
                        return json.loads(datos.decode("utf-8")) if datos else {}
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        raise ErrorIARemota("AI_RESPUESTA", SOLUCIONES["AI_RESPUESTA"], True, estado) from None
                ultimo = self._error_http(estado, cab, datos)
            if not ultimo.reintentable or intento == intentos - 1:
                break
            pausa = min(ultimo.espera_s if ultimo.espera_s is not None else 0.5 * 2 ** intento, 10.0)
            logger.info("ia_remota: %s; reintento %d en %.1f s", ultimo.codigo, intento + 1, pausa)
            self.espera(pausa)
        raise ultimo

    @staticmethod
    def _error_http(estado: int, cab: dict, datos: bytes) -> ErrorIARemota:
        try:
            servidor = json.loads(datos.decode("utf-8")).get("error", {})
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            servidor = {}
        detalle = servidor.get("mensaje")
        try:
            espera = float(cab.get("retry-after", "")) if cab.get("retry-after") else None
        except ValueError:
            espera = None
        if estado == 401:
            return ErrorIARemota("AI_AUTH", SOLUCIONES["AI_AUTH"], False, estado)
        if estado == 403:
            return ErrorIARemota("AI_REVOCADO", SOLUCIONES["AI_REVOCADO"], False, estado)
        if estado == 429:
            return ErrorIARemota("AI_LIMITE", SOLUCIONES["AI_LIMITE"], True, estado, espera_s=espera or 5.0)
        if estado >= 500:
            reintentable = bool(servidor.get("reintentable", estado in (502, 503, 504)))
            return ErrorIARemota("AI_SERVIDOR", detalle or SOLUCIONES["AI_SERVIDOR"], reintentable, estado, espera_s=espera,
                                 codigo_servidor=servidor.get("codigo"))
        return ErrorIARemota(servidor.get("codigo") or "AI_RESPUESTA", detalle or f"El servidor respondió {estado}.",
                             False, estado)

    # ------------------------------------------------------------------ API
    def salud(self) -> dict:
        r = self._peticion("GET", "/salud")
        if r.get("servicio") != "apuntia-ia":
            raise ErrorIARemota("AI_RESPUESTA", "Esa URL no es un servidor IA de ApuntIA.")
        if str(r.get("api_version", "")).split(".")[0] != VERSION_COMPATIBLE:
            raise ErrorIARemota("AI_VERSION", SOLUCIONES["AI_VERSION"])
        return r

    def solicitar_vinculacion(self, nombre: str) -> dict:
        self.salud()
        cuerpo = json.dumps({"dispositivo_id": self.almacen.dispositivo_id(), "nombre": nombre[:60]}).encode()
        r = self._peticion("POST", "/api/v1/vinculacion/solicitudes", cuerpo, reintentar=False)
        secreto, proteccion = proteger(r["secreto"])
        self.almacen.actualizar(vinculacion={"solicitud_id": r["solicitud_id"], "secreto": secreto, "proteccion": proteccion,
                                             "codigo": r["codigo"], "origen": origen(self.url),
                                             "expira": time.time() + float(r.get("expira_en_s", 600))})
        return {"codigo": r["codigo"], "expira_en_s": r.get("expira_en_s", 600)}

    def sondear_vinculacion(self) -> dict:
        v = self.almacen.leer().get("vinculacion")
        if not v or v.get("origen") != origen(self.url):
            raise ErrorIARemota("AI_VINCULACION", "No hay ninguna vinculación en curso con este servidor.")
        secreto = desproteger(v["secreto"], v["proteccion"])
        r = self._peticion("POST", f"/api/v1/vinculacion/solicitudes/{v['solicitud_id']}/estado",
                           json.dumps({"secreto": secreto}).encode())
        if r.get("estado") == "aprobada" and r.get("token"):
            token, proteccion = proteger(r["token"])
            self.almacen.actualizar(vinculacion=None, credencial={
                "origen": origen(self.url), "dispositivo_id": r["dispositivo_id"], "token": token,
                "proteccion": proteccion, "vinculado_en": time.time()})
            logger.info("ia_remota: equipo vinculado con %s (protección %s)", origen(self.url), proteccion)
            return {"estado": "vinculado"}
        if r.get("estado") in ("rechazada", "expirada", "anulada", "entregada"):
            self.almacen.actualizar(vinculacion=None)
        return {"estado": r.get("estado", "desconocido"), "codigo": v.get("codigo")}

    def desvincular(self) -> None:
        """Borra la credencial local. La revocación en el servidor la hace su administrador."""
        self.almacen.actualizar(credencial=None, vinculacion=None)

    def yo(self) -> dict:
        return self._peticion("GET", "/api/v1/yo", con_token=True)

    def listo(self) -> dict:
        try:
            return self._peticion("GET", "/listo", con_token=True, reintentar=False)
        except ErrorIARemota as e:
            if e.codigo == "AI_SERVIDOR" and e.estado_http == 503:
                return {"listo": False}
            raise

    def analizar(self, imagen: bytes, tarea: str = "pagina", tipo: str = "image/png") -> dict:
        tarea_q = urllib.parse.quote(tarea, safe="")
        return self._peticion("POST", f"/api/v1/analisis?tarea={tarea_q}", imagen, tipo=tipo, con_token=True,
                              timeout=self.timeout_analisis_s)

    # ------------------------------------------------------------------ trabajos asíncronos (BACK-37)
    def analizar_trabajo(self, imagen: bytes, tarea: str, clave: str, trabajo_remoto: str | None = None,
                         guardar_id=None, cancelado=None, al_avance=None, tipo: str = "image/png",
                         max_espera_s: float = 900.0, reloj=time.monotonic) -> dict:
        """Envía la imagen a la cola del servidor IA y espera el resultado consultando con espera
        creciente (1 s → 5 s, con jitter). `clave`: Idempotency-Key estable (apunte/página/foto):
        reenviar con la misma clave NO repite el trabajo en la GPU. `trabajo_remoto`: id guardado de un
        intento anterior (se retoma en vez de reenviar). `guardar_id(id)` permite persistirlo.
        `cancelado()` → True cancela también en el servidor."""
        tid = trabajo_remoto
        if tid:
            try:
                self._peticion("GET", f"/api/v1/trabajos/{urllib.parse.quote(tid, safe='')}", con_token=True)
            except ErrorIARemota as e:
                if e.codigo != "TRABAJO_NO_ENCONTRADO":   # el servidor se reinició o caducó: reenviar
                    raise
                tid = None
        if not tid:
            r = self._peticion("POST", f"/api/v1/trabajos?tarea={urllib.parse.quote(tarea, safe='')}", imagen, tipo=tipo,
                               con_token=True, timeout=self.timeout_s * 3, extra={"Idempotency-Key": clave[:100]})
            tid = r["trabajo_id"]
            if guardar_id:
                guardar_id(tid)
        fin, pausa = reloj() + max_espera_s, 1.0
        while True:
            if cancelado and cancelado():
                try:
                    self._peticion("DELETE", f"/api/v1/trabajos/{tid}", con_token=True, reintentar=False)
                except ErrorIARemota:
                    pass
                raise ErrorIARemota("AI_CANCELADO", "Cancelado por el usuario.")
            r = self._peticion("GET", f"/api/v1/trabajos/{tid}", con_token=True)
            if al_avance:
                al_avance(r.get("estado"), int(r.get("progreso") or 0), r.get("posicion"))
            if r["estado"] == "completado":
                return r["resultado"]
            if r["estado"] in ("fallido", "cancelado"):
                err = r.get("error") or {}
                raise ErrorIARemota("AI_SERVIDOR", err.get("mensaje") or "El servidor IA no pudo completar el trabajo.",
                                    bool(err.get("reintentable")), codigo_servidor=err.get("codigo") or "CANCELADO")
            if reloj() > fin:
                raise ErrorIARemota("AI_NET_TIMEOUT", "El servidor IA sigue procesando; se podrá recoger al reintentar.",
                                    True)
            self.espera(pausa * random.uniform(0.8, 1.2))
            pausa = min(pausa * 1.5, 5.0)

    # ------------------------------------------------------------------ estado y diagnóstico
    def estado(self) -> dict:
        datos = self.almacen.leer()
        cred = datos.get("credencial") or {}
        vinculado = bool(self.url) and cred.get("origen") == (origen(self.url) if self.url and not validar_url(self.url) else None)
        en_curso = datos.get("vinculacion") or {}
        return {
            "modo": "remoto" if self.url and vinculado else "local",
            "url": self.url or None,
            "url_valida": not validar_url(self.url) if self.url else False,
            "vinculado": vinculado,
            "requiere_vinculacion": bool(self.url) and not vinculado,
            "vinculacion_en_curso": {"codigo": en_curso.get("codigo"), "expira": en_curso.get("expira")} if en_curso else None,
            "proteccion_credencial": cred.get("proteccion") if vinculado else None,
            "circuito_abierto": self.circuito.abierto_hasta > self.circuito.reloj(),
        }

    def diagnosticar(self) -> list[dict]:
        """Comprobaciones en orden; cada una con resultado y solución. Nunca incluye el token."""
        pasos: list[dict] = []

        def paso(nombre, funcion):
            inicio = time.perf_counter()
            try:
                detalle = funcion()
                pasos.append({"paso": nombre, "ok": True, "detalle": detalle, "ms": round((time.perf_counter() - inicio) * 1000)})
                return True
            except ErrorIARemota as e:
                pasos.append({"paso": nombre, "ok": False, "codigo": e.codigo, "detalle": e.mensaje,
                              "solucion": SOLUCIONES.get(e.codigo, ""), "ms": round((time.perf_counter() - inicio) * 1000)})
                return False

        if not paso("configuracion", lambda: (self._comprobar_url(), self.url)[1]):
            return pasos
        host = urllib.parse.urlsplit(self.url).hostname

        def dns():
            try:
                return sorted({i[4][0] for i in socket.getaddrinfo(host, None)})[:3]
            except socket.gaierror:
                raise ErrorIARemota("AI_NET_DNS", SOLUCIONES["AI_NET_DNS"], True) from None

        if not paso("dns", dns):
            return pasos
        if not paso("salud_tls_y_version", lambda: self.salud().get("api_version")):
            return pasos
        if paso("credencial", lambda: self.yo().get("nombre")):
            paso("modelo_y_gpu", lambda: "listo" if self.listo().get("listo") else "en marcha, pero NO listo (modelo o GPU)")
        return pasos
