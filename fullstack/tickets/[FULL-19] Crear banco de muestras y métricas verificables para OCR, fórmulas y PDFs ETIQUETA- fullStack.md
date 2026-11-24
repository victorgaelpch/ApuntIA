# [FULL-19] Crear banco de muestras y métricas verificables para OCR, fórmulas y PDFs ETIQUETA: fullStack

- Numero de Issue: #49
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/49
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:25:53 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:14 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:14 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:25:53Z
- Cierre UTC: 2026-11-10T17:05:14Z

- Fecha de captura: 2026-11-24 12:06:12 -0600 (CDMX)
- [Captura original](%5BFULL-19%5D%20Crear%20banco%20de%20muestras%20y%20m%C3%A9tricas%20verificables%20para%20OCR%2C%20f%C3%B3rmulas%20y%20PDFs%20ETIQUETA-%20fullStack-original.png)
- [Captura con metadatos](%5BFULL-19%5D%20Crear%20banco%20de%20muestras%20y%20m%C3%A9tricas%20verificables%20para%20OCR%2C%20f%C3%B3rmulas%20y%20PDFs%20ETIQUETA-%20fullStack.png)

## Descripcion original

## Objetivo
Definir un conjunto de evaluación reproducible para medir la calidad real de reconocimiento, estructura documental y exportación; priorizar correcciones por evidencia, no por impresiones.

## Contexto técnico y alcance
El procesamiento OpenCV actual mejora imagen, pero eso no demuestra extracción de texto ni de matemáticas. Se requieren ejemplos etiquetados y métricas comparables, sin incluir fotografías reales privadas en un repositorio público.

## Actividades detalladas
- [ ] Crear categorías de imágenes: pizarrón, libreta rayada/cuadriculada, impreso, manuscrito, inclinación, sombras, iluminación, múltiples páginas, fórmulas y diagramas.
- [ ] Crear muestras sintéticas y/o con autorización de uso, con verdades de referencia (`ground_truth`) en texto, LaTeX y estructura.
- [ ] Definir CER/WER para texto; exactitud/validación de LaTeX y revisión semántica para fórmulas; recuperación de bloques/orden para estructura.
- [ ] Definir chequeos de PDF: número de páginas, texto seleccionable, fuentes Unicode, tablas completas, fórmulas visibles, enlaces y metadatos.
- [ ] Establecer línea base real de cada motor por tipo de fuente y reportar fallos; acordar metas antes de afirmar calidad.
- [ ] Automatizar evaluación en scripts de `fullstack/tests/` con salida CSV/JSON/HTML, versiones de modelos y tiempos.
- [ ] Registrar consumo de memoria, tiempo, tasa de errores y comportamiento ante archivos inválidos o muy grandes.
- [ ] Añadir conjunto de regresión para los errores reales observados por el equipo.
- [ ] Separar resultados estimados/manuales de métricas computadas; documentar limitaciones de reconocimiento manuscrito.
- [ ] Actualizar tablero de criterios de aceptación y decisiones de modelo según coste, privacidad y calidad.

## Criterios de aceptación
- [ ] Hay un corpus legal y reproducible que evalúa tanto pizarrones como cuadernos y fórmulas.
- [ ] Existe una línea base obtenida con comando documentado y resultados legibles.
- [ ] Los informes distinguen reconocimiento correcto, incierto y fallido; no inventan métricas.
- [ ] Los cambios significativos de OCR/PDF presentan comparación antes/después y regresiones.

## Pruebas y verificación obligatoria
- Ejecutar evaluación dos veces para comprobar determinismo del procedimiento (sin exigir predicciones idénticas si el motor no lo permite).
- Inspeccionar manualmente muestras difíciles y varios lectores PDF.
- Comprobar que no haya materiales privados o con licencias incompatibles.

## Archivos y entregables esperados
- Fixtures etiquetadas y guía de uso.
- Script de evaluación y resultados de referencia.
- Matriz de calidad y reporte de limitaciones.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-11..BACK-16, BACK-20, FULL-17.
- **Área responsable:** fullStack.
- **Prioridad:** Alta.

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

![Captura del Issue #49](%5BFULL-19%5D%20Crear%20banco%20de%20muestras%20y%20m%C3%A9tricas%20verificables%20para%20OCR%2C%20f%C3%B3rmulas%20y%20PDFs%20ETIQUETA-%20fullStack.png)
