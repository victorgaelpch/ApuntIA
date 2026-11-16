"""Base de datos SQLite con migraciones versionadas (BACK-22, FULL-23).

- Una conexión por hilo, con claves foráneas activadas y modo WAL (lecturas
  concurrentes mientras un trabajo escribe).
- Las migraciones son archivos `migraciones/NNNN_nombre.sql` que se aplican en
  orden, cada una en una transacción. Se registran en `schema_migraciones` con
  su SHA-256: si alguien modifica una migración ya aplicada, el arranque falla
  con un error visible en lugar de dejar la base en un estado desconocido.
"""

import hashlib
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("apuntia.datos")

MIGRACIONES = Path(__file__).resolve().parent / "migraciones"


class ErrorMigracion(RuntimeError):
    """Una migración no se pudo aplicar o fue modificada después de aplicarse."""


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BaseDatos:
    def __init__(self, ruta: Path):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._bloqueo_escritura = threading.RLock()
        # Una conexión por hilo; se registran todas para poder cerrarlas al apagar.
        self._abiertas: list[sqlite3.Connection] = []
        self._generacion = 0
        self._bloqueo_abiertas = threading.Lock()

    def conexion(self) -> sqlite3.Connection:
        con = getattr(self._local, "con", None)
        if con is None or getattr(self._local, "generacion", -1) != self._generacion:
            con = sqlite3.connect(self.ruta, timeout=30, isolation_level=None, check_same_thread=False)
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys = ON")
            con.execute("PRAGMA journal_mode = WAL")
            con.execute("PRAGMA busy_timeout = 30000")
            with self._bloqueo_abiertas:
                self._abiertas.append(con)
                self._local.generacion = self._generacion
            self._local.con = con
        return con

    def cerrar(self) -> None:
        """Cierra las conexiones de TODOS los hilos (al apagar o al terminar una prueba)."""
        # Con el bloqueo de escritura: ninguna transacción de otro hilo queda a medias sobre una
        # conexión cerrada (sqlite3 puede abortar el proceso en ese caso).
        with self._bloqueo_escritura:
            with self._bloqueo_abiertas:
                abiertas, self._abiertas = self._abiertas, []
                self._generacion += 1  # un hilo que siga vivo abrirá una conexión nueva
            for con in abiertas:
                try:
                    con.close()
                except sqlite3.Error:
                    pass
        self._local.con = None

    @contextmanager
    def transaccion(self):
        """BEGIN IMMEDIATE … COMMIT, con ROLLBACK si algo falla."""
        con = self.conexion()
        with self._bloqueo_escritura:
            con.execute("BEGIN IMMEDIATE")
            try:
                yield con
            except BaseException:
                con.execute("ROLLBACK")
                raise
            else:
                con.execute("COMMIT")

    def uno(self, sql: str, params=()) -> sqlite3.Row | None:
        return self.conexion().execute(sql, params).fetchone()

    def todos(self, sql: str, params=()) -> list[sqlite3.Row]:
        return self.conexion().execute(sql, params).fetchall()

    def ejecutar(self, sql: str, params=()) -> int:
        with self.transaccion() as con:
            return con.execute(sql, params).rowcount

    # ------------------------------------------------------------ migraciones

    def migrar(self, carpeta: Path = MIGRACIONES) -> list[str]:
        """Aplica las migraciones pendientes. Devuelve los nombres aplicados."""
        con = self.conexion()
        con.execute("""CREATE TABLE IF NOT EXISTS schema_migraciones (
            version INTEGER PRIMARY KEY, nombre TEXT NOT NULL, sha256 TEXT NOT NULL, aplicada TEXT NOT NULL)""")
        aplicadas = {r["version"]: r for r in con.execute("SELECT * FROM schema_migraciones")}
        nuevas = []
        for archivo in sorted(carpeta.glob("[0-9][0-9][0-9][0-9]_*.sql")):
            version = int(archivo.name[:4])
            sql = archivo.read_text(encoding="utf-8")
            sha = hashlib.sha256(sql.encode()).hexdigest()
            if version in aplicadas:
                if aplicadas[version]["sha256"] != sha:
                    raise ErrorMigracion(
                        f"La migración {archivo.name} cambió después de aplicarse. "
                        "No modifiques migraciones aplicadas: crea una nueva.")
                continue
            try:
                with self._bloqueo_escritura:
                    con.execute("BEGIN IMMEDIATE")
                    for sentencia in _sentencias(sql):
                        con.execute(sentencia)
                    con.execute("INSERT INTO schema_migraciones VALUES (?, ?, ?, ?)",
                                (version, archivo.name, sha, ahora()))
                    con.execute("COMMIT")
            except sqlite3.Error as exc:
                con.execute("ROLLBACK")
                raise ErrorMigracion(f"Falló la migración {archivo.name}: {exc}") from exc
            logger.info("Migración aplicada: %s", archivo.name)
            nuevas.append(archivo.name)
        return nuevas

    def migraciones_pendientes(self, carpeta: Path = MIGRACIONES) -> list[str]:
        """Migraciones que faltan por aplicar (sin aplicarlas). Vacía si la base es nueva."""
        existe = self.uno("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migraciones'")
        if not existe:
            return []
        aplicadas = {r["version"] for r in self.todos("SELECT version FROM schema_migraciones")}
        return [a.name for a in sorted(carpeta.glob("[0-9][0-9][0-9][0-9]_*.sql")) if int(a.name[:4]) not in aplicadas]

    def version_esquema(self) -> int:
        fila = self.uno("SELECT MAX(version) AS v FROM schema_migraciones")
        return int(fila["v"] or 0) if fila else 0


def _sentencias(sql: str) -> list[str]:
    """Divide un script SQL en sentencias (sin comentarios de línea)."""
    limpio = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))
    partes, actual = [], []
    for linea in limpio.splitlines():
        actual.append(linea.split("--")[0] if "--" in linea else linea)
        if linea.rstrip().endswith(";"):
            texto = "\n".join(actual).strip()
            if texto.strip(";").strip():
                partes.append(texto)
            actual = []
    resto = "\n".join(actual).strip()
    if resto:
        partes.append(resto)
    return partes
