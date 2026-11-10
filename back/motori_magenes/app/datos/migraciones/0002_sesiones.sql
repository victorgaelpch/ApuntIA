-- 0002: sesiones, recuperación de contraseña y control de intentos (BACK-23).
CREATE TABLE sesiones (
    id          TEXT PRIMARY KEY,           -- SHA-256 del token; el token solo existe en la cookie
    usuario_id  TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    csrf        TEXT NOT NULL,
    creada      REAL NOT NULL,
    ultimo_uso  REAL NOT NULL,
    expira      REAL NOT NULL
);
CREATE INDEX idx_sesiones_usuario ON sesiones(usuario_id);

CREATE TABLE tokens_recuperacion (
    id          TEXT PRIMARY KEY,           -- SHA-256 del token
    usuario_id  TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    expira      REAL NOT NULL,
    usado       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE intentos_login (
    clave       TEXT NOT NULL,              -- "email:<hash>" o "ip:<ip>"
    momento     REAL NOT NULL
);
CREATE INDEX idx_intentos_clave ON intentos_login(clave, momento);
