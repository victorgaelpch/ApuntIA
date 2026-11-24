# [BACK-21] Construir API de análisis y generación de apuntes con estado de tareas y errores

- Numero de Issue: #64
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/64
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:34:43 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:27 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:27 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:34:43Z
- Cierre UTC: 2026-11-10T17:02:27Z

- Fecha de captura: 2026-11-24 12:07:28 -0600 (CDMX)
- [Captura original](%5BBACK-21%5D%20Construir%20API%20de%20an%C3%A1lisis%20y%20generaci%C3%B3n%20de%20apuntes%20con%20estado%20de%20tareas%20y%20errores-original.png)
- [Captura con metadatos](%5BBACK-21%5D%20Construir%20API%20de%20an%C3%A1lisis%20y%20generaci%C3%B3n%20de%20apuntes%20con%20estado%20de%20tareas%20y%20errores.png)

## Descripcion original

## Objetivo
Exponer rutas FastAPI versionadas para crear trabajos, consultar extracción, guardar correcciones, añadir investigación y solicitar exportación PDF. Mantener contratos HTTP estables y escalables.

## Contexto técnico y alcance
No modificar `POST /analisis` (respuesta PNG) ni `GET /salud`. El nuevo flujo puede tardar mucho más que una petición de mejora de imagen y exige gestión de estados/errores consistente.

## Actividades detalladas
- [ ] Implementar routers versionados y separar lógica de servicios, validación, persistencia, OCR y PDF.
- [ ] Crear endpoints de carga multipágina, inicio/análisis, estado de trabajo, documento estructurado, correcciones, enriquecimiento y exportación.
- [ ] Definir estados, progresos y error por etapa; considerar 202 Accepted y polling para trabajos largos sin cerrar conexiones prematuramente.
- [ ] Asignar IDs no predecibles/UUIDs para trabajo y nota, pero sin confiar en ello para autorización.
- [ ] Implementar límites de concurrencia, tamaño, timeouts, cancelación y reintentos idempotentes que no generen documentos duplicados.
- [ ] Reutilizar el formato de error `{error:{codigo,mensaje}}` y añadir códigos específicos sin trazas internas.
- [ ] Validar contratos de archivo/JSON y contenidos esperados con Pydantic, versionado e OpenAPI.
- [ ] Alinear cabeceras, CORS, caché y descarga `application/pdf` sin exponer documentos a público.
- [ ] Evitar tareas `BackgroundTasks` no durables si se exige supervivencia al reinicio: elegir almacenamiento/cola conforme a requisitos.
- [ ] Documentar ejemplos curl y rutas frontend, estados de fallo y backwards compatibility.

## Criterios de aceptación
- [ ] Los flujos nuevos se ejecutan mediante API documentada, con estados legibles por el cliente.
- [ ] Un error de OCR o investigación no es un HTTP 200 con contenido fingido; se documenta el estado parcial.
- [ ] Los reintentos no duplican trabajos/PDFs de manera accidental.
- [ ] Los endpoints originales y estructura de errores siguen funcionando.

## Pruebas y verificación obligatoria
- Tests TestClient/httpx para éxito, progreso, error, timeout, reintento, cancelación y contenido incorrecto.
- Pruebas de concurrencia y contrato v1/v2.
- Smoke de generación y descarga de PDF real.

## Archivos y entregables esperados
- Routers y servicios de orquestación versionados.
- OpenAPI, ejemplos de request/response.
- Pruebas integradas con mocks de OCR y PDF.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-15; BACK-11..BACK-20.
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

![Captura del Issue #64](%5BBACK-21%5D%20Construir%20API%20de%20an%C3%A1lisis%20y%20generaci%C3%B3n%20de%20apuntes%20con%20estado%20de%20tareas%20y%20errores.png)
