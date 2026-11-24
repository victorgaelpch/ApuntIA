# [BACK-15] Detectar fórmulas y convertir expresiones matemáticas a LaTeX verificable

- Numero de Issue: #59
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/59
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch, I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:30:17 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:19 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:20 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:30:17Z
- Cierre UTC: 2026-11-10T17:02:19Z

- Fecha de captura: 2026-11-24 12:07:08 -0600 (CDMX)
- [Captura original](%5BBACK-15%5D%20Detectar%20f%C3%B3rmulas%20y%20convertir%20expresiones%20matem%C3%A1ticas%20a%20LaTeX%20verificable-original.png)
- [Captura con metadatos](%5BBACK-15%5D%20Detectar%20f%C3%B3rmulas%20y%20convertir%20expresiones%20matem%C3%A1ticas%20a%20LaTeX%20verificable.png)

## Descripcion original

## Objetivo
Reconocer fórmulas escritas o impresas como estructuras matemáticas —no como texto plano— y producir representaciones editables (por ejemplo LaTeX) capaces de visualizarse y exportarse fielmente.

## Contexto técnico y alcance
Alcance inicial: operaciones, fracciones, raíces, potencias, subíndices, sumatorias, integrales simples y ecuaciones; ampliar gradualmente según corpus. Evaluar motores de OCR matemático local o proveedor opcional, coste/licencias/privacidad y límites de calidad.

## Actividades detalladas
- [ ] Diseñar detector de regiones matemáticas en fotos con texto mixto, manteniendo coordenadas y página.
- [ ] Separar detección de fórmula de reconocimiento de notación; documentar ejemplos soportados y no soportados.
- [ ] Implementar adaptador de reconocimiento matemático que devuelva `latex`, texto alternativo si existe, confianza y recorte original.
- [ ] Validar sintaxis con parser/renderizador restringido; no permitir ejecución arbitraria de comandos de LaTeX ni acceso al sistema.
- [ ] Preservar operadores, paréntesis, fracciones, raíces, exponente/subíndice y alineaciones en ecuaciones.
- [ ] Evitar convertir a prosa símbolos ambiguos sin señalizar incertidumbre; ofrecer corrección posterior.
- [ ] Conservar imágenes originales cuando el motor no pueda interpretar una fórmula.
- [ ] Definir versión del modelo, idioma/notación y códigos de error específicos.
- [ ] Integrar salida en esquema de documento con tipo `formula` sin romper OCR general.
- [ ] Diseñar tests con LaTeX de referencia y render de fórmulas para PDF y vista previa.

## Criterios de aceptación
- [ ] Las fórmulas incluidas en el alcance se reconocen como bloques matemáticos editables y renderizables.
- [ ] Las ambiguas se marcan y el usuario puede corregir el código o conservar imagen.
- [ ] La entrada matemática maliciosa no ejecuta comandos ni accede a archivos.
- [ ] El PDF puede recuperar la fórmula corregida sin reinterpretarla como texto común.

## Pruebas y verificación obligatoria
- Conjunto etiquetado con fracciones, superíndices, raíces y ecuaciones mixtas.
- Comparación visual de fórmula fuente, LaTeX y PDF final.
- Inputs maliciosos, sintaxis no válida y errores de motor.

## Archivos y entregables esperados
- Detector/adaptador matemático, esquema y pruebas.
- Corpus de fórmulas y guía de edición LaTeX segura.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-12..BACK-14; FULL-15.
- **Área responsable:** backend.
- **Prioridad:** Crítica.

### Reglas obligatorias de implementación para Claude o cualquier desarrollador
- Antes de escribir código, inspeccionar la rama objetivo y el estado REAL del repositorio (`README.md`, `docs/api.md`, `docs/arquitectura.md`, `back/`, `front/`, `fullstack/` si existe, scripts, tests y PR relacionados). No asumir rutas, tecnologías o funcionalidades que no estén presentes.
- NO crear una segunda implementación si ya existe: extender, refactorizar de manera incremental y reutilizar módulos. Resolver discrepancias del código real y documentarlas en el PR.
- Conservar compatibilidad del sistema previo: `POST /analisis` recibe campo `file` y devuelve PNG; `GET /salud` y el formato `{ "error": { "codigo": "...", "mensaje": "..." } }` siguen disponibles salvo decisión explícita y versionada.
- No eliminar ni debilitar validaciones, seguridad, módulos, pruebas ni documentación existentes; no introducir rutas absolutas, claves en el repositorio ni datos privados de alumnos.
- Antes de cerrar, ejecutar tests afectados (y suites disponibles), corregir fallos, revisar integración con frontend/backend/fullstack, actualizar README/contrato/arquitectura y registrar comandos + resultados reales.
- Adjuntar en el PR evidencia reproducible, capturas o archivos sintéticos cuando correspondan, problemas detectados y decisiones técnicas; NO declarar pruebas como aprobadas sin haberlas ejecutado.

