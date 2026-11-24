# [FULL-21] Agregar diagnósticos, métricas y manejo de fallos del sistema completo

- Numero de Issue: #51
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/51
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:27:02 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:17 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:17 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:27:02Z
- Cierre UTC: 2026-11-10T17:05:17Z

- Fecha de captura: 2026-11-24 12:06:23 -0600 (CDMX)
- [Captura original](%5BFULL-21%5D%20Agregar%20diagn%C3%B3sticos%2C%20m%C3%A9tricas%20y%20manejo%20de%20fallos%20del%20sistema%20completo-original.png)
- [Captura con metadatos](%5BFULL-21%5D%20Agregar%20diagn%C3%B3sticos%2C%20m%C3%A9tricas%20y%20manejo%20de%20fallos%20del%20sistema%20completo.png)

## Descripcion original

## Objetivo
Facilitar que el equipo y el profesor comprendan el estado de ApuntIA y los problemas reales cuando OCR, reconocimiento matemático, PDF o servicios externos fallen.

## Contexto técnico y alcance
La API ya cuenta con `GET /salud` y errores normalizados; extender diagnósticos sin filtrar datos confidenciales ni reemplazar el contrato anterior.

## Actividades detalladas
- [ ] Diseñar `request_id`/`job_id` consistente para frontend, backend y exportaciones.
- [ ] Definir logs estructurados para cargas, OCR, investigación, render PDF, autenticación y errores, con redacción de información sensible.
- [ ] Agregar métricas de latencia por etapa, uso de memoria, tamaño de archivo, tasa de éxito, errores y tareas pendientes.
- [ ] Mantener `/salud` compatible e incorporar readiness separada cuando existan base de datos, modelos y colas.
- [ ] Explicar diferencia entre app viva y dependencias listas, con timeouts y mensajes accionables.
- [ ] Incorporar diagnóstico desde scripts locales y Docker, con logs fáciles de obtener.
- [ ] Establecer límites y alertas sencillas ante tiempos excesivos y agotamiento de disco.
- [ ] Mostrar en UI error identificable por código sin exponer stacktraces.
- [ ] Documentar manejo de información de producción, conservación de logs y cómo reproducir un fallo.

## Criterios de aceptación
- [ ] Se puede correlacionar un fallo desde interfaz hasta API usando un identificador no sensible.
- [ ] La app no reporta listo si una dependencia obligatoria está caída.
- [ ] Los logs no incluyen contraseñas, imágenes completas, texto privado ni tokens.
- [ ] El contrato original de `GET /salud` sigue siendo utilizable.

## Pruebas y verificación obligatoria
- Simular caída de OCR/PDF/base de datos y comprobar códigos, mensajes, logs y limpieza.
- Verificar carga alta y temporales residuales.
- Revisar logs de una sesión real para descartar filtraciones.

## Archivos y entregables esperados
- Instrumentación y guías de diagnóstico.
- Pruebas de fallos simulados y reportes de métricas.
- Actualización de health/readiness y README.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-16, FULL-17, BACK-21.
- **Área responsable:** fullStack.
- **Prioridad:** Media.

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

![Captura del Issue #51](%5BFULL-21%5D%20Agregar%20diagn%C3%B3sticos%2C%20m%C3%A9tricas%20y%20manejo%20de%20fallos%20del%20sistema%20completo.png)
