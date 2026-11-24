# [BACK-27] Crear gestor de trabajos durables para OCR y PDF con cancelación y límites

- Numero de Issue: #70
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/70
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:36:51 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:35 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:35 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:36:51Z
- Cierre UTC: 2026-11-10T17:02:35Z

- Fecha de captura: 2026-11-24 12:07:52 -0600 (CDMX)
- [Captura original](%5BBACK-27%5D%20Crear%20gestor%20de%20trabajos%20durables%20para%20OCR%20y%20PDF%20con%20cancelaci%C3%B3n%20y%20l%C3%ADmites-original.png)
- [Captura con metadatos](%5BBACK-27%5D%20Crear%20gestor%20de%20trabajos%20durables%20para%20OCR%20y%20PDF%20con%20cancelaci%C3%B3n%20y%20l%C3%ADmites.png)

## Descripcion original

## Objetivo
Administrar procesos costosos de OCR/manuscrito/matemáticas/PDF sin bloquear indebidamente la API, con estados persistentes, cancelación, reintento seguro y límites de concurrencia.

## Contexto técnico y alcance
`BackgroundTasks` sin persistencia puede perder trabajo tras un reinicio. Elegir diseño proporcional (cola persistente, worker dedicado o gestor durable sencillo) y que opere tanto con scripts como Docker, justificando dependencias.

## Actividades detalladas
- [ ] Estimar recursos de OCR/PDF y definir límites documentados por tamaño/páginas/usuarios.
- [ ] Elegir backend de ejecución adecuado y persistir ID, propietario, etapa, progreso, tiempos y fallos.
- [ ] Implementar encolado, estado, cancelación, política de reintentos con backoff e idempotencia.
- [ ] Evitar que dos workers generen la misma exportación simultáneamente o procesen una nota borrada.
- [ ] Aislar modelos grandes, limitar concurrencia y liberar memoria/temporales al terminar o cancelar.
- [ ] Recuperar trabajos tras reinicio según política documentada: reanudar, reintentar o marcar fallo recuperable.
- [ ] Devolver errores por etapa y estimación solo si se puede medir, nunca declarar listo sin archivo válido.
- [ ] Integrar seguimiento con `job_id` en API, logs, UI y dashboard.
- [ ] Probar cierre controlado con los scripts y contenedores de fullstack.

## Criterios de aceptación
- [ ] Los trabajos reportan estados reales y pueden recuperarse tras fallo de proceso según política.
- [ ] Reintentar no duplica notas/PDFs; cancelar no deja recursos huérfanos.
- [ ] La API responde mientras el reconocimiento está ocupado y aplica límites para evitar agotamiento.
- [ ] Modo local y Docker funcionan con la misma interfaz externa.

## Pruebas y verificación obligatoria
- Simular reinicio a mitad de OCR, dos trabajos duplicados, cancelación, timeout y disco lleno.
- Pruebas de concurrencia y limpieza de temporales.
- Tests de estado desde API y persistencia de trabajos.

## Archivos y entregables esperados
- Gestor de tareas, configuración y pruebas.
- Diagrama de estados y guía operativa.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-21, BACK-22, FULL-21.
- **Área responsable:** backend.
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

![Captura del Issue #70](%5BBACK-27%5D%20Crear%20gestor%20de%20trabajos%20durables%20para%20OCR%20y%20PDF%20con%20cancelaci%C3%B3n%20y%20l%C3%ADmites.png)
