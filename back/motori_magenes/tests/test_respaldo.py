"""Copias de seguridad, restauración y migraciones con datos (FULL-23)."""

import io
import json
import shutil
import sqlite3
import tarfile
import time

import pytest

from app.core import contexto
from app.datos import respaldo
from app.datos.bd import MIGRACIONES, BaseDatos
from app.datos.respaldo import ErrorRespaldo
from herramientas.claves_prueba import clave_de_prueba


def esperar(c, tid, limite=60):
    fin = time.time() + limite
    while time.time() < fin:
        t = c.get(f"/api/v2/trabajos/{tid}").json()["trabajo"]
        if t["estado"] not in ("pendiente", "procesando"):
            return t
        time.sleep(0.05)
    raise AssertionError("no terminó")


@pytest.fixture
def con_datos(nuevo_cliente, datos_tmp):
    """Cuenta con un apunte editado y su PDF."""
    from app.datos.apuntes import RepositorioApuntes
    from app.services.documento import Bloque
    from app.services.entrada import PaginaRecibida
    from app.services.validacion import ImagenRecibida
    from tests.conftest import imagen_pil
    import numpy as np
    c = nuevo_cliente()
    u = c.registrar("respaldo@example.com")
    repo = RepositorioApuntes(datos_tmp.bd, datos_tmp.almacen)
    a, _ = repo.crear(u["id"], "Física", [PaginaRecibida(1, "cuaderno", ImagenRecibida("a.png", "png", imagen_pil("PNG"), np.zeros((8, 8, 3), np.uint8)))])
    doc = repo.documento(u["id"], a["id"])
    doc.bloques.append(Bloque(id="b1", orden=0, tipo="texto", origen="usuario", texto="La luz se refracta."))
    repo.nueva_version(u["id"], a["id"], doc, "edicion", estado="listo")
    r = c.post(f"/api/v2/apuntes/{a['id']}/exportaciones", json={})
    assert esperar(c, r.json()["trabajo"]["id"])["estado"] == "completado"
    return c, u, a["id"], r.json()["exportacion"]["id"], datos_tmp


def test_respaldo_completo_y_restauracion_en_un_entorno_limpio(con_datos, tmp_path, nuevo_cliente):
    c, u, aid, eid, datos = con_datos
    pdf_antes = c.get(f"/api/v2/exportaciones/{eid}/pdf").content
    copia = tmp_path / "copias" / "apuntia.tar.gz"
    manifiesto = respaldo.crear(datos.data_dir, copia)
    assert manifiesto["recuentos"]["usuarios"] == 1 and manifiesto["recuentos"]["apuntes"] == 1
    assert len(manifiesto["archivos"]) >= 2 and not manifiesto["faltaban"]
    assert (copia.stat().st_mode & 0o777) == 0o600, "la copia tiene datos personales: solo su dueño la lee"
    nombres = tarfile.open(copia).getnames()
    assert not any(n.startswith(("tmp/", "buzon/", "respaldos/")) for n in nombres)

    # Se pierde el entorno entero y se restaura en otra carpeta limpia
    nuevo = tmp_path / "restaurado"
    resultado = respaldo.restaurar(copia, nuevo)
    assert resultado["migraciones_aplicadas"] == []
    contexto.reiniciar(nuevo)
    otro = nuevo_cliente()
    r = otro.http.post("/api/v2/auth/sesion", json={"email": "respaldo@example.com", "password": clave_de_prueba("c1")})
    assert r.status_code == 200, "la cuenta y su contraseña vuelven"
    otro.csrf = r.json()["csrf"]
    apunte = otro.get(f"/api/v2/apuntes/{aid}").json()["apunte"]
    assert apunte["titulo"] == "Física" and apunte["version"] == 2
    assert apunte["documento"]["bloques"][0]["texto"] == "La luz se refracta."
    assert otro.get(f"/api/v2/apuntes/{aid}/archivos/{apunte['documento']['paginas'][0]['archivo_original']}").status_code == 200
    assert otro.get(f"/api/v2/exportaciones/{eid}/pdf").content == pdf_antes
    # El propietario se conserva: otra cuenta sigue sin verlo
    intruso = nuevo_cliente()
    intruso.registrar("intruso@example.com")
    assert intruso.get(f"/api/v2/apuntes/{aid}").status_code == 404


