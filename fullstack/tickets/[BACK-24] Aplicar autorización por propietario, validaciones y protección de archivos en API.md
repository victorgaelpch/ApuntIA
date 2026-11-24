# [BACK-24] Aplicar autorización por propietario, validaciones y protección de archivos en API

- Numero de Issue: #67
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/67
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:35:52 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:31 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:31 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:35:52Z
- Cierre UTC: 2026-11-10T17:02:31Z

- Fecha de captura: 2026-11-24 12:07:40 -0600 (CDMX)
- [Captura original](%5BBACK-24%5D%20Aplicar%20autorizaci%C3%B3n%20por%20propietario%2C%20validaciones%20y%20protecci%C3%B3n%20de%20archivos%20en%20API-original.png)
- [Captura con metadatos](%5BBACK-24%5D%20Aplicar%20autorizaci%C3%B3n%20por%20propietario%2C%20validaciones%20y%20protecci%C3%B3n%20de%20archivos%20en%20API.png)

## Descripcion original

## Objetivo
Endurecer todos los endpoints de ApuntIA y garantizar aislamiento de apuntes, archivos, PDFs, trabajos y datos personales, con control de errores uniforme y prevención de abusos.

## Contexto técnico y alcance
Los nuevos recursos no pueden identificarse solo por un UUID y considerarse privados. La API debe resolver siempre el usuario autenticado y consultar/autorizar el recurso en el servidor.

## Actividades detalladas
- [ ] Implementar dependencia común `usuario_actual` y autorización por propietario para ver, crear, editar, borrar y exportar notas.
- [ ] Denegar acceso cruzado a archivos, trabajos, fuentes, versiones, citas y PDF; no usar nombres de archivo proporcionados para construir paths sin validar.
- [ ] Fortalecer validación real de tipos de archivo, MB/MP, número de páginas, contenido Unicode, LaTeX y HTML no confiable.
- [ ] Definir rate limiting y cuotas de trabajos/almacenamiento para frenar abuso y DoS.
- [ ] Implementar CORS restrictivo si hay cookies y protección CSRF; revisar HTTPS/headers/cookies en producción.
- [ ] Controlar fugas de datos en logs, trazas, respuestas de error, listado de carpetas, URL de exportación y cabeceras de caché.
- [ ] Aislar trabajo de OCR/HTML/PDF y evitar SSRF, path traversal y ejecución de contenido de usuarios.
- [ ] Establecer política para borrar cuenta/datos, invalidar exportaciones y eliminar temporales.
- [ ] Agregar catálogo de errores nuevos alineado al contrato previo; no mostrar stacktraces al cliente.
- [ ] Revisar compatibilidad del endpoint legacy y cerrar cualquier puerta lateral a datos privados.

## Criterios de aceptación
- [ ] Dos usuarios no pueden acceder a recursos ajenos manipulando identificadores o URLs.
- [ ] Ninguna ruta sirve archivos privados fuera del controlador autenticado.
- [ ] Uploads maliciosos y contenidos peligrosos se rechazan o aíslan sin ejecutar código.
- [ ] Errores muestran mensaje útil sin revelar tokens, datos privados ni paths internos.

## Pruebas y verificación obligatoria
- Tests IDOR por recurso, traversal `../`, contenido disfrazado, LaTeX/HTML malicioso y payload enorme.
- Pruebas CSRF, CORS y rate limit.
- Revisión automática de headers, logs y archivos temporales.

## Archivos y entregables esperados
- Middleware/dependencias de autorización y políticas.
- Pruebas negativas y guía de seguridad de API.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-21..BACK-23.
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

![Captura del Issue #67](%5BBACK-24%5D%20Aplicar%20autorizaci%C3%B3n%20por%20propietario%2C%20validaciones%20y%20protecci%C3%B3n%20de%20archivos%20en%20API.png)
