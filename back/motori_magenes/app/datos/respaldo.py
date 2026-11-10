"""Copias de seguridad y recuperación de DATA_DIR (FULL-23). Guía: docs/respaldo.md.

Una copia es un .tar.gz con:
  apuntia.sqlite3  instantánea CONSISTENTE de la base de datos (API de copia en línea de
                   SQLite: se puede hacer con el servidor en marcha);
  archivos/…       fotos, recortes y PDF de los usuarios;
  manifiesto.json  versión del esquema, fecha, recuentos y SHA-256 de cada archivo.

No incluye temporales (tmp/), el buzón de desarrollo (enlaces de recuperación de un solo
uso) ni las copias automáticas. La copia contiene datos personales: se crea con permisos
0600 y nunca debe ir al repositorio, a una imagen ni a la interfaz estática.

Uso (desde back/motori_magenes, o con fullstack/scripts/respaldar.sh y restaurar.sh):
    python -m app.datos.respaldo crear      DATA_DIR  destino.tar.gz
    python -m app.datos.respaldo verificar  copia.tar.gz
    python -m app.datos.respaldo restaurar  copia.tar.gz  DATA_DIR  [--forzar]
"""

import hashlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

FORMATO = "apuntia.respaldo/1"
BD = "apuntia.sqlite3"


class ErrorRespaldo(Exception):
    pass


def _sha(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def instantanea_bd(origen: Path, destino: Path) -> None:
    """Copia consistente aunque el servidor esté escribiendo (sqlite3 backup API)."""
    with sqlite3.connect(origen) as fuente, sqlite3.connect(destino) as copia:
        fuente.backup(copia)
    sqlite3.connect(destino).close()


def crear(data_dir: Path, destino: Path) -> dict:
    data_dir, destino = Path(data_dir), Path(destino)
    bd = data_dir / BD
    if not bd.exists():
        raise ErrorRespaldo(f"No hay base de datos en {data_dir}: ¿es la carpeta DATA_DIR correcta?")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="apuntia-respaldo-") as tmp:
        copia_bd = Path(tmp) / BD
        instantanea_bd(bd, copia_bd)
        con = sqlite3.connect(copia_bd)
        version = con.execute("SELECT MAX(version) FROM schema_migraciones").fetchone()[0] or 0
        recuentos = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # noqa: S608 (tablas fijas)
                     for t in ("usuarios", "apuntes", "versiones", "archivos", "exportaciones")}
        rutas = [r[0] for r in con.execute("SELECT ruta FROM archivos")]
        con.close()
        archivos = {}
        faltan = []
        for rel in rutas:
            ruta = data_dir / "archivos" / rel
            if ruta.is_file():
                archivos[f"archivos/{rel}"] = _sha(ruta.read_bytes())
            else:
                faltan.append(rel)
        manifiesto = {"formato": FORMATO, "creado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "version_esquema": version, "recuentos": recuentos,
                      "bd_sha256": _sha(copia_bd.read_bytes()), "archivos": archivos, "faltaban": faltan}
        temporal = destino.with_suffix(destino.suffix + ".parcial")
        descriptor = os.open(temporal, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "wb") as f, tarfile.open(fileobj=f, mode="w:gz") as tar:
            datos = json.dumps(manifiesto, ensure_ascii=False, indent=2).encode()
            info = tarfile.TarInfo("manifiesto.json")
            info.size, info.mode = len(datos), 0o600
            tar.addfile(info, io.BytesIO(datos))
            tar.add(copia_bd, arcname=BD)
            for nombre in archivos:
                tar.add(data_dir / nombre, arcname=nombre)
        os.replace(temporal, destino)
    return manifiesto


def _miembros_seguros(tar: tarfile.TarFile) -> list[tarfile.TarInfo]:
    """Solo archivos normales con rutas relativas dentro de la copia (sin ../ ni enlaces)."""
    seguros = []
    for m in tar.getmembers():
        ruta = Path(m.name)
        if m.isdir():
            continue
        if not m.isfile() or ruta.is_absolute() or ".." in ruta.parts:
            raise ErrorRespaldo(f"La copia contiene una entrada no permitida: {m.name}")
        if not (m.name in ("manifiesto.json", BD) or m.name.startswith("archivos/")):
            raise ErrorRespaldo(f"La copia contiene un archivo inesperado: {m.name}")
        seguros.append(m)
    return seguros


