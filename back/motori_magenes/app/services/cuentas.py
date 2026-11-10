"""Cuentas de usuario: contraseñas, sesiones y recuperación (BACK-23).

- Contraseñas con scrypt (N=2^14, r=8, p=1) y sal aleatoria de 16 bytes;
  comparación en tiempo constante.
- La sesión es un token aleatorio de 256 bits que solo vive en la cookie; en la
  base se guarda su SHA-256. Caduca tras 12 h sin uso o 7 días en total.
- Fuerza bruta: 5 fallos por email o 20 por IP en 15 minutos → bloqueo temporal.
- Recuperación: token de un solo uso, 30 minutos, guardado como hash. Sin
  servidor de correo, el enlace se escribe en el buzón de desarrollo
  (DATA_DIR/buzon/), nunca en el log.
"""

import base64
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from dataclasses import dataclass, field

from app.core.errores import ApiError
from app.datos.bd import BaseDatos, ahora

logger = logging.getLogger("apuntia.cuentas")

SCRYPT = {"n": 2 ** 14, "r": 8, "p": 1, "dklen": 32}
MIN_PASSWORD = 10
INACTIVIDAD_S = 12 * 3600
DURACION_MAXIMA_S = 7 * 24 * 3600
VENTANA_INTENTOS_S = 15 * 60
MAX_FALLOS_EMAIL = 5
MAX_FALLOS_IP = 20
RECUPERACION_S = 30 * 60
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")

PREFERENCIAS_POR_DEFECTO = {
    "tipo_fuente": "cuaderno",          # tipo propuesto al subir fotos
    "investigacion_permitida": False,   # la investigación externa requiere activarla
    "idioma_ocr": "spa+eng",   # eng ayuda con símbolos y fórmulas
}


@dataclass
class Usuario:
    id: str
    email: str
    nombre: str
    preferencias: dict = field(default_factory=dict)

    def publico(self) -> dict:
        return {"id": self.id, "email": self.email, "nombre": self.nombre, "preferencias": self.preferencias}


@dataclass
class Sesion:
    token: str
    csrf: str
    usuario: Usuario


# ------------------------------------------------------------------ contraseñas

def hash_password(password: str) -> str:
    sal = secrets.token_bytes(16)
    clave = hashlib.scrypt(password.encode(), salt=sal, **SCRYPT)
    return "scrypt$" + base64.b64encode(sal).decode() + "$" + base64.b64encode(clave).decode()


def verificar_password(password: str, guardado: str) -> bool:
    try:
        _, sal_b64, clave_b64 = guardado.split("$")
        clave = hashlib.scrypt(password.encode(), salt=base64.b64decode(sal_b64), **SCRYPT)
        return hmac.compare_digest(clave, base64.b64decode(clave_b64))
    except (ValueError, TypeError):
        return False


# Hash de una contraseña cualquiera para igualar el tiempo cuando el email no existe.
_HASH_SEÑUELO = hash_password(secrets.token_urlsafe(16))


