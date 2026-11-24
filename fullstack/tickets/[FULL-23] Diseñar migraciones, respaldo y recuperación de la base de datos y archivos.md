# [FULL-23] Diseñar migraciones, respaldo y recuperación de la base de datos y archivos

- Numero de Issue: #53
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/53
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:28:00 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:20 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:20 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:28:00Z
- Cierre UTC: 2026-11-10T17:05:20Z

- Fecha de captura: 2026-11-24 12:06:34 -0600 (CDMX)
- [Captura original](%5BFULL-23%5D%20Dise%C3%B1ar%20migraciones%2C%20respaldo%20y%20recuperaci%C3%B3n%20de%20la%20base%20de%20datos%20y%20archivos-original.png)
- [Captura con metadatos](%5BFULL-23%5D%20Dise%C3%B1ar%20migraciones%2C%20respaldo%20y%20recuperaci%C3%B3n%20de%20la%20base%20de%20datos%20y%20archivos.png)

## Descripcion original

## Objetivo
Garantizar evolución del modelo de datos, persistencia segura y recuperación de notas/PDFs sin pérdidas cuando el sistema se reinicia, actualiza o cambia de modo de ejecución.

## Contexto técnico y alcance
La versión actual no persiste resultados de `/analisis`; al agregar cuentas e historial hay que decidir base de datos, archivos y migraciones. Evitar introducir bases paralelas o almacenamiento no documentado.

## Actividades detalladas
- [ ] Analizar ORM/base de datos seleccionada por backend; preferir una sola fuente de verdad y migraciones versionadas.
- [ ] Establecer rutas y volúmenes persistentes, permisos, partición de temporales y separación de archivos públicos/privados.
- [ ] Crear scripts migración y verificación de esquema con rollback o plan de recuperación documentado.
- [ ] Definir política de versiones de notas, PDFs regenerables, contenido fuente y borrado en cascada.
- [ ] Implementar respaldo consistente de base de datos y archivos asociados, con cifrado/acceso restringido según escenario.
- [ ] Documentar restauración local y Docker y procedimiento ante migración fallida.
- [ ] Evitar incluir backups reales en Git, contenedores o frontend estático.
- [ ] Diseñar migración si cambian ubicaciones por carpeta `fullstack/`.
- [ ] Incluir pruebas que preserven nota, propietario y PDF tras reinicio, backup/restore y actualización.

## Criterios de aceptación
- [ ] Es posible restaurar una nota completa con su propietario y archivos en un entorno limpio.
- [ ] Ninguna actualización esperada pierde datos silenciosamente y los errores de migración quedan visibles.
- [ ] Los archivos privados no son accesibles a través del servidor estático.
- [ ] Hay instrucciones y scripts probados para script local y Docker.

## Pruebas y verificación obligatoria
- Backup de muestra sintética -> eliminar entorno -> restaurar -> verificar cuenta, nota y PDF.
- Prueba de migración desde versión anterior y reinicio con volumen.
- Intentar acceso anónimo a archivos privados.

## Archivos y entregables esperados
- Migraciones/backup/restore y documentación de recuperación.
- Evidencias de persistencia en ambos modos.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-22; FULL-13; FULL-18.
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

![Captura del Issue #53](%5BFULL-23%5D%20Dise%C3%B1ar%20migraciones%2C%20respaldo%20y%20recuperaci%C3%B3n%20de%20la%20base%20de%20datos%20y%20archivos.png)
