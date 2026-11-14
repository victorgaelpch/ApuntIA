"""Autenticación y perfil (BACK-23). Contrato: fullstack/docs/api-v2.md §4."""

import time

import pytest

from app.services import cuentas as modulo_cuentas
from app.services.cuentas import hash_password, verificar_password
from herramientas.claves_prueba import clave_de_prueba

PASSWORD = clave_de_prueba("c1")


def error(r, status, codigo):
    assert r.status_code == status, r.text
    assert r.json()["error"]["codigo"] == codigo
    return r.json()["error"]["mensaje"]


def test_hash_scrypt_con_sal():
    a, b = hash_password("x" * 12), hash_password("x" * 12)
    assert a != b and a.startswith("scrypt$")
    assert verificar_password("x" * 12, a) and not verificar_password("y" * 12, a)


def test_registro_inicia_sesion_y_cookie_segura(nuevo_cliente):
    c = nuevo_cliente()
    r = c.http.post("/api/v2/auth/registro", json={"email": "ana@example.com", "nombre": "Ana", "password": PASSWORD})
    assert r.status_code == 201
    cookie = r.headers["set-cookie"]
    assert "apuntia_sesion=" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert "password" not in r.text and "hash" not in r.text
    c.csrf = r.json()["csrf"]
    assert c.get("/api/v2/auth/sesion").json()["usuario"]["email"] == "ana@example.com"


def test_password_nunca_en_claro(nuevo_cliente, datos_tmp):
    nuevo_cliente().registrar()
    guardado = datos_tmp.bd.uno("SELECT hash_password FROM usuarios")["hash_password"]
    assert PASSWORD not in guardado and guardado.startswith("scrypt$")
    token = datos_tmp.bd.uno("SELECT id FROM sesiones")["id"]
    assert len(token) == 64  # se guarda el SHA-256, no el token


@pytest.mark.parametrize("datos,codigo", [
    ({"email": "no-es-email", "nombre": "A", "password": PASSWORD}, "DATOS_INVALIDOS"),
    ({"email": "a@x.com", "nombre": "A", "password": clave_de_prueba("corta")[-5:]}, "DATOS_INVALIDOS"),
    ({"email": "a@x.com", "nombre": "", "password": PASSWORD}, "DATOS_INVALIDOS"),
    ({"email": "a@x.com"}, "DATOS_INVALIDOS"),
])
def test_registro_invalido(nuevo_cliente, datos, codigo):
    error(nuevo_cliente().http.post("/api/v2/auth/registro", json=datos), 400, codigo)


def test_email_duplicado_sin_distinguir_mayusculas(nuevo_cliente):
    nuevo_cliente().registrar("ana@example.com")
    r = nuevo_cliente().http.post("/api/v2/auth/registro",
                                  json={"email": "ANA@example.com", "nombre": "B", "password": PASSWORD})
    error(r, 409, "EMAIL_EN_USO")


def test_login_logout(nuevo_cliente):
    nuevo_cliente().registrar()
    c = nuevo_cliente()
    r = c.http.post("/api/v2/auth/sesion", json={"email": "ana@example.com", "password": PASSWORD})
    assert r.status_code == 200
    c.csrf = r.json()["csrf"]
    assert c.delete("/api/v2/auth/sesion").status_code == 204
    error(c.get("/api/v2/auth/sesion"), 401, "NO_AUTENTICADO")


