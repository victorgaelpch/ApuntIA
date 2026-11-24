# [BACK-22] Implementar base de datos y almacenamiento privado para usuarios, apuntes, versiones y PDFs

- Numero de Issue: #65
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/65
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:35:07 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:28 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:28 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:35:07Z
- Cierre UTC: 2026-11-10T17:02:28Z

- Fecha de captura: 2026-11-24 12:07:33 -0600 (CDMX)
- [Captura original](%5BBACK-22%5D%20Implementar%20base%20de%20datos%20y%20almacenamiento%20privado%20para%20usuarios%2C%20apuntes%2C%20versiones%20y%20PDFs-original.png)
- [Captura con metadatos](%5BBACK-22%5D%20Implementar%20base%20de%20datos%20y%20almacenamiento%20privado%20para%20usuarios%2C%20apuntes%2C%20versiones%20y%20PDFs.png)

## Descripcion original

## Objetivo
Añadir persistencia del historial de apuntes y sus archivos asociados, con relaciones claras de propietario, fuente, extracción, ediciones, enriquecimientos y exportaciones.

## Contexto técnico y alcance
El diseño actual no guarda resultados. Seleccionar una tecnología proporcionada al proyecto (por ejemplo SQLite en desarrollo y configuración preparada para PostgreSQL si se decide), usando migraciones y no archivos públicos accesibles directamente.

## Actividades detalladas
- [ ] Modelar entidades Usuario, Nota, Pagina/Fuente, Bloque, Revision, Trabajo, Exportacion y ReferenciaInvestigacion.
- [ ] Definir relaciones e índices por propietario/fecha/estado para historial y búsquedas eficientes.
- [ ] Implementar ORM/repository y migraciones versionadas, controlando actualizaciones sin destruir datos.
- [ ] Guardar originales y PDFs en almacenamiento privado con rutas basadas en IDs y nombres seguros; no exponer archivos bajo el frontend.
- [ ] Implementar guardado transaccional de notas y versiones, con estado correcto si falla la escritura de archivos.
- [ ] Definir política de temporales, cuotas, tamaños, limpieza, retención y borrado por usuario.
- [ ] Configurar rutas/volúmenes según modo local y Docker, con permisos mínimos y sin secretos en Git.
- [ ] Permitir exportaciones regenerables y registrar checksum/fecha de origen, versión de nota y formato.
- [ ] Prever copia/restauración con FULL-23 e integridad referencial.
- [ ] Documentar esquema y límites de persistencia para desarrollo/evaluación.

## Criterios de aceptación
- [ ] Notas, correcciones y PDF siguen disponibles tras reiniciar servicios.
- [ ] Los metadatos y archivos están correctamente vinculados al propietario.
- [ ] Los temporales se limpian; las rutas privadas no se sirven directamente al público.
- [ ] Las migraciones son repetibles y contemplan fallos controlados.

## Pruebas y verificación obligatoria
- CRUD y relectura tras reinicio, integridad de borrado y edición concurrente.
- Fallo a mitad de escritura para comprobar consistencia.
- Acceso anónimo a carpetas y backup/restore en entorno de prueba.

## Archivos y entregables esperados
- Modelos, migraciones, repositorios, configuración de almacenamiento.
- Tests de persistencia y esquema de datos documentado.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-15; BACK-17; FULL-23 coordinación.
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

![Captura del Issue #65](%5BBACK-22%5D%20Implementar%20base%20de%20datos%20y%20almacenamiento%20privado%20para%20usuarios%2C%20apuntes%2C%20versiones%20y%20PDFs.png)
