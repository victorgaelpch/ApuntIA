# Plan de integración frontend ↔ backend (FULL-02)

Documento vivo: hay que actualizarlo en cada PR que cambie el estado de un issue, una decisión o un bloqueo.
Referencias: [flujo](flujo.md) · [contrato de la API](api.md) · [pruebas del frontend](../../front/docs/pruebas-frontend.md).

## 1. Estado de avance

| Área | Issue | Estado | Dónde |
|------|-------|--------|-------|
| Full | FULL-01 Flujo | ✅ Propuesta escrita · ⏳ acuerdo del equipo | `fullstack/docs/flujo.md` |
| Full | FULL-03 Contrato API v1.0 | ✅ Escrito e implementado · ⏳ revisión de los responsables | `fullstack/docs/api.md` |
| Back | BACK-01 a BACK-10 | ✅ Implementados, 70 pruebas en verde | `back/motori_magenes` |
| Front | FRONT-01 a FRONT-10 | ✅ Implementados, 20 pruebas en verde (Chromium) | `index.html`, `front/` |
| Full | FULL-04 a FULL-08 | ✅ Integración, flujo, compatibilidad, pruebas e incidencias | `fullstack/docs/ejecutar.md`, `fullstack/docs/compatibilidad.md`, `fullstack/docs/pruebas-integracion.md`, `fullstack/docs/incidencias.md` |
| Full | FULL-09 Validación de UX | ✅ En dispositivos emulados · ⏳ celulares reales | `fullstack/docs/validacion-ux.md` |
| Full | FULL-10 Arquitectura | ✅ | `fullstack/docs/arquitectura.md`, `README.md` |

## 2. Ramas y entregas

**Convención propuesta:**
- Una rama por issue, creada desde `main` con el formato `<area>-<nn>-<descripcion>`, por ejemplo `back-02-validacion` o `front-07-carga`.
- Commits con el prefijo del issue: `[BACK-02] Implementa la carga y validación…`.
- PR hacia `main` con `Closes #<n>` y evidencias (pruebas, capturas o ejemplos de petición).
- Al menos **una revisión de la otra área** cuando el PR toca el contrato. Por ejemplo, un cambio de backend que afecta al frontend lo revisa alguien de frontend.

**Entregas parciales** (en orden de dependencias, según `fullstack/docs/flujo.md`):

| Entrega | Contenido | Se verifica con |
|---------|-----------|-----------------|
| E1: Base | BACK-01, FRONT-01, FULL-01, FULL-03 | El servidor arranca; la página carga; contrato escrito |
| E2: Capas por separado | BACK-02…10 · FRONT-02…10 | `python -m pytest` (70) · `npm run test:front` (20), con la API simulada |
| E3: Integración | FULL-04, FULL-05, FULL-06 | Petición real desde el navegador a FastAPI |
| E4: Validación | FULL-07, FULL-08, FULL-09, FULL-10 | `npm run test:integracion` y recorrido manual en dispositivos |

> **Nota sobre esta entrega:** el trabajo se desarrolló en la rama `claude/vibrant-ptolemy-jiqdp7` con **un commit por issue**,
> cada uno con `Refs victorgaelpch/ApuntIA#<n>`. Si el equipo prefiere un PR por issue, se puede crear una rama por
> commit con `git cherry-pick`, respetando el orden de dependencias.

## 3. Pruebas conjuntas

| Cuándo | Prueba | Participantes | Cómo |
|--------|--------|---------------|------|
| Tras E2 | Contrato | Back + Front | Comparar peticiones reales con `fullstack/docs/api.md` (FULL-06) |
| Tras E3 | Integración automatizada | Full | `npm run test:integracion` con los dos servicios levantados (FULL-07) |
| Tras E3 | Recorrido en dispositivos | Todo el equipo | Lista de validación de FULL-09: un Android, un iPhone y una laptop |
| Antes de entregar | Prueba desde cero | Alguien que no haya desarrollado | Seguir solo el README raíz (FULL-10) |

## 4. Bloqueos y riesgos

| # | Bloqueo / riesgo | Afecta a | Responsable | Estado |
|---|------------------|----------|-------------|--------|
| B1 | El backend no expone las cabeceras `X-ApuntIA-*` por CORS: el navegador no ve si la perspectiva se corrigió ni las dimensiones | FRONT-06, FULL-04 | Full / Back | ✅ Resuelto en FULL-04 |
| B2 | Contrato y flujo pendientes de aprobación formal del equipo | FULL-01, FULL-03 | Responsables de cada área | ⏳ Abierto |
| B3 | Cámara en vivo (`getUserMedia`) solo en `https` o `localhost`; desde el celular por `http://<ip>` se usa la app de cámara | FRONT-03, FULL-09 | Front | Mitigado (alternativa automática); documentado |
| B4 | Fotos HEIC de iPhone no admitidas | BACK-02, FRONT-08 | Back | Mitigado: mensaje con instrucciones; HEIC queda fuera del alcance v1 |
| B5 | Pruebas en Firefox, Safari y celulares reales no ejecutadas | FRONT-10, FULL-09 | Todo el equipo | ⏳ Abierto |
| B6 | Fotos reales donde el pizarrón se sale del encuadre: no se endereza | BACK-04 | Back | Limitación documentada; mejora futura con rectas de Hough |
| B7 | La bitácora de los issues (fecha, tiempo, dificultades) debe escribirla cada responsable en los comentarios de GitHub | Todos | Cada responsable | ⏳ Abierto |

## 5. Registro de decisiones

| Fecha | Decisión | Motivo | Issue |
|-------|----------|--------|-------|
| 2026-11-03 | El resultado se devuelve como **PNG binario** en la respuesta, sin guardarlo en el servidor | Sin almacenamiento ni limpieza de temporales; sin URLs que caduquen | FULL-03, BACK-02 |
| 2026-11-03 | Validación por **firma binaria** en las dos capas; el backend es la fuente de verdad | El `accept` y la extensión se pueden falsear | BACK-02, FRONT-02 |
| 2026-11-03 | Errores con la estructura única `{"error": {"codigo", "mensaje"}}`; el frontend decide el texto según el `codigo` | Mensajes coherentes y desacoplados del texto del servidor | FULL-03, BACK-07, FRONT-08 |
| 2026-11-03 | Filtro de ruido por defecto: `combinado` (mediana + bilateral) en lugar de `bilateral` | 36.2 dB frente a 23.0 dB de PSNR con ruido de cámara | BACK-06 (cambio del contrato) |
| 2026-11-03 | Procesar con un lado máximo de 2000 px | 5.8 veces más rápido en fotos de 12 MP sin perder legibilidad | BACK-09 |
| 2026-11-03 | Frontend con scripts clásicos (sin módulos ES) y URL de la API configurable | Funciona con doble clic (`file://`) y desde el celular en la red local | FRONT-05 |
| 2026-11-03 | `api-mock.js` para trabajar el frontend sin backend | Avance en paralelo y pruebas reproducibles | FRONT-05, FRONT-10 |

## 6. Reglas de colaboración

- **No modificar trabajo ajeno sin coordinarlo:** si un cambio toca un archivo de otra área (por ejemplo, el frontend necesita un cambio en `fullstack/docs/api.md` o en el backend), se comenta en el issue correspondiente y se pide revisión a su responsable.
- **El contrato es la frontera:** cualquier cambio de ruta, campo, código de error o cabecera se refleja en `fullstack/docs/api.md` **en el mismo PR**, y también en el mock (`front/js/api-mock.js`) y en las pruebas.
- **No se marca un issue como Done** sin sus pruebas en verde y su evidencia (ver la sección «Cierre» de cada issue).
