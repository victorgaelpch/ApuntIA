# [BACK-26] Crear endpoints seguros de historial, búsqueda, edición y descarga de apuntes

- Numero de Issue: #69
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/69
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:36:33 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:33 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:34 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:36:33Z
- Cierre UTC: 2026-11-10T17:02:33Z

- Fecha de captura: 2026-11-24 12:07:49 -0600 (CDMX)
- [Captura original](%5BBACK-26%5D%20Crear%20endpoints%20seguros%20de%20historial%2C%20b%C3%BAsqueda%2C%20edici%C3%B3n%20y%20descarga%20de%20apuntes-original.png)
- [Captura con metadatos](%5BBACK-26%5D%20Crear%20endpoints%20seguros%20de%20historial%2C%20b%C3%BAsqueda%2C%20edici%C3%B3n%20y%20descarga%20de%20apuntes.png)

## Descripcion original

## Objetivo
Ofrecer API privada para que cada usuario consulte apuntes anteriores, los busque, edite, recupere versiones, regenere PDFs y elimine materiales, usando datos persistentes.

## Contexto técnico y alcance
No confundir descarga temporal de PNG con historial de documentos. Los nuevos endpoints deben usar la base de datos/almacenamiento definido y proteger autorización en cada consulta.

## Actividades detalladas
- [ ] Diseñar e implementar rutas CRUD versionadas para notas del usuario, detalle, actualización, archivado/borrado y restauración si se aprueba.
- [ ] Agregar listado paginado y orden por fecha de creación/actualización, estado y búsqueda por título/tags.
- [ ] Diseñar recuperación de fuentes, bloques, revisiones y PDF por versión, comprobando propietario.
- [ ] Implementar edición optimista con versión/ETag o estrategia equivalente para prevenir pérdida silenciosa en pestañas concurrentes.
- [ ] Actualizar exportaciones al cambiar el contenido y permitir regeneración de PDF desde versión exacta.
- [ ] Devolver nombres de archivo seguros, tipo `application/pdf` y cabeceras anti-cache para contenido privado cuando aplique.
- [ ] Separar metadatos listables de contenido completo para evitar cargar archivos costosos en el dashboard.
- [ ] Definir estados para notas incompletas, fallidas y listas, y borrado de todos los recursos asociados.
- [ ] Documentar DTO, códigos de error, paginación y filtros en OpenAPI.

## Criterios de aceptación
- [ ] Cada usuario ve, modifica, busca y descarga únicamente sus propias notas.
- [ ] Las ediciones concurrentes no pisan cambios silenciosamente.
- [ ] Las URLs privadas no permiten descarga sin autorización.
- [ ] El historial muestra el último estado correcto después de reinicios.

## Pruebas y verificación obligatoria
- Pruebas con dos cuentas, lista paginada, búsqueda, nota borrada y versionado.
- Descarga con sesión expirada, PDF regenerado y URL adivinada.
- Tests de conflicto en edición concurrente.

## Archivos y entregables esperados
- Endpoints de notas/historial y servicio de exportación privada.
- OpenAPI y tests CRUD/seguridad.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-17, BACK-20..BACK-24.
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

![Captura del Issue #69](%5BBACK-26%5D%20Crear%20endpoints%20seguros%20de%20historial%2C%20b%C3%BAsqueda%2C%20edici%C3%B3n%20y%20descarga%20de%20apuntes.png)