def validar_password_nueva(password: str, email: str = "") -> None:
    if len(password) < MIN_PASSWORD:
        raise ApiError(400, "DATOS_INVALIDOS", f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres.")
    if len(password) > 256:
        raise ApiError(400, "DATOS_INVALIDOS", "La contraseña es demasiado larga.")
    if email and password.lower() == email.lower():
        raise ApiError(400, "DATOS_INVALIDOS", "La contraseña no puede ser igual al email.")


def _sha(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


def _fila_a_usuario(fila) -> Usuario:
    prefs = {**PREFERENCIAS_POR_DEFECTO, **json.loads(fila["preferencias"] or "{}")}
    return Usuario(fila["id"], fila["email"], fila["nombre"], prefs)


class Cuentas:
    def __init__(self, bd: BaseDatos, buzon_dir):
        self.bd = bd
        self.buzon = buzon_dir

    # -------------------------------------------------------------- registro

    def registrar(self, email: str, nombre: str, password: str) -> Usuario:
        email = (email or "").strip()
        nombre = (nombre or "").strip()
        if not EMAIL_RE.match(email):
            raise ApiError(400, "DATOS_INVALIDOS", "Escribe un email válido.")
        if not 1 <= len(nombre) <= 80:
            raise ApiError(400, "DATOS_INVALIDOS", "Escribe tu nombre (máximo 80 caracteres).")
        validar_password_nueva(password, email)
        if self.bd.uno("SELECT 1 FROM usuarios WHERE email = ?", (email,)):
            raise ApiError(409, "EMAIL_EN_USO", "Ya existe una cuenta con ese email. Inicia sesión o recupera tu contraseña.")
        uid = secrets.token_hex(16)
        self.bd.ejecutar(
            "INSERT INTO usuarios (id, email, nombre, hash_password, preferencias, creado, actualizado) "
            "VALUES (?, ?, ?, ?, '{}', ?, ?)", (uid, email, nombre, hash_password(password), ahora(), ahora()))
        logger.info("Cuenta creada (usuario=%s)", uid)
        return self.usuario(uid)

    def usuario(self, uid: str) -> Usuario:
        fila = self.bd.uno("SELECT * FROM usuarios WHERE id = ?", (uid,))
        if fila is None:
            raise ApiError(401, "NO_AUTENTICADO", "Tu sesión ya no es válida. Inicia sesión de nuevo.")
        return _fila_a_usuario(fila)

    # -------------------------------------------------------------- inicio de sesión

    def _comprobar_limites(self, email: str, ip: str) -> None:
        desde = time.time() - VENTANA_INTENTOS_S
        por_email = self.bd.uno("SELECT COUNT(*) AS n FROM intentos_login WHERE clave = ? AND momento > ?",
                                ("email:" + _sha(email.lower()), desde))["n"]
        por_ip = self.bd.uno("SELECT COUNT(*) AS n FROM intentos_login WHERE clave = ? AND momento > ?",
                             ("ip:" + ip, desde))["n"]
        if por_email >= MAX_FALLOS_EMAIL or por_ip >= MAX_FALLOS_IP:
            raise ApiError(429, "DEMASIADOS_INTENTOS",
                           "Demasiados intentos fallidos. Espera 15 minutos o recupera tu contraseña.")

    def _registrar_fallo(self, email: str, ip: str) -> None:
        ahora_s = time.time()
        with self.bd.transaccion() as con:
            con.execute("INSERT INTO intentos_login VALUES (?, ?)", ("email:" + _sha(email.lower()), ahora_s))
            con.execute("INSERT INTO intentos_login VALUES (?, ?)", ("ip:" + ip, ahora_s))
            # Solo los intentos de inicio de sesión: los límites de BACK-24 («lim:») tienen otras ventanas.
            con.execute("DELETE FROM intentos_login WHERE momento < ? AND clave NOT LIKE 'lim:%'",
                        (ahora_s - VENTANA_INTENTOS_S,))

    def iniciar_sesion(self, email: str, password: str, ip: str) -> Sesion:
        email = (email or "").strip()
        self._comprobar_limites(email, ip)
        fila = self.bd.uno("SELECT * FROM usuarios WHERE email = ?", (email,))
        valida = verificar_password(password or "", fila["hash_password"] if fila else _HASH_SEÑUELO)
        if fila is None or not valida:
            self._registrar_fallo(email, ip)
            raise ApiError(401, "CREDENCIALES_INVALIDAS", "Email o contraseña incorrectos.")
        self.bd.ejecutar("DELETE FROM intentos_login WHERE clave = ?", ("email:" + _sha(email.lower()),))
        return self.crear_sesion(fila["id"])

    def crear_sesion(self, uid: str) -> Sesion:
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        ahora_s = time.time()
        self.bd.ejecutar("INSERT INTO sesiones VALUES (?, ?, ?, ?, ?, ?)",
                         (_sha(token), uid, csrf, ahora_s, ahora_s, ahora_s + DURACION_MAXIMA_S))
        return Sesion(token, csrf, self.usuario(uid))

    def sesion(self, token: str | None) -> Sesion:
        """Valida el token de la cookie y renueva su último uso."""
        if not token:
            raise ApiError(401, "NO_AUTENTICADO", "Inicia sesión para continuar.")
        fila = self.bd.uno("SELECT * FROM sesiones WHERE id = ?", (_sha(token),))
        ahora_s = time.time()
        if fila is None or fila["expira"] < ahora_s or fila["ultimo_uso"] + INACTIVIDAD_S < ahora_s:
            if fila is not None:
                self.bd.ejecutar("DELETE FROM sesiones WHERE id = ?", (fila["id"],))
            raise ApiError(401, "NO_AUTENTICADO", "Tu sesión caducó. Inicia sesión de nuevo.")
        if ahora_s - fila["ultimo_uso"] > 60:  # no escribir en cada petición
            self.bd.ejecutar("UPDATE sesiones SET ultimo_uso = ? WHERE id = ?", (ahora_s, fila["id"]))
        return Sesion(token, fila["csrf"], self.usuario(fila["usuario_id"]))

    def cerrar_sesion(self, token: str | None) -> None:
        if token:
            self.bd.ejecutar("DELETE FROM sesiones WHERE id = ?", (_sha(token),))

    # -------------------------------------------------------------- contraseña

    def cambiar_password(self, sesion: Sesion, actual: str, nueva: str) -> None:
        fila = self.bd.uno("SELECT hash_password FROM usuarios WHERE id = ?", (sesion.usuario.id,))
        if not verificar_password(actual or "", fila["hash_password"]):
            raise ApiError(400, "CREDENCIALES_INVALIDAS", "La contraseña actual no es correcta.")
        validar_password_nueva(nueva, sesion.usuario.email)
        with self.bd.transaccion() as con:
            con.execute("UPDATE usuarios SET hash_password = ?, actualizado = ? WHERE id = ?",
                        (hash_password(nueva), ahora(), sesion.usuario.id))
            # Cierra las demás sesiones (por si alguien más tenía acceso); conserva la actual.
            con.execute("DELETE FROM sesiones WHERE usuario_id = ? AND id != ?",
                        (sesion.usuario.id, _sha(sesion.token)))

    def solicitar_recuperacion(self, email: str, url_base: str) -> None:
        """No revela si el email existe: el llamador responde 202 siempre."""
        fila = self.bd.uno("SELECT id, email FROM usuarios WHERE email = ?", ((email or "").strip(),))
        if fila is None:
            return
        token = secrets.token_urlsafe(32)
        self.bd.ejecutar("INSERT INTO tokens_recuperacion VALUES (?, ?, ?, 0)",
                         (_sha(token), fila["id"], time.time() + RECUPERACION_S))
        self.buzon.mkdir(parents=True, exist_ok=True)
        mensaje = (f"Para: {fila['email']}\nAsunto: Recupera tu contraseña de ApuntIA\n\n"
                   f"Abre este enlace en los próximos 30 minutos (solo funciona una vez):\n"
                   f"{url_base}#recuperar={token}\n")
        archivo = self.buzon / f"{int(time.time())}-{_sha(fila['email'])[:10]}.txt"
        archivo.write_text(mensaje, encoding="utf-8")
        logger.info("Recuperación solicitada (usuario=%s); mensaje en el buzón de desarrollo", fila["id"])

    def confirmar_recuperacion(self, token: str, nueva: str) -> None:
        fila = self.bd.uno("SELECT * FROM tokens_recuperacion WHERE id = ?", (_sha(token or ""),))
        if fila is None or fila["usado"] or fila["expira"] < time.time():
            raise ApiError(400, "TOKEN_INVALIDO", "El enlace no es válido o ya caducó. Solicita uno nuevo.")
        usuario = self.usuario(fila["usuario_id"])
        validar_password_nueva(nueva, usuario.email)
        with self.bd.transaccion() as con:
            con.execute("UPDATE tokens_recuperacion SET usado = 1 WHERE id = ?", (fila["id"],))
            con.execute("UPDATE usuarios SET hash_password = ?, actualizado = ? WHERE id = ?",
                        (hash_password(nueva), ahora(), usuario.id))
            con.execute("DELETE FROM sesiones WHERE usuario_id = ?", (usuario.id,))
            con.execute("DELETE FROM intentos_login WHERE clave = ?", ("email:" + _sha(usuario.email.lower()),))

    # -------------------------------------------------------------- perfil

    def actualizar_perfil(self, uid: str, nombre: str | None, preferencias: dict | None) -> Usuario:
        actual = self.usuario(uid)
        if nombre is not None:
            nombre = nombre.strip()
            if not 1 <= len(nombre) <= 80:
                raise ApiError(400, "DATOS_INVALIDOS", "Escribe tu nombre (máximo 80 caracteres).")
        prefs = dict(actual.preferencias)
        for clave, valor in (preferencias or {}).items():
            if clave not in PREFERENCIAS_POR_DEFECTO:
                raise ApiError(400, "DATOS_INVALIDOS", f"Preferencia desconocida: {clave}.")
            if clave == "tipo_fuente" and valor not in ("pizarron", "cuaderno"):
                raise ApiError(400, "DATOS_INVALIDOS", "El tipo de fuente debe ser pizarron o cuaderno.")
            if clave == "investigacion_permitida" and not isinstance(valor, bool):
                raise ApiError(400, "DATOS_INVALIDOS", "investigacion_permitida debe ser verdadero o falso.")
            if clave == "idioma_ocr" and valor not in ("spa", "eng", "spa+eng"):
                raise ApiError(400, "DATOS_INVALIDOS", "Idioma de OCR no admitido.")
            prefs[clave] = valor
        self.bd.ejecutar("UPDATE usuarios SET nombre = ?, preferencias = ?, actualizado = ? WHERE id = ?",
                         (nombre if nombre is not None else actual.nombre, json.dumps(prefs), ahora(), uid))
        return self.usuario(uid)

    def borrar_cuenta(self, sesion: Sesion, password: str) -> None:
        fila = self.bd.uno("SELECT hash_password FROM usuarios WHERE id = ?", (sesion.usuario.id,))
        if not verificar_password(password or "", fila["hash_password"]):
            raise ApiError(400, "CREDENCIALES_INVALIDAS", "La contraseña no es correcta.")
        self.bd.ejecutar("DELETE FROM usuarios WHERE id = ?", (sesion.usuario.id,))