def test_la_copia_se_hace_con_el_servidor_escribiendo(con_datos, tmp_path):
    c, *_, datos = con_datos
    import threading
    parar = threading.Event()

    def escribir():
        while not parar.is_set():
            datos.bd.ejecutar("INSERT INTO intentos_login VALUES (?, ?)", ("carga", time.time()))

    hilo = threading.Thread(target=escribir)
    hilo.start()
    try:
        respaldo.crear(datos.data_dir, tmp_path / "c.tar.gz")
    finally:
        parar.set()
        hilo.join()
    assert respaldo.verificar(tmp_path / "c.tar.gz")["version_esquema"] == 4


def test_verificar_detecta_copias_danadas_o_maliciosas(con_datos, tmp_path):
    *_, datos = con_datos
    copia = tmp_path / "c.tar.gz"
    respaldo.crear(datos.data_dir, copia)
    # Archivo alterado
    alterada = tmp_path / "alterada.tar.gz"
    with tarfile.open(copia) as origen, tarfile.open(alterada, "w:gz") as destino:
        for m in origen.getmembers():
            datos_m = origen.extractfile(m).read()
            if m.name.startswith("archivos/"):
                datos_m = b"cambiado" + datos_m[8:]
            m.size = len(datos_m)
            destino.addfile(m, io.BytesIO(datos_m))
    with pytest.raises(ErrorRespaldo, match="dañado"):
        respaldo.verificar(alterada)
    # Entrada con ../ (path traversal al restaurar)
    maliciosa = tmp_path / "maliciosa.tar.gz"
    with tarfile.open(copia) as origen, tarfile.open(maliciosa, "w:gz") as destino:
        for m in origen.getmembers():
            destino.addfile(m, origen.extractfile(m))
        info = tarfile.TarInfo("../../fuera.txt")
        info.size = 2
        destino.addfile(info, io.BytesIO(b"no"))
    with pytest.raises(ErrorRespaldo, match="no permitida"):
        respaldo.restaurar(maliciosa, tmp_path / "x")
    assert not (tmp_path / "fuera.txt").exists()
    with pytest.raises(ErrorRespaldo):
        respaldo.verificar(tmp_path / "no-existe.tar.gz")


def test_restaurar_no_pisa_datos_sin_forzar_y_los_aparta_con_forzar(con_datos, tmp_path):
    *_, datos = con_datos
    copia = tmp_path / "c.tar.gz"
    respaldo.crear(datos.data_dir, copia)
    destino = tmp_path / "destino"
    destino.mkdir()
    (destino / "algo.txt").write_text("datos actuales")
    with pytest.raises(ErrorRespaldo, match="--forzar"):
        respaldo.restaurar(copia, destino)
    r = respaldo.restaurar(copia, destino, forzar=True)
    apartado = r["apartado"]
    assert apartado and (tmp_path / apartado.split("/")[-1] / "algo.txt").read_text() == "datos actuales"
    assert (destino / "apuntia.sqlite3").exists()


def test_restaurar_una_copia_de_una_version_anterior_la_migra(tmp_path):
    previas = tmp_path / "previas"
    previas.mkdir()
    for a in sorted(MIGRACIONES.glob("000[123]_*.sql")):
        shutil.copy(a, previas / a.name)
    viejo = tmp_path / "viejo"
    viejo.mkdir()
    bd = BaseDatos(viejo / "apuntia.sqlite3")
    bd.migrar(previas)
    bd.ejecutar("INSERT INTO usuarios VALUES ('u', 'u@x.com', 'U', 'h', '{}', 'f', 'f')")
    bd.cerrar()
    copia = tmp_path / "vieja.tar.gz"
    assert respaldo.crear(viejo, copia)["version_esquema"] == 3
    r = respaldo.restaurar(copia, tmp_path / "nuevo")
    assert r["migraciones_aplicadas"] == ["0004_exportaciones.sql"]
    con = sqlite3.connect(tmp_path / "nuevo" / "apuntia.sqlite3")
    assert con.execute("SELECT MAX(version) FROM schema_migraciones").fetchone()[0] == 4
    assert con.execute("SELECT email FROM usuarios").fetchone()[0] == "u@x.com"


