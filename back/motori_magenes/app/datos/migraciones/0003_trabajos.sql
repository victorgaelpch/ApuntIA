-- 0003: trabajos durables (BACK-27).
CREATE TABLE trabajos (
    id          TEXT PRIMARY KEY,
    usuario_id  TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    apunte_id   TEXT REFERENCES apuntes(id) ON DELETE CASCADE,
    tipo        TEXT NOT NULL,              -- analisis | investigacion | exportacion
    estado      TEXT NOT NULL,              -- pendiente | procesando | completado | parcial | fallido | cancelado
    etapa       TEXT,
    progreso    INTEGER NOT NULL DEFAULT 0,
    intentos    INTEGER NOT NULL DEFAULT 0,
    max_intentos INTEGER NOT NULL DEFAULT 3,
    parametros  TEXT NOT NULL DEFAULT '{}',
    resultado   TEXT,
    error_codigo TEXT,
    error       TEXT,
    error_id    TEXT,
    cancelar    INTEGER NOT NULL DEFAULT 0,
    creado      TEXT NOT NULL,
    actualizado TEXT NOT NULL
);
CREATE INDEX idx_trabajos_estado ON trabajos(estado, creado);
CREATE INDEX idx_trabajos_usuario ON trabajos(usuario_id, estado);
