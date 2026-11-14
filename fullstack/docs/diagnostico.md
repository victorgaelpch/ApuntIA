# Diagnóstico y manejo de fallos (FULL-21)

## 1. ¿Está viva o está lista?

| Pregunta | Ruta | Responde |
|----------|------|----------|
| ¿El proceso responde? | `GET /salud` | Siempre `200` mientras viva (contrato v1 intacto), con el estado del OCR, la investigación y la base de datos |
| ¿Puede trabajar? | `GET /api/v2/listo` | `200` si las dependencias **obligatorias** funcionan; `503` con cuál falla y qué hacer |

Obligatorias: base de datos (responde y tiene todas las migraciones), almacenamiento (se puede escribir
en `DATA_DIR` y quedan al menos `MINIMO_DISCO_MB`), despachador de trabajos y OCR cuando está
configurado. Opcional: investigación. Cada comprobación es breve (consulta, archivo de prueba,
versión de Tesseract), así que `listo` responde en milisegundos.

## 2. Seguir un fallo de la interfaz al servidor

1. La interfaz muestra el mensaje y, en errores del servidor, **«Referencia: …»** (el `X-ApuntIA-Error-Id`
   de un 500, el id de la petición o el `error.referencia` de un trabajo).
2. Busca esa referencia en el registro: `grep <referencia> fullstack/.estado/backend.log` (scripts) o
   `docker compose -f fullstack/compose.yaml logs backend | grep <referencia>` (Docker).
3. Cada línea lleva entre corchetes el id de la petición. La petición que crea un trabajo deja
   `trabajo=… encolado` con ese id; al terminar, el trabajo deja
   `trabajo=… tipo=… apunte=… version=… exportacion=… estado=… codigo=… error_id=… ms=…`.

## 3. Qué hay en los registros (y qué no)

- Acceso: método, **ruta sin la consulta** (las búsquedas `?q=` son privadas) agrupada sin ids,
  estado y milisegundos; `LENTA` y nivel WARNING si supera `ALERTA_PETICION_MS` (10 s).
- Trabajos: ids, estado, código de error y duración; `ALERTA` si superan `ALERTA_TRABAJO_S` (120 s).
- Disco: `ALERTA quedan N MB libres en DATA_DIR` al guardar archivos por debajo de `MINIMO_DISCO_MB`.
- Errores 5xx: traza completa solo en el log, con su `error_id`; al cliente, un mensaje genérico.
- **Nunca**: contraseñas, tokens, cookies, emails (se enmascaran automáticamente en todas las líneas:
  `[email]`, `[oculto]`, `[token]`), imágenes, texto de los apuntes ni conceptos investigados.
- `LOG_FORMATO=json` escribe una línea JSON por evento (`ts`, `nivel`, `origen`, `peticion`, `mensaje`).

**Conservación:** en modo local el registro es `fullstack/.estado/backend.log` y se sobrescribe en cada
arranque; en Docker lo gestiona Docker (`docker compose logs`). Antes de compartir un registro o un
informe de diagnóstico, revísalo: aunque los datos sensibles se enmascaran, puede haber nombres de
archivo o ids que no hace falta difundir.

## 4. Métricas

`GET /api/v2/diagnostico` (solo desde el propio equipo) devuelve: peticiones por grupo de ruta (número,
p50/p95, 5xx), trabajos por tipo (completados, parciales, fallidos, tasa de éxito, duración p50/p95,
códigos de error), pendientes y en curso, tamaño de `DATA_DIR`, memoria máxima del proceso, estado de
las dependencias y los límites de alerta.

## 5. Script de diagnóstico

```bash
fullstack/scripts/diagnostico.sh
```

```bash
fullstack/scripts/diagnostico.sh --docker --guardar diagnostico.txt
```

Reúne salud, disponibilidad, métricas y las últimas 80 líneas del registro (en Docker, de los dos
servicios, consultando la métrica desde dentro del contenedor).

## 6. Fallos simulados y comprobados

| Fallo | Qué pasa | Prueba |
|-------|----------|--------|
| Base de datos caída | `listo` → 503 (`base_datos`); `/salud` sigue en 200 con `base_datos.disponible=false` | `test_diagnostico.py` |
| Tesseract ausente con OCR configurado | `listo` → 503 (`ocr`, con cómo instalarlo); el análisis falla con `OCR_NO_DISPONIBLE` | `test_diagnostico.py`, `test_analisis.py`, `v2-flujo` |
| Disco casi lleno / lleno | `listo` → 503 (`almacenamiento`); al guardar, `507 ALMACENAMIENTO_LLENO` sin temporales | `test_diagnostico.py`, `test_regresion.py` |
| Despachador de trabajos parado | `listo` → 503 (`trabajos`) | `test_diagnostico.py` |
| Fallo del PDF o de la investigación | Trabajo `fallido` con código y referencia; el apunte queda intacto | `test_pdf.py`, `test_investigacion.py`, `v2-pdf`, `v2-investigacion` |
| 500 inesperado | Mensaje genérico + «Referencia: …» en la interfaz; traza solo en el log | `test_seguridad_api.py`, `v2-errores` |
| Carga alta | Rendimiento y memoria medidos con límites de alarma | `pytest -m rendimiento` |
