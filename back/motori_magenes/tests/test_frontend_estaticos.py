"""La interfaz servida no expone pruebas ni documentación de front/ (FRONT-11, FULL-29)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.routers import frontend


def _cliente(tmp_path, monkeypatch) -> TestClient:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "captura.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "docs" / "guia.md").write_text("# Guía", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "prueba.js").write_text("//", encoding="utf-8")
    (tmp_path / "apuntes.html").write_text("<!doctype html>", encoding="utf-8")
    monkeypatch.setattr(settings, "front_dir", str(tmp_path))
    monkeypatch.setattr(settings, "pagina_inicio", str(tmp_path / "no-existe.html"))
    app = FastAPI()
    frontend.registrar(app)
    return TestClient(app)


def test_sirve_paginas_de_la_interfaz(tmp_path, monkeypatch):
    assert _cliente(tmp_path, monkeypatch).get("/front/apuntes.html").status_code == 200


def test_no_sirve_docs_ni_pruebas(tmp_path, monkeypatch):
    cliente = _cliente(tmp_path, monkeypatch)
    for ruta in ("/front/docs/captura.png", "/front/docs/guia.md", "/front/tests/prueba.js"):
        assert cliente.get(ruta).status_code == 404, ruta