def test_logout_invalida_el_token_en_el_servidor(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    robado = c.http.cookies.get("apuntia_sesion")
    c.delete("/api/v2/auth/sesion")
    otro = nuevo_cliente()
    otro.http.cookies.set("apuntia_sesion", robado)
    error(otro.get("/api/v2/perfil"), 401, "NO_AUTENTICADO")


def test_mismo_error_si_el_email_no_existe(nuevo_cliente):
    nuevo_cliente().registrar()
    c = nuevo_cliente()
    m1 = error(c.http.post("/api/v2/auth/sesion", json={"email": "ana@example.com", "password": clave_de_prueba("c3")}),
               401, "CREDENCIALES_INVALIDAS")
    m2 = error(c.http.post("/api/v2/auth/sesion", json={"email": "nadie@example.com", "password": clave_de_prueba("c3")}),
               401, "CREDENCIALES_INVALIDAS")
    assert m1 == m2


def test_fuerza_bruta_bloquea(nuevo_cliente):
    nuevo_cliente().registrar()
    c = nuevo_cliente()
    for _ in range(5):
        c.http.post("/api/v2/auth/sesion", json={"email": "ana@example.com", "password": clave_de_prueba("c3")})
    # Ni siquiera la contraseña correcta entra mientras dura el bloqueo
    error(c.http.post("/api/v2/auth/sesion", json={"email": "ana@example.com", "password": PASSWORD}),
          429, "DEMASIADOS_INTENTOS")


def test_csrf_obligatorio_en_cambios(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    csrf, c.csrf = c.csrf, ""
    error(c.patch("/api/v2/perfil", json={"nombre": "X"}), 403, "CSRF_INVALIDO")
    c.csrf = "falso"
    error(c.patch("/api/v2/perfil", json={"nombre": "X"}), 403, "CSRF_INVALIDO")
    c.csrf = csrf
    assert c.patch("/api/v2/perfil", json={"nombre": "X"}).status_code == 200


def test_origen_ajeno_rechazado(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    r = c.patch("/api/v2/perfil", json={"nombre": "X"}, headers={"Origin": "https://malicioso.example"})
    error(r, 403, "ORIGEN_NO_PERMITIDO")


def test_sesion_caduca_por_inactividad(nuevo_cliente, datos_tmp):
    c = nuevo_cliente()
    c.registrar()
    datos_tmp.bd.ejecutar("UPDATE sesiones SET ultimo_uso = ?", (time.time() - modulo_cuentas.INACTIVIDAD_S - 5,))
    error(c.get("/api/v2/perfil"), 401, "NO_AUTENTICADO")


def test_cambio_password_cierra_las_otras_sesiones(nuevo_cliente):
    a = nuevo_cliente()
    a.registrar()
    b = nuevo_cliente()
    b.csrf = b.http.post("/api/v2/auth/sesion", json={"email": "ana@example.com", "password": PASSWORD}).json()["csrf"]
    error(a.put("/api/v2/auth/password", json={"actual": clave_de_prueba("c7"), "nueva": clave_de_prueba("c4")}),
          400, "CREDENCIALES_INVALIDAS")
    assert a.put("/api/v2/auth/password", json={"actual": PASSWORD, "nueva": clave_de_prueba("c4")}).status_code == 204
    assert a.get("/api/v2/perfil").status_code == 200       # la actual sigue
    error(b.get("/api/v2/perfil"), 401, "NO_AUTENTICADO")   # las demás se cierran


def test_recuperacion_un_solo_uso_y_sin_revelar(nuevo_cliente, datos_tmp):
    nuevo_cliente().registrar()
    c = nuevo_cliente()
    r1 = c.http.post("/api/v2/auth/recuperacion", json={"email": "ana@example.com"})
    r2 = c.http.post("/api/v2/auth/recuperacion", json={"email": "nadie@example.com"})
    assert r1.status_code == r2.status_code == 202 and r1.json() == r2.json()
    mensajes = list((datos_tmp.data_dir / "buzon").glob("*.txt"))
    assert len(mensajes) == 1
    token = mensajes[0].read_text().split("#recuperar=")[1].strip()
    assert c.http.post("/api/v2/auth/recuperacion/confirmar",
                       json={"token": token, "password": clave_de_prueba("c2")}).status_code == 204
    error(c.http.post("/api/v2/auth/recuperacion/confirmar", json={"token": token, "password": clave_de_prueba("c5")}),
          400, "TOKEN_INVALIDO")
    assert c.http.post("/api/v2/auth/sesion", json={"email": "ana@example.com",
                                                    "password": clave_de_prueba("c2")}).status_code == 200


def test_recuperacion_caducada(nuevo_cliente, datos_tmp):
    nuevo_cliente().registrar()
    c = nuevo_cliente()
    c.http.post("/api/v2/auth/recuperacion", json={"email": "ana@example.com"})
    token = next((datos_tmp.data_dir / "buzon").glob("*.txt")).read_text().split("#recuperar=")[1].strip()
    datos_tmp.bd.ejecutar("UPDATE tokens_recuperacion SET expira = ?", (time.time() - 1,))
    error(c.http.post("/api/v2/auth/recuperacion/confirmar", json={"token": token, "password": clave_de_prueba("c2")}),
          400, "TOKEN_INVALIDO")


def test_perfil_y_preferencias(nuevo_cliente):
    c = nuevo_cliente()
    c.registrar()
    r = c.patch("/api/v2/perfil", json={"preferencias": {"tipo_fuente": "pizarron", "investigacion_permitida": True}})
    prefs = r.json()["usuario"]["preferencias"]
    assert prefs["tipo_fuente"] == "pizarron" and prefs["investigacion_permitida"] is True
    error(c.patch("/api/v2/perfil", json={"preferencias": {"admin": True}}), 400, "DATOS_INVALIDOS")
    assert c.get("/api/v2/perfil").json()["usuario"]["preferencias"]["tipo_fuente"] == "pizarron"


def test_borrar_cuenta_exige_password(nuevo_cliente, datos_tmp):
    c = nuevo_cliente()
    c.registrar()
    error(c.delete("/api/v2/perfil", json={"password": clave_de_prueba("c7")}), 400, "CREDENCIALES_INVALIDAS")
    assert c.delete("/api/v2/perfil", json={"password": PASSWORD}).status_code == 204
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM usuarios")["n"] == 0
    assert datos_tmp.bd.uno("SELECT COUNT(*) AS n FROM sesiones")["n"] == 0


def test_contrato_v1_intacto(client):
    assert client.get("/salud").json()["estado"] == "ok"


def test_estado_de_sesion_sin_error(nuevo_cliente):
    c = nuevo_cliente()
    r = c.get("/api/v2/auth/estado")
    assert r.status_code == 200 and r.json() == {"autenticado": False, "usuario": None, "csrf": None}
    u = c.registrar()
    r = c.get("/api/v2/auth/estado").json()
    assert r["autenticado"] is True and r["usuario"]["id"] == u["id"] and r["csrf"] == c.csrf


def test_enlace_de_recuperacion_usa_url_publica(nuevo_cliente, datos_tmp, monkeypatch):
    from app.core.config import settings
    c = nuevo_cliente()
    c.registrar("rec@example.com")
    monkeypatch.setattr(settings, "url_publica", "https://apuntia.ejemplo.edu")
    c.http.post("/api/v2/auth/recuperacion", json={"email": "rec@example.com"}, headers={"Host": "malicioso.example"})
    mensaje = next((datos_tmp.data_dir / "buzon").glob("*.txt")).read_text(encoding="utf-8")
    assert "https://apuntia.ejemplo.edu/front/cuenta.html#recuperar=" in mensaje and "malicioso" not in mensaje


def test_preferencias_del_pdf_y_fecha_de_alta(nuevo_cliente):
    c = nuevo_cliente()
    u = c.registrar()
    assert u["creado"] and u["preferencias"]["estilo_pdf"] == "extendido"
    r = c.patch("/api/v2/perfil", json={"preferencias": {"estilo_pdf": "basico", "incluir_originales_pdf": True}})
    assert r.status_code == 200 and r.json()["usuario"]["preferencias"]["incluir_originales_pdf"] is True
    assert c.patch("/api/v2/perfil", json={"preferencias": {"estilo_pdf": "raro"}}).status_code == 400
    assert c.patch("/api/v2/perfil", json={"preferencias": {"incluir_complementos_pdf": "si"}}).status_code == 400


def test_cerrar_las_demas_sesiones(nuevo_cliente):
    a = nuevo_cliente()
    a.registrar("multi@example.com")
    b = nuevo_cliente()
    r = b.http.post("/api/v2/auth/sesion", json={"email": "multi@example.com", "password": clave_de_prueba("c1")})
    b.csrf = r.json()["csrf"]
    assert a.get("/api/v2/auth/sesiones").json() == {"otras": 1}
    assert a.delete("/api/v2/auth/sesiones/otras").json() == {"cerradas": 1}
    assert b.get("/api/v2/perfil").status_code == 401
    assert a.get("/api/v2/perfil").status_code == 200
