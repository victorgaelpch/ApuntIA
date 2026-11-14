"""Vinculación y autorización de dispositivos del servidor IA (FULL-31).

Flujo (fullstack/docs/conexion-remota.md):
1. La laptop pide vincularse: recibe un CÓDIGO corto (para leérselo al administrador) y un
   SECRETO de sondeo (solo ella lo conoce). Caduca a los 10 min.
2. El administrador, sentado en la PC del servidor, aprueba el código por consola
   (`python -m ia_servidor.admin aprobar K7Q4-M2XP`). No existe ninguna ruta HTTP de
   administración: por el túnel las peticiones también llegan desde 127.0.0.1.
3. La laptop sondea con su secreto; tras la aprobación recibe UNA vez un token individual.
   Aquí solo se guarda su SHA-256: si se roba este archivo, los tokens no sirven.
4. Cada dispositivo se puede revocar; un token revocado responde 403 y no se reactiva.

Además existe un token de ADMINISTRADOR local (`admin.token`, junto a este registro) para las
herramientas que corren en la propia PC (`iniciar.bat`, `ia_servidor.medir`).

Persistencia: un JSON en IA_DATOS (por defecto ia_servidor/.datos/, ignorado por Git), escrito
de forma atómica y con un cerrojo entre procesos (servidor y consola de administración).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O ni 1/I/L: se dicta sin confusiones
VIGENCIA_SOLICITUD_S = 600
MAX_PENDIENTES = 5
MAX_SOLICITUDES_HORA = 20
MAX_SONDEOS_FALLIDOS = 10
ID_DISPOSITIVO = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class ErrorVinculacion(Exception):
    def __init__(self, codigo: str, estado: int, mensaje: str):
        super().__init__(mensaje)
        self.codigo, self.estado, self.mensaje = codigo, estado, mensaje


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalizar_codigo(codigo: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (codigo or "").upper())


def nombre_seguro(nombre: str) -> str:
    limpio = "".join(c for c in (nombre or "") if c.isprintable() and c not in "<>\"'`\\")
    return re.sub(r"\s+", " ", limpio).strip()[:60] or "dispositivo sin nombre"


@dataclass
class Autorizado:
    dispositivo_id: str
    nombre: str
    admin: bool = False


class Registro:
    def __init__(self, carpeta: Path, ahora=time.time):
        self.carpeta = Path(carpeta)
        self.archivo = self.carpeta / "dispositivos.json"
        self.ahora = ahora

    # ------------------------------------------------------------------ persistencia
    @contextmanager
    def _bloqueo(self, espera_s: float = 5.0):
        self.carpeta.mkdir(parents=True, exist_ok=True)
        cerrojo = self.carpeta / "dispositivos.lock"
        fin = time.monotonic() + espera_s
        while True:
            try:
                fd = os.open(cerrojo, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                try:  # cerrojo huérfano de un proceso que murió
                    if time.time() - cerrojo.stat().st_mtime > 30:
                        cerrojo.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue
                if time.monotonic() > fin:
                    raise ErrorVinculacion("OCUPADO", 503, "El registro de dispositivos está ocupado; reintenta.")
                time.sleep(0.05)
            except PermissionError:
                # Windows: mientras otro hilo borra el cerrojo («delete pending»), crearlo da
                # acceso denegado en vez de FileExistsError. Es el mismo caso: ocupado, reintentar.
                if os.name != "nt":
                    raise
                if time.monotonic() > fin:
                    raise ErrorVinculacion("OCUPADO", 503, "El registro de dispositivos está ocupado; reintenta.")
                time.sleep(0.05)
        try:
            yield
        finally:
            os.close(fd)
            cerrojo.unlink(missing_ok=True)

    def _leer(self) -> dict:
        if not self.archivo.exists():
            return {"version": 1, "dispositivos": [], "solicitudes": []}
        datos = json.loads(self.archivo.read_text(encoding="utf-8"))
        datos.setdefault("dispositivos", [])
        datos.setdefault("solicitudes", [])
        return datos

    def _escribir(self, datos: dict) -> None:
        temporal = self.archivo.with_suffix(".tmp")
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(temporal, self.archivo)

    def _purgar(self, datos: dict) -> None:
        t = self.ahora()
        for s in datos["solicitudes"]:
            if s["estado"] == "pendiente" and s["expira"] < t:
                s["estado"] = "expirada"
        # se conservan 24 h para que el cliente reciba «expirada» o «rechazada» y no «no existe»
        datos["solicitudes"] = [s for s in datos["solicitudes"] if s["creada"] > t - 86400]

    # ------------------------------------------------------------------ token de administrador local
    def token_admin(self) -> str:
        """Lo crea la primera vez. Solo lo leen las herramientas de la propia PC."""
        ruta = self.carpeta / "admin.token"
        self.carpeta.mkdir(parents=True, exist_ok=True)
        if not ruta.exists():
            ruta.write_text(secrets.token_urlsafe(32), encoding="utf-8")
            try:
                os.chmod(ruta, 0o600)
            except OSError:
                pass
        return ruta.read_text(encoding="utf-8").strip()

    # ------------------------------------------------------------------ vinculación (HTTP)
    def solicitar(self, dispositivo_id: str, nombre: str) -> dict:
        if not ID_DISPOSITIVO.match(dispositivo_id or ""):
            raise ErrorVinculacion("DATOS_INVALIDOS", 400, "Identificador de dispositivo no válido.")
        with self._bloqueo():
            datos = self._leer()
            self._purgar(datos)
            t = self.ahora()
            if sum(s["creada"] > t - 3600 for s in datos["solicitudes"]) >= MAX_SOLICITUDES_HORA:
                raise ErrorVinculacion("DEMASIADAS_SOLICITUDES", 429, "Demasiadas solicitudes de vinculación; espera una hora.")
            if sum(s["estado"] == "pendiente" for s in datos["solicitudes"]) >= MAX_PENDIENTES:
                raise ErrorVinculacion("DEMASIADAS_SOLICITUDES", 429, "Hay demasiadas solicitudes pendientes; espera.")
            codigo = "".join(secrets.choice(ALFABETO) for _ in range(8))
            secreto = secrets.token_urlsafe(32)
            solicitud = {"id": uuid.uuid4().hex, "codigo": codigo, "secreto_hash": hash_token(secreto),
                         "dispositivo_id": dispositivo_id, "nombre": nombre_seguro(nombre), "creada": t,
                         "expira": t + VIGENCIA_SOLICITUD_S, "estado": "pendiente", "fallos": 0}
            datos["solicitudes"].append(solicitud)
            self._escribir(datos)
        return {"solicitud_id": solicitud["id"], "secreto": secreto, "codigo": f"{codigo[:4]}-{codigo[4:]}",
                "expira_en_s": VIGENCIA_SOLICITUD_S}

    def sondear(self, solicitud_id: str, secreto: str) -> dict:
        with self._bloqueo():
            datos = self._leer()
            self._purgar(datos)
            s = next((x for x in datos["solicitudes"] if x["id"] == solicitud_id), None)
            if s is None:
                raise ErrorVinculacion("SOLICITUD_NO_ENCONTRADA", 404, "La solicitud no existe o ya caducó.")
            if not hmac.compare_digest(s["secreto_hash"], hash_token(secreto or "")):
                s["fallos"] += 1
                if s["fallos"] >= MAX_SONDEOS_FALLIDOS:
                    s["estado"] = "anulada"
                self._escribir(datos)
                raise ErrorVinculacion("NO_AUTORIZADO", 401, "Secreto de solicitud incorrecto.")
            if s["estado"] != "aprobada":
                self._escribir(datos)
                return {"estado": s["estado"]}
            # Aprobada: se entrega el token UNA vez y la solicitud queda cerrada.
            token = secrets.token_urlsafe(32)
            dispositivo = {"id": s["dispositivo_id"], "nombre": s["nombre"], "token_hash": hash_token(token),
                           "creado": self.ahora(), "ultimo_uso": None, "revocado": False, "revocado_en": None}
            datos["dispositivos"] = [d for d in datos["dispositivos"]
                                     if not (d["id"] == dispositivo["id"] and not d["revocado"])] + [dispositivo]
            s["estado"] = "entregada"
            self._escribir(datos)
            return {"estado": "aprobada", "token": token, "dispositivo_id": dispositivo["id"]}

    # ------------------------------------------------------------------ autorización
    def autorizar(self, cabecera: str | None) -> Autorizado:
        if not cabecera or not cabecera.startswith("Bearer "):
            raise ErrorVinculacion("NO_AUTENTICADO", 401, "Falta la credencial del dispositivo: vincúlalo primero.")
        token = cabecera[7:].strip()
        if hmac.compare_digest(hash_token(token), hash_token(self.token_admin())):
            return Autorizado("admin-local", "administrador local", admin=True)
        h = hash_token(token)
        with self._bloqueo():
            datos = self._leer()
            d = next((x for x in datos["dispositivos"] if hmac.compare_digest(x["token_hash"], h)), None)
            if d is None:
                raise ErrorVinculacion("NO_AUTENTICADO", 401, "Credencial desconocida: vuelve a vincular el dispositivo.")
            if d["revocado"]:
                raise ErrorVinculacion("DISPOSITIVO_REVOCADO", 403, "Este dispositivo fue revocado por el administrador.")
            t = self.ahora()
            if not d["ultimo_uso"] or t - d["ultimo_uso"] > 60:  # no escribir en cada petición
                d["ultimo_uso"] = t
                self._escribir(datos)
            return Autorizado(d["id"], d["nombre"])

    # ------------------------------------------------------------------ administración (consola)
    def pendientes(self) -> list[dict]:
        with self._bloqueo():
            datos = self._leer()
            self._purgar(datos)
            self._escribir(datos)
            return [{k: s[k] for k in ("codigo", "nombre", "dispositivo_id", "creada", "expira")}
                    for s in datos["solicitudes"] if s["estado"] == "pendiente"]

    def resolver(self, codigo: str, aprobar: bool) -> dict:
        c = normalizar_codigo(codigo)
        with self._bloqueo():
            datos = self._leer()
            self._purgar(datos)
            s = next((x for x in datos["solicitudes"] if x["codigo"] == c and x["estado"] == "pendiente"), None)
            if s is None:
                raise ErrorVinculacion("SOLICITUD_NO_ENCONTRADA", 404, f"No hay ninguna solicitud pendiente con el código {codigo}.")
            s["estado"] = "aprobada" if aprobar else "rechazada"
            self._escribir(datos)
            return {"nombre": s["nombre"], "dispositivo_id": s["dispositivo_id"], "estado": s["estado"]}

    def dispositivos(self) -> list[dict]:
        with self._bloqueo():
            return [{k: d[k] for k in ("id", "nombre", "creado", "ultimo_uso", "revocado", "revocado_en")}
                    for d in self._leer()["dispositivos"]]

    def revocar(self, dispositivo_id: str) -> int:
        with self._bloqueo():
            datos = self._leer()
            n = 0
            for d in datos["dispositivos"]:
                if d["id"] == dispositivo_id and not d["revocado"]:
                    d["revocado"], d["revocado_en"], n = True, self.ahora(), n + 1
            self._escribir(datos)
            return n
