# [BACK-17] Crear modelo intermedio editable de apuntes con confianza y trazabilidad

- Numero de Issue: #60
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/60
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:33:32 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:21 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:21 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:33:32Z
- Cierre UTC: 2026-11-10T17:02:21Z

- Fecha de captura: 2026-11-24 12:07:12 -0600 (CDMX)
- [Captura original](%5BBACK-17%5D%20Crear%20modelo%20intermedio%20editable%20de%20apuntes%20con%20confianza%20y%20trazabilidad-original.png)
- [Captura con metadatos](%5BBACK-17%5D%20Crear%20modelo%20intermedio%20editable%20de%20apuntes%20con%20confianza%20y%20trazabilidad.png)

## Descripcion original

## Objetivo
Construir una representación única, versionable y validada de cada apunte, separando lo que realmente aparece en la imagen de las correcciones del usuario y de la información adicional investigada.

## Contexto técnico y alcance
El backend no debe generar PDF directamente desde texto OCR desordenado. El modelo intermedio permite revisión, historiales, exportación y pruebas de calidad sin duplicación de lógica.

## Actividades detalladas
- [ ] Definir esquemas Pydantic/JSON: documento, fuente, página, bloque, texto, fórmula, tabla, diagrama, citas, revisiones, exportaciones.
- [ ] Incluir identificadores estables, orden de lectura, región, confianza, idioma, modelo y versión; evitar valores desconocidos inventados.
- [ ] Separar campos `extraido`, `corregido_por_usuario`, `complemento_investigado` y `contenido_generado` con historial de cambios.
- [ ] Implementar reglas de validación: títulos y tamaño, referencias existentes, coherencia de páginas y límites de bloques.
- [ ] Aplicar normalización Unicode, puntuación y espaciado sin alterar expresiones matemáticas ni corregir contenido académico sin aprobación.
- [ ] Definir edición y validación para texto, LaTeX, tablas y esquema; registrar autor, fecha y versión con restricciones de permisos.
- [ ] Proveer serialización/deserialización estable y versionada, compatible con almacenamiento y frontend.
- [ ] Implementar política de contenido no reconocido y revisión requerida sin pérdida de imagen original.
- [ ] Crear fixtures JSON representativas, documentación y ejemplos de transformación de imagen a documento.

## Criterios de aceptación
- [ ] Un documento puede corregirse y volver a serializarse sin perder bloques ni procedencia.
- [ ] El contenido investigado no se confunde con el extraído de la fotografía.
- [ ] Las fórmulas y tablas sobreviven a la exportación/importación del modelo.
- [ ] Esquemas inválidos se rechazan con errores claros sin modificar el documento previo.

## Pruebas y verificación obligatoria
- Round-trip JSON y validaciones maliciosas/incorrectas.
- Pruebas con caracteres Unicode, LaTeX, tabla, orden multi página y edición concurrente.
- Tests de migración de versión de esquema.

## Archivos y entregables esperados
- Esquemas y servicios de transformación con tests.
- Ejemplos JSON y tabla de compatibilidad.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-15; BACK-13..BACK-16.
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

![Captura del Issue #60](%5BBACK-17%5D%20Crear%20modelo%20intermedio%20editable%20de%20apuntes%20con%20confianza%20y%20trazabilidad.png)
