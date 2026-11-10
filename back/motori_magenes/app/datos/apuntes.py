"""Repositorio de apuntes (BACK-11, BACK-26). Todo método recibe el usuario.

Ninguna consulta busca un apunte solo por su id: siempre filtra por
`usuario_id`, y un apunte ajeno responde igual que uno inexistente (404).
"""

import json
import secrets

from app.core.errores import ApiError
from app.datos.almacen import Almacen
from app.datos.bd import BaseDatos, ahora
from app.services.documento import Documento, Pagina, documento_vacio, texto_plano
from app.services.entrada import PaginaRecibida



def _no_encontrado() -> ApiError:
    return ApiError(404, "NO_ENCONTRADO", "No encontramos ese apunte.")


class RepositorioApuntes:
    def __init__(self, bd: BaseDatos, almacen: Almacen):
        self.bd = bd
        self.almacen = almacen

    # ------------------------------------------------------------------ crear

    def crear(self, usuario_id: str, titulo: str, paginas: list[PaginaRecibida],
              clave_idempotencia: str | None = None) -> tuple[dict, bool]:
        """Crea el apunte con sus fotos originales. Devuelve (apunte, creado)."""
        if clave_idempotencia:
            previo = self.bd.uno("SELECT id FROM apuntes WHERE usuario_id = ? AND clave_idempotencia = ?",
                                 (usuario_id, clave_idempotencia))
            if previo:
                return self.obtener(usuario_id, previo["id"]), False
        titulo = (titulo or "").strip()[:200] or "Apunte sin título"
        tipos = {p.tipo_fuente for p in paginas}
        tipo = tipos.pop() if len(tipos) == 1 else "mixto"
        apunte_id = secrets.token_hex(16)
        guardados = []
        try:
            with self.bd.transaccion() as con:
                con.execute("INSERT INTO apuntes (id, usuario_id, titulo, estado, tipo_fuente, version_actual, "
                            "clave_idempotencia, creado, actualizado) VALUES (?, ?, ?, 'pendiente', ?, 1, ?, ?, ?)",
                            (apunte_id, usuario_id, titulo, tipo, clave_idempotencia, ahora(), ahora()))
                modelo = []
                for p in paginas:
                    archivo = self.almacen.guardar(usuario_id, p.imagen.datos, "original",
                                                   "image/" + p.imagen.formato, apunte_id, con=con)
                    guardados.append(archivo)
                    pid = f"p{p.orden}"
                    con.execute("INSERT INTO paginas VALUES (?, ?, ?, ?, ?, ?)",
                                (f"{apunte_id}-{pid}", apunte_id, p.orden, p.tipo_fuente, archivo, p.imagen.nombre))
                    alto, ancho = p.imagen.imagen.shape[:2]
                    modelo.append(Pagina(id=pid, orden=p.orden, tipo_fuente=p.tipo_fuente,
                                         archivo_original=archivo, ancho=ancho, alto=alto))
                doc = documento_vacio(titulo, modelo)
                con.execute("INSERT INTO versiones VALUES (?, 1, ?, 'creacion', ?)",
                            (apunte_id, doc.model_dump_json(), ahora()))
        except Exception:
            for archivo in guardados:  # no dejar archivos huérfanos si la transacción falló
                fila = self.bd.uno("SELECT ruta FROM archivos WHERE id = ?", (archivo,))
                if fila is None:
                    (self.almacen.base / usuario_id / archivo).unlink(missing_ok=True)
            raise
        return self.obtener(usuario_id, apunte_id), True

    # ------------------------------------------------------------------ leer

    def _fila(self, usuario_id: str, apunte_id: str):
        fila = self.bd.uno("SELECT * FROM apuntes WHERE id = ? AND usuario_id = ?", (apunte_id, usuario_id))
        if fila is None:
            raise _no_encontrado()
        return fila

    def obtener(self, usuario_id: str, apunte_id: str, con_documento: bool = True) -> dict:
        fila = self._fila(usuario_id, apunte_id)
        apunte = {k: fila[k] for k in ("id", "titulo", "estado", "tipo_fuente", "creado", "actualizado")}
        apunte["version"] = fila["version_actual"]
        apunte["paginas"] = self.bd.uno("SELECT COUNT(*) AS n FROM paginas WHERE apunte_id = ?", (apunte_id,))["n"]
        if con_documento:
            apunte["documento"] = json.loads(self.documento(usuario_id, apunte_id).model_dump_json())
        return apunte

    def documento(self, usuario_id: str, apunte_id: str, version: int | None = None) -> Documento:
        fila = self._fila(usuario_id, apunte_id)
        numero = version or fila["version_actual"]
        v = self.bd.uno("SELECT documento FROM versiones WHERE apunte_id = ? AND numero = ?", (apunte_id, numero))
        if v is None:
            raise ApiError(404, "NO_ENCONTRADO", "No existe esa versión del apunte.")
        return Documento.model_validate_json(v["documento"])

    # ------------------------------------------------------------------ escribir

    def nueva_version(self, usuario_id: str, apunte_id: str, doc: Documento, motivo: str,
                      version_esperada: int | None = None, estado: str | None = None) -> int:
        """Guarda una versión nueva; con version_esperada aplica control optimista."""
        with self.bd.transaccion() as con:
            fila = con.execute("SELECT version_actual FROM apuntes WHERE id = ? AND usuario_id = ?",
                               (apunte_id, usuario_id)).fetchone()
            if fila is None:
                raise _no_encontrado()
            if version_esperada is not None and fila["version_actual"] != version_esperada:
                raise ApiError(409, "CONFLICTO_VERSION",
                               f"El apunte cambió mientras editabas (versión actual: {fila['version_actual']}). "
                               "Recarga para ver los cambios antes de guardar.")
            numero = fila["version_actual"] + 1
            con.execute("INSERT INTO versiones VALUES (?, ?, ?, ?, ?)",
                        (apunte_id, numero, doc.model_dump_json(), motivo, ahora()))
            con.execute("UPDATE apuntes SET version_actual = ?, titulo = ?, texto_busqueda = ?, actualizado = ?"
                        + (", estado = ?" if estado else "") + " WHERE id = ?",
                        (numero, doc.titulo, texto_plano(doc), ahora(), *((estado,) if estado else ()), apunte_id))
        return numero

    def cambiar_estado(self, apunte_id: str, estado: str) -> None:
        self.bd.ejecutar("UPDATE apuntes SET estado = ?, actualizado = ? WHERE id = ?", (estado, ahora(), apunte_id))

    def borrar(self, usuario_id: str, apunte_id: str) -> None:
        """Borra el apunte, sus versiones, trabajos y archivos (incluidos los PDF)."""
        self._fila(usuario_id, apunte_id)
        self.almacen.borrar_de_apunte(apunte_id)
        with self.bd.transaccion() as con:
            con.execute("DELETE FROM exportaciones WHERE apunte_id = ?", (apunte_id,))
            con.execute("DELETE FROM paginas WHERE apunte_id = ?", (apunte_id,))
            con.execute("DELETE FROM archivos WHERE apunte_id = ?", (apunte_id,))
            con.execute("DELETE FROM apuntes WHERE id = ? AND usuario_id = ?", (apunte_id, usuario_id))

    # ------------------------------------------------------------------ historial (BACK-26)

    ORDENES = {"reciente": "actualizado DESC, a.rowid DESC", "antiguo": "actualizado ASC, a.rowid ASC",
               "titulo": "titulo COLLATE NOCASE ASC, a.rowid ASC"}

    def listar(self, usuario_id: str, q: str = "", estado: str | None = None, tipo_fuente: str | None = None,
               pagina: int = 1, por_pagina: int = 20, orden: str = "reciente",
               desde: str | None = None, hasta: str | None = None) -> dict:
        condiciones, params = ["usuario_id = ?"], [usuario_id]
        if q:
            patron = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            condiciones.append("(titulo LIKE ? ESCAPE '\\' OR texto_busqueda LIKE ? ESCAPE '\\')")
            params += [patron, patron]
        if estado:
            condiciones.append("estado = ?")
            params.append(estado)
        if tipo_fuente:
            condiciones.append("tipo_fuente = ?")
            params.append(tipo_fuente)
        if desde:  # fechas AAAA-MM-DD sobre la fecha de creación (ISO, comparable como texto)
            condiciones.append("creado >= ?")
            params.append(desde)
        if hasta:
            condiciones.append("creado < ?")
            params.append(hasta + "T99")  # incluye todo el día «hasta»
        donde = " AND ".join(condiciones)
        total = self.bd.uno(f"SELECT COUNT(*) AS n FROM apuntes WHERE {donde}", params)["n"]
        filas = self.bd.todos(
            f"SELECT a.*, (SELECT COUNT(*) FROM paginas p WHERE p.apunte_id = a.id) AS n_paginas, "
            f"(SELECT COUNT(*) FROM exportaciones e WHERE e.apunte_id = a.id AND e.estado = 'completado') AS n_pdfs "
            f"FROM apuntes a WHERE {donde} ORDER BY {self.ORDENES.get(orden, self.ORDENES['reciente'])} "
            f"LIMIT ? OFFSET ?", params + [por_pagina, (pagina - 1) * por_pagina])
        elementos = [{"id": f["id"], "titulo": f["titulo"], "estado": f["estado"], "tipo_fuente": f["tipo_fuente"],
                      "version": f["version_actual"], "paginas": f["n_paginas"], "pdfs": f["n_pdfs"],
                      "creado": f["creado"], "actualizado": f["actualizado"]} for f in filas]
        return {"elementos": elementos, "total": total, "pagina": pagina, "por_pagina": por_pagina}

    def versiones(self, usuario_id: str, apunte_id: str) -> list[dict]:
        self._fila(usuario_id, apunte_id)
        filas = self.bd.todos("SELECT numero, motivo, creado, length(documento) AS tamano FROM versiones "
                              "WHERE apunte_id = ? ORDER BY numero DESC", (apunte_id,))
        return [dict(f) for f in filas]

    def comprobar_editable(self, usuario_id: str, apunte_id: str) -> None:
        if self._fila(usuario_id, apunte_id)["estado"] in ("pendiente", "procesando"):
            raise ApiError(409, "APUNTE_EN_PROCESO",
                           "El apunte se está analizando. Espera a que termine para editarlo.")
