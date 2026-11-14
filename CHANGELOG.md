# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versiones
[semánticas](https://semver.org/lang/es/). La versión se ve en `GET /salud` (`"version"`).
Cómo se publica una versión: [fullstack/docs/entrega.md](fullstack/docs/entrega.md#6-lista-de-comprobación-de-la-versión).

## [Sin publicar]

### Añadido

- **Cierre de ApuntIA 3.0, parte verificable** (FULL-32): `fullstack/scripts/validar.ps1` (rápido,
  `-Completo`, `-Gpu` con el servidor IA real y `-Remoto` para la prueba entre redes); CI con el backend
  en Windows y `pip-audit` del servidor IA; `/api/v2/listo` avisa si a Tesseract le faltan idiomas;
  README con los dos perfiles y guías `algoritmos.md`, `modelos-y-requisitos.md`,
  `exposicion-paso-a-paso.md`, `pruebas-y-metricas.md` y `referencias.md`. La prueba entre dos redes
  sigue pendiente.
- **Propuestas del servidor IA en el PDF y fuentes verificables** (BACK-38): etiqueta «propuesta del
  servidor IA: sin revisar/revisada», recorte de la foto una vez por región (opción
  `incluir_recortes_ia`, clave de exportación por defecto sin cambios) y aviso en la portada; las
  regiones multilínea se dividen en un bloque por fórmula; resumen, glosario y conceptos a investigar
  solo de bloques confirmados; Wikilibros como segunda fuente (`INVESTIGACION_PROVEEDOR=wikipedia,wikilibros`)
  y redirecciones a otros hosts rechazadas. Guías `generacion-pdf.md`, `investigacion-verificada.md`,
  `trazabilidad-contenido.md` y PDFs sintéticos de referencia.
- **Editor de revisión de propuestas de IA** (FRONT-26): etiqueta «Propuesta de IA · sin revisar» sin
  porcentajes, recorte siempre visible, dudas del modelo, aviso de símbolos confundibles y «Marcar como
  revisado» (campo `revisado`, opcional y compatible con apuntes anteriores).
- **Pantalla «Servidor IA»** (FRONT-25): estado con texto, conexión automática/manual/sin IA, vinculación
  con código, diagnóstico paso a paso; selector de reconocimiento al crear apuntes y «Analizar en modo
  local» cuando el servidor IA falla. El navegador nunca recibe el token.
- **Análisis con el servidor IA en trabajos durables** (BACK-37): `motor` local / ia_remota / auto, cola
  asíncrona en el servidor IA (`/api/v1/trabajos`), clave idempotente por página y resultado guardado
  (`ia_resultados`), retomar por id tras cortes o reinicios, cancelación remota, códigos AI_* y
  `POST /api/v2/apuntes/{id}/analisis` para re-analizar sin perder correcciones (versión nueva).
- **Banco de evaluación con fotos reales** (BACK-36): `python -m ia_servidor.medir --corpus` sobre un corpus
  privado fuera de Git (permiso obligatorio por foto), con métricas de fórmulas por LaTeX normalizado y
  notación equivalente. Guía: `fullstack/docs/evaluacion-multimodal.md`.
- **Conexión remota segura** (FULL-31): vinculación de un solo uso aprobada en la consola de la PC
  del servidor (`iniciar.bat -Modo dispositivos`), token individual revocable (el servidor guarda
  solo su hash), credencial cifrada con DPAPI en la laptop y enviada solo al origen vinculado, sin
  redirecciones, con reintentos, circuit breaker y códigos `AI_*`. Rutas `/api/v2/ia/*` (estado,
  configuración, vinculación, diagnóstico) y `python -m herramientas.vincular_ia`. Guías de
  Tailscale Serve y Cloudflare Tunnel (sin probar aún entre dos redes reales).
- Servidor IA, pipeline 1.1 (BACK-35): prompts cortos y texto plano, `qwen3-vl:8b-instruct` y
  `4b-instruct` por defecto (la etiqueta `qwen3-vl:8b` es la variante «thinking»), medido en la RTX 3060.
- **Servidor de inferencia IA** (BACK-35): `ia_servidor/` (FastAPI) para la PC con GPU, con contrato
  v1 (`/salud`, `/listo`, `/api/v1/capacidades`, `/api/v1/analisis`), errores con código y
  `reintentable`, una inferencia a la vez, respaldo `qwen3-vl:4b` ante falta de memoria y Ollama
  solo en loopback. Guía: `fullstack/docs/servidor-ia.md`.
- **Menú y modos en Windows** (FULL-30): `iniciar.bat` sin argumentos muestra un menú;
  `-Modo app|servidor-ia|instalar-ia|diagnostico|configurar|detener`. Instalación reanudable
  del servidor IA (pregunta antes de instalar Ollama o descargar el modelo), diagnóstico y URL del
  servidor validada. CI nueva en Windows para los scripts.
- **Tickets con trazabilidad real** (FULL-29): `fullstack/tickets/` con una ficha por cada Issue de
  GitHub (abiertos y cerrados), índice, cronograma PLANIFICADO, plantilla y bitácoras REALES.
  `fullstack/scripts/sincronizar_tickets.py` pagina la API, separa Pull Requests de Issues, no pisa
  colisiones de identificador ni notas manuales, funciona sin red con un snapshot y es idempotente.
- El comprobador de enlaces revisa también imágenes y documentos huérfanos (FULL-29).
- **Reconocimiento adaptativo** (BACK-28, `RECONOCIMIENTO_MODO=adaptativo` por defecto): diagnóstico
  de calidad de cada foto con avisos concretos y nivel `insuficiente` (se pide repetir la foto y
  nada queda como seguro); el texto girado se endereza; las regiones dudosas se releen con
  variantes por región; una relectura de consenso detecta errores con confianza alta; lectura
  especializada de fórmulas. Cada bloque guarda su procedencia, hasta 3 lecturas alternativas
  reales y el motivo de revisión; el editor las muestra y una alternativa se usa con un clic.
  Corpus de casos difíciles con particiones de desarrollo y evaluación (`herramientas/corpus_dificil.py`,
  `herramientas/evaluar_dificil.py`). En la partición de evaluación: CER 27,4 % → 17,4 %, textos
  falsos dados por seguros 6 → 3. Sin dependencias nuevas. `RECONOCIMIENTO_MODO=clasico` vuelve al flujo anterior.

### Cambiado

- **La documentación se movió** (FULL-29) de `docs/` a `fullstack/docs/` (transversal) y
  `front/docs/` (interfaz) con `git mv`; enlaces, comentarios, pruebas y CI actualizados.
  Correspondencia de rutas: `fullstack/docs/ESTRUCTURA_DOCUMENTAL.md`. Las entradas anteriores de
  este registro mencionan las rutas antiguas tal como eran entonces.
- `front/docs/` no se sirve al navegador (FastAPI y la imagen Docker web la excluyen).
- El análisis tarda más: ~1 s por foto en la mediana (antes ~0,4 s). Límites configurables con
  `RECONOCIMIENTO_MAX_VARIANTES`, `RECONOCIMIENTO_MAX_BLOQUES` y `RECONOCIMIENTO_MAX_SEGUNDOS`.
- Igualdades cortas como `F = ma` se detectan como fórmula.

### Corregido

- **Copias de seguridad en Windows** (FULL-32): `respaldo crear/verificar` dejaba abiertas las
  conexiones SQLite (`with sqlite3.connect()` no cierra) y Windows no podía borrar la carpeta temporal;
  además las rutas con `\` no coincidían con los nombres del archivo tar. Ahora se cierran con
  `contextlib.closing` y las rutas se normalizan. Pruebas del respaldo portables a Windows.
- Pruebas de integración en Windows: `pdftotext -enc UTF-8` y borrado temporal con reintentos.

## [2.0.0] — 2026-11-10 (preparada, sin etiqueta publicada)

Apuntes completos con cuenta: de varias fotos de pizarrón o cuaderno a un apunte editable y un PDF.
Todo lo de la 1.0.0 sigue igual (**sin cambios incompatibles en `POST /analisis` ni en `/salud`**);
el número mayor sube porque cambia el producto, no el contrato v1.

### Añadido

- **Cuentas** (registro, sesión con cookie HttpOnly y CSRF, recuperación de contraseña por buzón
  local, perfil, preferencias, cerrar las demás sesiones, borrar la cuenta). BACK-23, FRONT-17, FRONT-19, FULL-18.
- **Apuntes de 1 a 20 fotos** con trabajos durables (avance, cancelación, reintento). BACK-11, BACK-21, BACK-27, FRONT-12.
- **OCR por bloques** con Tesseract 5 y preprocesado por tipo de fuente; **manuscrito** con respaldo
  que no inventa texto; **fórmulas** a LaTeX verificable (las 2D se conservan como imagen). BACK-12 a BACK-15.
- **Editor**: bloques junto a su región de la foto, fórmulas con vista previa, tablas, esquemas,
  versiones, comparación y restauración. BACK-17, BACK-19, BACK-26, FRONT-13, FRONT-14, FRONT-22.
- **Información complementaria** opcional de Wikipedia, con consentimiento y fuente citada. BACK-18, FRONT-15.
- **PDF académico** (portada, índice, tablas, fórmulas, referencias), exportación idempotente. BACK-20, FRONT-16.
- **Mis apuntes**: búsqueda, filtros por fecha, estado y tipo; historial. BACK-26, FRONT-18.
- **Base de datos** SQLite con migraciones y almacenamiento privado; autorización por propietario. BACK-22, BACK-24.
- **Arranque con scripts** (`iniciar`/`detener` en Linux, macOS y Windows) y con **Docker Compose**
  (Nginx sin privilegios + backend). FULL-11, FULL-12, FULL-13.
- **Diagnóstico** (`/api/v2/listo`, `/api/v2/diagnostico` local, id de petición, alertas) y **copias de
  seguridad** verificadas con restauración. FULL-21, FULL-23.
- **Banco de evaluación** sintético con línea base y comparación automática. FULL-19.
- **Modo demostración** (`iniciar.sh --demo`): cuenta y apuntes sintéticos en una carpeta aparte. FULL-22.
- **Escenarios de aceptación** con criterios de rechazo (`fullstack/evaluacion/aceptacion.py`), en la CI. FULL-24.
- Pruebas de punta a punta con el backend real, accesibilidad y diseño adaptable; CI con trabajos
  rápido, interfaz, integración y Docker. BACK-25, FRONT-21, FULL-16, FULL-17.

### Cambiado

- La interfaz se sirve desde el backend en el mismo origen (`/inicio`, `/front/…`) con CSP estricta.
- `GET /salud` informa de la versión 2.0.0 (antes 1.0.0); el resto de su respuesta no cambia.

### Corregido (durante la preparación de la entrega)

- El paquete `back/motori_magenes/app/datos/` no estaba en el repositorio por una regla demasiado
  amplia del `.gitignore` (`datos/`): un clon limpio no arrancaba. Detectado al instalar desde cero.
- Dos análisis simultáneos tardaban ~200 s en vez de ~2 s porque los hilos OpenMP de Tesseract
  competían: ahora `OMP_THREAD_LIMIT=1` por defecto.
- Una tabla dibujada en la hoja se tomaba por el borde de la hoja (se perdía lo de alrededor) y sus
  celdas no se leían (0 de 8): ahora se conserva la página entera y se leen 7 de 8.
- El PDF rotulaba como «manuscrito» cualquier fragmento no transcrito (también fórmulas impresas).
- Nginx sobrescribe `X-Forwarded-For` (antes se podía falsear para saltarse los límites por IP).
- Las bombas de descompresión se rechazan como `IMAGEN_DEMASIADO_GRANDE` (413), no como imagen corrupta.

### Seguridad

Auditoría completa (FULL-20) en [docs/seguridad.md](fullstack/docs/seguridad.md), con los riesgos que siguen abiertos.
Escenarios de aceptación, criterios de rechazo, trazabilidad y limitaciones: [docs/aceptacion.md](fullstack/docs/aceptacion.md) (FULL-24).

## [1.0.0] — 2026-11-03

Primera versión (commit `791290f`, rama `main`): «Mejorar una foto» sin cuenta.

- `POST /analisis` (campo `file`, JPEG/PNG/WEBP hasta 10 MB) → PNG enderezado, sin ruido y con
  contraste; `GET /salud`; errores `{error:{codigo,mensaje}}`.
- Interfaz estática (`index.html` + `front/`) con cámara, arrastrar y soltar, diseño adaptable.
- Pruebas del backend, de la interfaz y de integración; documentación de arquitectura y API.