def test_copia_automatica_antes_de_migrar_al_arrancar(tmp_path):
    previas = tmp_path / "previas"
    previas.mkdir()
    for a in sorted(MIGRACIONES.glob("000[123]_*.sql")):
        shutil.copy(a, previas / a.name)
    datos = tmp_path / "datos"
    datos.mkdir()
    bd = BaseDatos(datos / "apuntia.sqlite3")
    bd.migrar(previas)
    bd.cerrar()
    ctx = contexto.reiniciar(datos)   # arranque de la versión nueva: aplica 0004
    assert ctx.bd.version_esquema() == 4
    copias = list((datos / "respaldos").glob("antes-de-migrar-desde-v3-*.sqlite3"))
    assert len(copias) == 1
    assert sqlite3.connect(copias[0]).execute("SELECT MAX(version) FROM schema_migraciones").fetchone()[0] == 3
    # Un arranque sin migraciones pendientes no hace copias
    contexto.reiniciar(datos)
    assert len(list((datos / "respaldos").glob("*.sqlite3"))) == 1


def test_cli(con_datos, tmp_path, capsys):
    *_, datos = con_datos
    copia = tmp_path / "c.tar.gz"
    assert respaldo.main(["crear", str(datos.data_dir), str(copia)]) == 0
    assert respaldo.main(["verificar", str(copia)]) == 0
    assert "Copia correcta" in capsys.readouterr().out
    assert respaldo.main(["restaurar", str(copia), str(datos.data_dir)]) == 1  # tiene datos y no hay --forzar
    assert respaldo.main([]) == 2
    manifiesto = json.loads(tarfile.open(copia).extractfile("manifiesto.json").read())
    assert "respaldo@example.com" not in json.dumps(manifiesto), "el manifiesto no lleva datos personales"


def test_restaurar_sobre_un_punto_de_montaje(con_datos, tmp_path, monkeypatch):
    """En Docker DATA_DIR es un volumen: no se puede renombrar; se aparta su contenido."""
    *_, datos = con_datos
    copia = tmp_path / "c.tar.gz"
    respaldo.crear(datos.data_dir, copia)
    volumen = tmp_path / "volumen"
    volumen.mkdir()
    (volumen / "viejo.txt").write_text("antes")
    original = type(volumen).rename

    def rename(self, destino):
        if self == volumen:
            raise OSError(16, "Device or resource busy")
        return original(self, destino)

    monkeypatch.setattr(type(volumen), "rename", rename)
    r = respaldo.restaurar(copia, volumen, forzar=True)
    assert "/.antes-" in r["apartado"]
    apartado = next(volumen.glob(".antes-*"))
    assert (apartado / "viejo.txt").read_text() == "antes" and (volumen / "apuntia.sqlite3").exists()


def test_una_restauracion_fallida_deja_todo_como_estaba(con_datos, tmp_path, monkeypatch):
    *_, datos = con_datos
    copia = tmp_path / "c.tar.gz"
    respaldo.crear(datos.data_dir, copia)
    destino = tmp_path / "destino"
    destino.mkdir()
    (destino / "actual.txt").write_text("no tocar")
    from app.datos import bd as modulo_bd

    def falla(self, *a, **k):
        raise modulo_bd.ErrorMigracion("migración rota")

    monkeypatch.setattr(modulo_bd.BaseDatos, "migrar", falla)
    with pytest.raises(modulo_bd.ErrorMigracion):
        respaldo.restaurar(copia, destino, forzar=True)
    assert (destino / "actual.txt").read_text() == "no tocar" and not (destino / "apuntia.sqlite3").exists()