## Evidencia y bitácora
- Fecha, responsable, actividades realizadas y tiempo invertido.
- Archivos editados, endpoints/contratos afectados y motivo de cada cambio.
- Comandos de pruebas realmente ejecutados, resultados y capturas/logs saneados.
- Incidencias, soluciones, limitaciones y enlaces al Pull Request/commits.

FIN DESCRIPCION
FIN ISSUE BACK-15
======================================================================================

======================================================================================
INICIO ISSUE BACK-16
TITULO: [BACK-16] Reconstruir orden de lectura, títulos, listas, tablas, diagramas y esquemas
ETIQUETA: backend
PRIORIDAD: Crítica
DEPENDENCIAS: BACK-13..BACK-15
------------------------------------------------------------
INICIO DESCRIPCION (COPIAR A GITHUB)

## Objetivo
Detectar la estructura semántica y visual del apunte: encabezados, párrafos, listas, fórmulas, tablas, dibujos y diagramas; respetar el orden real de páginas y columnas.

## Contexto técnico y alcance
Una nota útil requiere conservar estructura, no solo extraer una cadena de palabras. Para dibujos difíciles, conservar recortes y anotaciones en vez de inventar la representación.

## Actividades detalladas
- [ ] Definir tipos de bloque (`titulo`, `parrafo`, `lista`, `formula`, `tabla`, `diagrama`, `imagen`, `desconocido`) y campos de origen.
- [ ] Analizar layout con detección de regiones y orden multi-columna; evitar mezclar texto de columnas o páginas diferentes.
- [ ] Construir tablas con filas, columnas, celdas y spans cuando sea posible; registrar ambigüedades.
- [ ] Detectar diagramas/esquemas con nodos y flechas; conservar región visual si reconstrucción no es fiable.
- [ ] Asignar IDs y bounding boxes por bloque, página y orden para permitir edición y trazabilidad.
- [ ] Distinguir títulos por evidencia visual sin introducir jerarquías arbitrarias; exponer incertidumbre.
- [ ] Retener referencias de figuras y pies con su imagen original.
- [ ] Implementar fallback sin pérdida de información: texto + recortes cuando falla layout.
- [ ] Definir cómo combinar bloques de distintas páginas sin repetir encabezados.
- [ ] Documentar contrato y ejemplos para render PDF y vista de edición.

## Criterios de aceptación
- [ ] El orden de lectura y tipo de bloque son consistentes en ejemplos con columnas, listas y tablas.
- [ ] Una tabla con filas reconocibles llega al documento como tabla, no como texto inconexo.
- [ ] Los diagramas no interpretables conservan imagen de origen con indicación.
- [ ] Cada bloque mantiene coordenadas y procedencia verificable.

## Pruebas y verificación obligatoria
- Casos de dos columnas, tabla 3x4, lista anidada, diagrama y fórmula intercalada.
- Evaluación de exactitud del orden y recorte de imágenes.
- Regresión de páginas múltiples y OCR.

## Archivos y entregables esperados
- Módulo de análisis de layout y esquemas estructurados.
- Fixtures con verdad de referencia y tests.
- Documentación de fallbacks y limitaciones.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-13..BACK-15.
- **Área responsable:** backend.
- **Prioridad:** Crítica.

### Reglas obligatorias de implementación para Claude o cualquier desarrollador
- Antes de escribir código, inspeccionar la rama objetivo y el estado REAL del repositorio (`README.md`, `docs/api.md`, `docs/arquitectura.md`, `back/`, `front/`, `fullstack/` si existe, scripts, tests y PR relacionados). No asumir rutas, tecnologías o funcionalidades que no estén presentes.
- NO crear una segunda implementación si ya existe: extender, refactorizar de manera incremental y reutilizar módulos. Resolver discrepancias del código real y documentarlas en el PR.
- Conservar compatibilidad del sistema previo: `POST /analisis` recibe campo `file` y devuelve PNG; `GET /salud` y el formato `{ "error": { "codigo": "...", "mensaje": "..." } }` siguen disponibles salvo decisión explícita y versionada.
- No eliminar ni debilitar validaciones, seguridad, módulos, pruebas ni documentación existentes; no introducir rutas absolutas, claves en el repositorio ni datos privados de alumnos.
- Antes de cerrar, ejecutar tests afectados (y suites disponibles), corregir fallos, revisar integración con frontend/backend/fullstack, actualizar README/contrato/arquitectura y registrar comandos + resultados reales.
- Adjuntar en el PR evidencia reproducible, capturas o archivos sintéticos cuando correspondan, problemas detectados y decisiones técnicas; NO declarar pruebas como aprobadas sin haberlas ejecutado.

## Evidencia y bitácora
- Fecha, responsable, actividades realizadas y tiempo invertido.
- Archivos editados, endpoints/contratos afectados y motivo de cada cambio.
- Comandos de pruebas realmente ejecutados, resultados y capturas/logs saneados.
- Incidencias, soluciones, limitaciones y enlaces al Pull Request/commits.


## Evidencia visual

![Captura del Issue #59](%5BBACK-15%5D%20Detectar%20f%C3%B3rmulas%20y%20convertir%20expresiones%20matem%C3%A1ticas%20a%20LaTeX%20verificable.png)
