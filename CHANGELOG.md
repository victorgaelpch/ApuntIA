# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versiones
[semánticas](https://semver.org/lang/es/). La versión se ve en `GET /salud` (`"version"`).
Cómo se publica una versión: [docs/entrega.md](docs/entrega.md#6-lista-de-comprobación-de-la-versión).

## [Sin publicar]

### Añadido

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

- El análisis tarda más: ~1 s por foto en la mediana (antes ~0,4 s). Límites configurables con
  `RECONOCIMIENTO_MAX_VARIANTES`, `RECONOCIMIENTO_MAX_BLOQUES` y `RECONOCIMIENTO_MAX_SEGUNDOS`.
- Igualdades cortas como `F = ma` se detectan como fórmula.

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

Auditoría completa (FULL-20) en [docs/seguridad.md](docs/seguridad.md), con los riesgos que siguen abiertos.
Escenarios de aceptación, criterios de rechazo, trazabilidad y limitaciones: [docs/aceptacion.md](docs/aceptacion.md) (FULL-24).

## [1.0.0] — 2026-11-03

Primera versión (commit `791290f`, rama `main`): «Mejorar una foto» sin cuenta.

- `POST /analisis` (campo `file`, JPEG/PNG/WEBP hasta 10 MB) → PNG enderezado, sin ruido y con
  contraste; `GET /salud`; errores `{error:{codigo,mensaje}}`.
- Interfaz estática (`index.html` + `front/`) con cámara, arrastrar y soltar, diseño adaptable.
- Pruebas del backend, de la interfaz y de integración; documentación de arquitectura y API.
