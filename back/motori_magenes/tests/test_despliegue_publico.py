"""Pruebas de compatibilidad del modo laptop + Cloudflare Tunnel.

No requieren DNS, túnel, GPU ni acceso al servidor Ollama.
"""

import pytest
from fastapi import Request

from app.core.config import settings
from app.core.errores import ApiError
from app.routers.v2_ia import solo_local


def test_inicio_se_redirige_solo_si_se_activa(client, monkeypatch):
    monkeypatch.setattr(settings, "redireccion_inicio", False)
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 200
    assert r.json() == {"message": "Hola Mundo"}

    monkeypatch.setattr(settings, "redireccion_inicio", True)
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/inicio"


def test_origen_publico_https_aceptado_y_otros_rechazados(client, datos_tmp, monkeypatch):
    """Cloudflare termina HTTPS antes de FastAPI (que recibe HTTP interno)."""
    monkeypatch.setattr(settings, "url_publica", "https://apuntia.ejemplo.com")
    r = client.post(
        "/api/v2/auth/registro",
        headers={"Origin": "https://apuntia.ejemplo.com"},
        json={"nombre": "Prueba", "email": "prueba-apuntia@example.com", "password": "ContraseñaDePrueba123!"},
    )
    assert r.status_code == 201, r.text

    r = client.post(
        "/api/v2/auth/registro",
        headers={"Origin": "https://sitio-malicioso.ejemplo.com"},
        json={"nombre": "Prueba 2", "email": "prueba2-apuntia@example.com", "password": "ContraseñaDePrueba123!"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["codigo"] == "ORIGEN_NO_PERMITIDO"


def test_vinculacion_ia_bloqueada_por_http_en_servidor_publico(monkeypatch):
    """Ni fingiendo loopback se puede modificar la IA vía API en el modo web."""
    monkeypatch.setattr(settings, "ia_solo_cli", True)
    solicitud = Request({"type": "http", "method": "POST", "path": "/api/v2/ia/vinculacion",
                         "headers": [], "client": ("127.0.0.1", 12345), "server": ("testserver", 80),
                         "scheme": "http"})
    with pytest.raises(ApiError) as exc:
        solo_local(solicitud)
    assert exc.value.status_code == 403
    assert exc.value.codigo == "SOLO_ADMIN_SERVIDOR"
