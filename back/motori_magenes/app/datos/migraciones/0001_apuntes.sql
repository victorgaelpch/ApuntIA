-- 0001: usuarios, apuntes, páginas, versiones, archivos y exportaciones (BACK-22).
CREATE TABLE usuarios (
    id            TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre        TEXT NOT NULL,
    hash_password TEXT NOT NULL,
    preferencias  TEXT NOT NULL DEFAULT '{}',
    creado        TEXT NOT NULL,
    actualizado   TEXT NOT NULL
);

CREATE TABLE apuntes (
    id              TEXT PRIMARY KEY,
    usuario_id      TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo          TEXT NOT NULL,
    estado          TEXT NOT NULL,          -- pendiente | procesando | listo | parcial | fallido | cancelado
    tipo_fuente     TEXT NOT NULL,          -- pizarron | cuaderno | mixto
    version_actual  INTEGER NOT NULL DEFAULT 0,
    texto_busqueda  TEXT NOT NULL DEFAULT '',
    clave_idempotencia TEXT,
    creado          TEXT NOT NULL,
    actualizado     TEXT NOT NULL,
    UNIQUE (usuario_id, clave_idempotencia)
);
CREATE INDEX idx_apuntes_usuario ON apuntes(usuario_id, actualizado DESC);

CREATE TABLE archivos (
    id          TEXT PRIMARY KEY,
    usuario_id  TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    apunte_id   TEXT REFERENCES apuntes(id) ON DELETE CASCADE,
    tipo        TEXT NOT NULL,              -- original | procesada | recorte | pdf
    mime        TEXT NOT NULL,
    tamano      INTEGER NOT NULL,
    sha256      TEXT NOT NULL,
    ruta        TEXT NOT NULL,              -- relativa a DATA_DIR/archivos; nunca servida directamente
    creado      TEXT NOT NULL
);
CREATE INDEX idx_archivos_apunte ON archivos(apunte_id);

CREATE TABLE paginas (
    id               TEXT PRIMARY KEY,
    apunte_id        TEXT NOT NULL REFERENCES apuntes(id) ON DELETE CASCADE,
    orden            INTEGER NOT NULL,
    tipo_fuente      TEXT NOT NULL,         -- pizarron | cuaderno
    archivo_original TEXT NOT NULL REFERENCES archivos(id),
    nombre_original  TEXT NOT NULL,
    UNIQUE (apunte_id, orden)
);

CREATE TABLE versiones (
    apunte_id   TEXT NOT NULL REFERENCES apuntes(id) ON DELETE CASCADE,
    numero      INTEGER NOT NULL,
    documento   TEXT NOT NULL,              -- JSON validado (esquema apuntia.documento/1)
    motivo      TEXT NOT NULL,              -- analisis | edicion | restauracion | investigacion
    creado      TEXT NOT NULL,
    PRIMARY KEY (apunte_id, numero)
);

CREATE TABLE exportaciones (
    id          TEXT PRIMARY KEY,
    apunte_id   TEXT NOT NULL REFERENCES apuntes(id) ON DELETE CASCADE,
    version     INTEGER NOT NULL,
    estado      TEXT NOT NULL,              -- pendiente | completado | fallido
    archivo_id  TEXT REFERENCES archivos(id),
    creado      TEXT NOT NULL,
    UNIQUE (apunte_id, version)
);
