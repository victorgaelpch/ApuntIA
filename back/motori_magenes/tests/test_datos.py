"""Base de datos y almacenamiento privado (BACK-22)."""

import os
import time

import pytest

from app.datos.almacen import Almacen, ArchivoNoEncontrado
from app.datos.bd import BaseDatos, ErrorMigracion, ahora


@pytest.fixture
def bd(tmp_path):
    base = BaseDatos(tmp_path / "prueba.sqlite3")
    base.migrar()
    yield base
    base.cerrar()


def crear_usuario(bd, uid="u1", email="a@x.com"):
    bd.ejecutar("INSERT INTO usuarios (id, email, nombre, hash_password, creado, actualizado) "
                "VALUES (?, ?, 'A', 'h', ?, ?)", (uid, email, ahora(), ahora()))


def test_migraciones_repetibles(bd):
    version = bd.version_esquema()
    assert version >= 1
    assert bd.migrar() == []  # una segunda ejecución no aplica nada
    assert bd.version_esquema() == version


def test_migracion_modificada_se_detecta(tmp_path):
    carpeta = tmp_path / "mig"
    carpeta.mkdir()
    (carpeta / "0001_a.sql").write_text("CREATE TABLE t (x INTEGER);")
    base = BaseDatos(tmp_path / "m.sqlite3")
    base.migrar(carpeta)
    (carpeta / "0001_a.sql").write_text("CREATE TABLE t (x INTEGER, y INTEGER);")
    with pytest.raises(ErrorMigracion, match="cambió después de aplicarse"):
        base.migrar(carpeta)


def test_migracion_fallida_no_deja_cambios(tmp_path):
    carpeta = tmp_path / "mig"
    carpeta.mkdir()
    (carpeta / "0001_ok.sql").write_text("CREATE TABLE a (x INTEGER);")
    (carpeta / "0002_mala.sql").write_text("CREATE TABLE b (x INTEGER);\nESTO NO ES SQL;")
    base = BaseDatos(tmp_path / "m.sqlite3")
    with pytest.raises(ErrorMigracion, match="0002_mala"):
        base.migrar(carpeta)
    assert base.version_esquema() == 1
    tablas = {r["name"] for r in base.todos("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "a" in tablas and "b" not in tablas  # la migración fallida se revirtió completa


def test_persistencia_tras_reabrir(tmp_path):
    ruta = tmp_path / "p.sqlite3"
    base = BaseDatos(ruta)
    base.migrar()
    crear_usuario(base)
    base.cerrar()
    otra = BaseDatos(ruta)
    otra.migrar()
    assert otra.uno("SELECT email FROM usuarios")["email"] == "a@x.com"


def test_borrar_usuario_borra_en_cascada(bd):
    crear_usuario(bd)
    bd.ejecutar("INSERT INTO apuntes (id, usuario_id, titulo, estado, tipo_fuente, creado, actualizado) "
                "VALUES ('ap', 'u1', 't', 'listo', 'cuaderno', ?, ?)", (ahora(), ahora()))
    bd.ejecutar("DELETE FROM usuarios WHERE id = 'u1'")
    assert bd.uno("SELECT COUNT(*) AS n FROM apuntes")["n"] == 0


def test_almacen_aisla_por_propietario(bd, tmp_path):
    crear_usuario(bd, "u1", "a@x.com")
    crear_usuario(bd, "u2", "b@x.com")
    almacen = Almacen(tmp_path / "datos", bd)
    aid = almacen.guardar("u1", b"contenido", "original", "image/png")
    assert almacen.leer("u1", aid) == b"contenido"
    with pytest.raises(ArchivoNoEncontrado):
        almacen.leer("u2", aid)  # otro usuario con el id correcto
    with pytest.raises(ArchivoNoEncontrado):
        almacen.leer("u1", "../../etc/passwd")
    # Sin extensión ni nombre original en disco
    ruta = almacen.obtener("u1", aid).ruta
    assert ruta.name == aid and ruta.suffix == ""


def test_limpieza_de_temporales(bd, tmp_path):
    almacen = Almacen(tmp_path / "datos", bd)
    viejo = almacen.tmp / "x.parcial"
    viejo.write_bytes(b"a medias")
    os.utime(viejo, (time.time() - 7200, time.time() - 7200))
    nuevo = almacen.tmp / "y.parcial"
    nuevo.write_bytes(b"en curso")
    assert almacen.limpiar_temporales() == 1
    assert not viejo.exists() and nuevo.exists()