def verificar(archivo: Path) -> dict:
    """Comprueba manifiesto, sumas SHA-256 e integridad de la base de datos. Lanza ErrorRespaldo."""
    try:
        tar = tarfile.open(archivo, "r:gz")
    except (OSError, tarfile.TarError) as exc:
        raise ErrorRespaldo(f"No es una copia válida: {exc}") from None
    with tar:
        miembros = {m.name: m for m in _miembros_seguros(tar)}
        if "manifiesto.json" not in miembros or BD not in miembros:
            raise ErrorRespaldo("A la copia le falta el manifiesto o la base de datos.")
        manifiesto = json.loads(tar.extractfile(miembros["manifiesto.json"]).read())
        if manifiesto.get("formato") != FORMATO:
            raise ErrorRespaldo(f"Formato de copia desconocido: {manifiesto.get('formato')}")
        datos_bd = tar.extractfile(miembros[BD]).read()
        if _sha(datos_bd) != manifiesto["bd_sha256"]:
            raise ErrorRespaldo("La base de datos de la copia está dañada (SHA-256 distinto).")
        for nombre, sha in manifiesto["archivos"].items():
            if nombre not in miembros:
                raise ErrorRespaldo(f"Falta {nombre} en la copia.")
            if _sha(tar.extractfile(miembros[nombre]).read()) != sha:
                raise ErrorRespaldo(f"{nombre} está dañado en la copia (SHA-256 distinto).")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / BD
        ruta.write_bytes(datos_bd)
        with sqlite3.connect(ruta) as con:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ErrorRespaldo("La base de datos de la copia no supera la comprobación de integridad.")
    return manifiesto


def restaurar(archivo: Path, data_dir: Path, forzar: bool = False) -> dict:
    """Restaura en DATA_DIR. Con el servidor PARADO. Si DATA_DIR tiene datos, se exige
    --forzar y lo actual se aparta (no se borra) a «DATA_DIR.antes-<fecha>»."""
    data_dir = Path(data_dir)
    manifiesto = verificar(archivo)
    marca = datetime.now().strftime("%Y%m%d-%H%M%S")
    apartado, dentro = None, False
    if data_dir.exists() and any(data_dir.iterdir()):
        if not forzar:
            raise ErrorRespaldo(f"{data_dir} ya tiene datos. Usa --forzar para restaurar (lo actual se guardará aparte).")
        apartado = data_dir.with_name(f"{data_dir.name}.antes-{marca}")
        try:
            data_dir.rename(apartado)
        except OSError:
            # DATA_DIR es un punto de montaje (volumen de Docker): se aparta su CONTENIDO a una subcarpeta.
            apartado, dentro = data_dir / f".antes-{marca}", True
            apartado.mkdir()
            for hijo in list(data_dir.iterdir()):
                if hijo != apartado:
                    hijo.rename(apartado / hijo.name)
    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(archivo, "r:gz") as tar:
            for m in _miembros_seguros(tar):
                if m.name == "manifiesto.json":
                    continue
                destino = data_dir / m.name
                destino.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(m) as origen, open(destino, "wb") as f:
                    shutil.copyfileobj(origen, f)
        # Una copia de una versión anterior se pone al día con las migraciones de esta versión.
        from app.datos.bd import BaseDatos
        bd = BaseDatos(data_dir / BD)
        aplicadas = bd.migrar()
        bd.cerrar()
    except Exception:
        # Se deja todo como estaba.
        if dentro:
            for hijo in list(data_dir.iterdir()):
                if hijo != apartado:
                    shutil.rmtree(hijo) if hijo.is_dir() else hijo.unlink()
            for hijo in list(apartado.iterdir()):
                hijo.rename(data_dir / hijo.name)
            apartado.rmdir()
        else:
            shutil.rmtree(data_dir, ignore_errors=True)
            if apartado:
                apartado.rename(data_dir)
        raise
    manifiesto["migraciones_aplicadas"] = aplicadas
    manifiesto["apartado"] = str(apartado) if apartado else None
    return manifiesto


def copia_antes_de_migrar(bd_ruta: Path, version: int) -> Path | None:
    """Copia automática de la base de datos antes de aplicar migraciones nuevas sobre datos existentes."""
    if not bd_ruta.exists() or bd_ruta.stat().st_size == 0:
        return None
    carpeta = bd_ruta.parent / "respaldos"
    carpeta.mkdir(exist_ok=True)
    destino = carpeta / f"antes-de-migrar-desde-v{version}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sqlite3"
    instantanea_bd(bd_ruta, destino)
    os.chmod(destino, 0o600)
    return destino


def main(argv: list[str]) -> int:
    try:
        if len(argv) >= 3 and argv[0] == "crear":
            m = crear(Path(argv[1]), Path(argv[2]))
            print(f"Copia creada: {argv[2]} (esquema v{m['version_esquema']}, {m['recuentos']['usuarios']} cuentas, "
                  f"{m['recuentos']['apuntes']} apuntes, {len(m['archivos'])} archivos)")
            if m["faltaban"]:
                print(f"Aviso: {len(m['faltaban'])} archivo(s) registrados no estaban en disco.")
        elif len(argv) >= 2 and argv[0] == "verificar":
            m = verificar(Path(argv[1]))
            print(f"Copia correcta: creada {m['creado']}, esquema v{m['version_esquema']}, {len(m['archivos'])} archivos.")
        elif len(argv) >= 3 and argv[0] == "restaurar":
            m = restaurar(Path(argv[1]), Path(argv[2]), forzar="--forzar" in argv)
            print(f"Restaurada la copia del {m['creado']} en {argv[2]}.")
            if m["migraciones_aplicadas"]:
                print(f"Se actualizó el esquema: {', '.join(m['migraciones_aplicadas'])}.")
            if m["apartado"]:
                print(f"Los datos que había se guardaron en {m['apartado']}.")
        else:
            print(__doc__)
            return 2
    except ErrorRespaldo as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
