-- 0005: resultados del servidor IA remoto por página (BACK-37).
-- La clave es idempotente (usuario, apunte, página, foto original y versión del pipeline):
-- reintentar un análisis reutiliza lo ya calculado o retoma el trabajo remoto por su id, y la GPU
-- no repite el trabajo. Se purgan tras 7 días (ver app/services/analisis_remoto.py).
CREATE TABLE IF NOT EXISTS ia_resultados (
    clave          TEXT PRIMARY KEY,
    usuario_id     TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    apunte_id      TEXT REFERENCES apuntes(id) ON DELETE CASCADE,
    pagina_id      TEXT,
    trabajo_remoto TEXT,                 -- id del trabajo en el servidor IA (para retomarlo)
    estado         TEXT NOT NULL,        -- enviado | completado
    resultado      TEXT,                 -- JSON del servidor IA validado (solo si completado)
    creado         TEXT NOT NULL,
    actualizado    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ia_resultados_usuario ON ia_resultados (usuario_id, actualizado);
