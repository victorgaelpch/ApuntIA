-- 0004: exportaciones PDF con opciones, checksum y trabajo (BACK-20).
-- Una exportación es única por (apunte, versión, opciones): exportar dos veces
-- lo mismo reutiliza el PDF. Se recrea la tabla de 0001 conservando sus filas.
CREATE TABLE exportaciones_nueva (
    id          TEXT PRIMARY KEY,
    apunte_id   TEXT NOT NULL REFERENCES apuntes(id) ON DELETE CASCADE,
    usuario_id  TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    version     INTEGER NOT NULL,
    opciones    TEXT NOT NULL DEFAULT '{}',
    clave       TEXT NOT NULL,              -- opciones normalizadas, p. ej. "extendido|o0|c1"
    estado      TEXT NOT NULL,              -- pendiente | completado | fallido | cancelado
    trabajo_id  TEXT,
    archivo_id  TEXT REFERENCES archivos(id) ON DELETE SET NULL,
    sha256      TEXT,
    tamano      INTEGER,
    paginas_pdf INTEGER,
    creado      TEXT NOT NULL,
    actualizado TEXT NOT NULL,
    UNIQUE (apunte_id, version, clave)
);
INSERT INTO exportaciones_nueva (id, apunte_id, usuario_id, version, opciones, clave, estado, archivo_id, creado, actualizado)
    SELECT e.id, e.apunte_id, a.usuario_id, e.version, '{}', 'extendido|o0|c1', e.estado, e.archivo_id, e.creado, e.creado
    FROM exportaciones e JOIN apuntes a ON a.id = e.apunte_id;
DROP TABLE exportaciones;
ALTER TABLE exportaciones_nueva RENAME TO exportaciones;
CREATE INDEX idx_exportaciones_usuario ON exportaciones(usuario_id);
