# Trabajos de análisis con el servidor IA (BACK-37)

Cómo se analiza un apunte con el servidor IA de la PC de casa sin perder fotos, sin repetir trabajo
en la GPU y sobreviviendo a cortes de red y reinicios. Conexión y seguridad:
[conexion-remota.md](conexion-remota.md). Servidor: [servidor-ia.md](servidor-ia.md).

> Estado (14/11/2026): implementado, 30 pruebas nuevas (12 de la cola del servidor y 18 del
> backend), y **probado de verdad en la PC destino** con `qwen3-vl:8b-instruct` y la foto real del
> pizarrón. Se mató el backend a mitad del análisis (19 %) y, al reiniciarlo, el trabajo se retomó
> por su id y terminó: **un solo trabajo en la GPU**, 17 bloques con su recorte, 6/6 trampas fieles.
> Pendiente: la misma prueba entre dos redes reales y la interfaz (FRONT-25).

## 1. Flujo

```
Interfaz ──POST /api/v2/apuntes (motor=ia_remota)──▶ backend: guarda las fotos y crea el trabajo «analisis»
                                                     │ (SQLite: sobrevive a reinicios)
            por cada página ─────────────────────────┤
            ¿ia_resultados tiene el resultado? ── sí ─▶ se reutiliza (ni red ni GPU)
            ¿tiene trabajo_remoto? ────────────── sí ─▶ GET /api/v1/trabajos/{id} (se retoma)
            si no ─▶ POST /api/v1/trabajos (Idempotency-Key) → se guarda el id ANTES de esperar
                     consulta con espera creciente 1 s → 5 s con jitter, hasta completado/fallido
            bloques → modelo del editor (bbox sobre la foto original, recorte, LaTeX validado,
                      revision="sin_confirmar") → nueva versión del apunte
```

- **Motor** (`motor` en `POST /api/v2/apuntes` y en `POST /api/v2/apuntes/{id}/analisis`):
  `local` (Tesseract, como siempre; por defecto), `ia_remota` o `auto` (servidor IA si el equipo está
  vinculado; si no, local **con aviso** en el resultado). Nunca se cambia de motor en silencio:
  si el servidor IA falla, el trabajo falla con su código y el usuario elige reintentar o «modo local».
- **Clave idempotente**: usuario + apunte + página + foto original + versión del pipeline. Reintentar
  (`POST /api/v2/trabajos/{id}/reintentar`) o re-analizar reutiliza lo calculado.
- **Re-analizar** (`POST /api/v2/apuntes/{id}/analisis` `{motor, sobrescribir_ediciones}`) crea una
  versión nueva; si la actual tiene correcciones del usuario exige `sobrescribir_ediciones: true`
  (409 `APUNTE_CON_EDICIONES`). Las versiones anteriores siguen en el historial.
- **Servidor IA**: cola en memoria con un trabajador (una GPU), límite `IA_MAX_COLA` (429 con
  `Retry-After`), progreso honesto por región, cancelación y resultados guardados `IA_TTL_TRABAJOS_S`
  (30 min) para recogerlos tras un corte. La imagen se libera al terminar.
- **Retención** en la laptop: `ia_resultados` se purga a los 7 días.

## 2. Estados y etapas que ve la interfaz

| Estado del trabajo | Etapa | Significado |
|--------------------|-------|-------------|
| `procesando` | `ia_enviando` | Enviando la foto al servidor IA |
| `procesando` | `ia_en_cola` | Esperando turno en la GPU |
| `procesando` | `ia_procesando` | Leyendo región por región (el progreso avanza por regiones) |
| `completado` | — | Nueva versión creada; `resultado.motor` dice qué motor se usó y `resultado.aviso` si hubo cambio |
| `fallido` | — | `error.codigo` AI_* (abajo); la foto y lo ya calculado se conservan |
| `cancelado` | — | También se cancela en el servidor IA |

## 3. Códigos públicos y recuperación

| Código | Causa | Reintentable | Qué hacer |
|--------|-------|--------------|-----------|
| `AI_NO_DISPONIBLE` | DNS, túnel, Internet, PC apagada o dormida, circuito abierto | Sí | Reintentar más tarde o re-analizar en modo local |
| `AI_NO_AUTORIZADA` | Sin vincular, 401 o revocado (403) | No (no se insiste) | Vincular de nuevo |
| `AI_MODELO_AUSENTE` | El servidor no tiene el modelo | No | `iniciar.bat -Modo instalar-ia` en la PC |
| `AI_MEMORIA_INSUFICIENTE` | GPU sin VRAM (p. ej. un juego abierto) | Sí | Reintentar más tarde |
| `AI_TIEMPO_AGOTADO` | El servidor tardó más de lo previsto | Sí | Reintentar: retoma el MISMO trabajo remoto |
| `AI_RESPUESTA_INVALIDA` | Respuesta fuera de contrato | Sí | Reintentar o modo local |
| `AI_COLA_LLENA` | 429 del servidor | Sí (respeta `Retry-After`) | Esperar |
| `AI_CONTRATO_INCOMPATIBLE` | Versiones de API distintas | No | Actualizar ambos equipos |

Casos cubiertos por pruebas: servidor caído y vuelta (mismo trabajo, sin duplicar el apunte), sin
vinculación, resultado reutilizado sin GPU, ediciones protegidas, retomar por id, el servidor olvidó
el trabajo (404 → se reenvía con la misma clave), cancelación remota, fallo del modelo, cola llena,
caducidad, aislamiento entre dispositivos. En el equipo real: **caída del backend a mitad**.

## 4. Límites conocidos

- La cola del servidor IA vive en memoria: si la PC se reinicia, los trabajos en curso se pierden y
  la laptop los reenvía (404 → reenvío con la misma clave; se repite ese trabajo en la GPU).
- Un trabajo `fallido` por el servidor IA no se reintenta solo: lo decide el usuario («Reintentar»).
- Los `fallido` por red dentro de una página detienen todo el trabajo (las demás páginas fallarían
  igual); lo ya calculado queda guardado para el reintento.
