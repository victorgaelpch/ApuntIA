# [FULL-24] Validar alcance educativo con escenarios reales y preparar evidencia de entrega

- Numero de Issue: #54
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/54
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:28:19 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:22 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:22 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:28:19Z
- Cierre UTC: 2026-11-10T17:05:22Z

- Fecha de captura: 2026-11-24 12:06:41 -0600 (CDMX)
- [Captura original](%5BFULL-24%5D%20Validar%20alcance%20educativo%20con%20escenarios%20reales%20y%20preparar%20evidencia%20de%20entrega-original.png)
- [Captura con metadatos](%5BFULL-24%5D%20Validar%20alcance%20educativo%20con%20escenarios%20reales%20y%20preparar%20evidencia%20de%20entrega.png)

## Descripcion original

## Objetivo
Cerrar el ciclo de calidad mediante casos de aceptación representativos del uso educativo, evitando declarar terminado algo que no extrae correctamente texto/fórmulas ni produce PDFs útiles.

## Contexto técnico y alcance
La nueva promesa del producto es transformar pizarrones y cuadernos en notas editables, completadas con información verificada y exportables, con cuentas e historial. Debe demostrarse con resultados reales, no pantallas simuladas.

## Actividades detalladas
- [ ] Diseñar escenarios de aceptación: pizarrón corto, cuaderno manuscrito, imagen difícil, hoja impresa, fórmula, tabla, diagrama y varias páginas.
- [ ] Evaluar recorrido sin investigación y con investigación opcional, con citas y aviso de limitaciones.
- [ ] Revisar con un usuario externo la corrección de OCR, vista previa, edición, PDF, guardado y recuperación desde historial.
- [ ] Crear matriz requisito -> Issue -> endpoint -> test -> evidencia; distinguir completo/parcial/pendiente.
- [ ] Asegurar accesibilidad básica, comprensión de errores y funcionamiento desde teléfono y PC compatibles.
- [ ] Preparar demo offline o fallback cuando servicio externo no esté disponible, sin simular información como real.
- [ ] Crear criterios de parada/rechazo: PDF vacío, pérdida de fórmula, cita inventada, acceso a notas ajenas, arranque imposible.
- [ ] Registrar bugs con pasos de reproducción y prioridad; reabrir Issues afectados si corresponde.
- [ ] Preparar manual de usuario, capturas, enlaces a PR y registro de resultados de evaluación.

## Criterios de aceptación
- [ ] Se cumplen escenarios completos con casos reales/permitidos y sus resultados quedan documentados.
- [ ] No se presentan como completas funciones aún simuladas o sin pruebas.
- [ ] Se comprueban arranque, seguridad, persistencia y calidad básica de salida.
- [ ] Existe evidencia auditable para la evaluación del profesor.

## Pruebas y verificación obligatoria
- Sesiones de aceptación por usuarios distintos al desarrollador.
- Regresión completa automatizada más inspección manual de PDFs, fórmulas y citas.
- Ensayo de entrega desde máquina limpia.

## Archivos y entregables esperados
- Matriz de aceptación y reporte final de resultados.
- Casos de prueba y evidencias sin datos privados.
- Guía de demostración y lista de limitaciones actuales.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-16, FULL-18, FULL-19, FULL-22.
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

![Captura del Issue #54](%5BFULL-24%5D%20Validar%20alcance%20educativo%20con%20escenarios%20reales%20y%20preparar%20evidencia%20de%20entrega.png)
