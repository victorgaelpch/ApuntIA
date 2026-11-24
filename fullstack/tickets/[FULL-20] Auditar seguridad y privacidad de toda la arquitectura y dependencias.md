# [FULL-20] Auditar seguridad y privacidad de toda la arquitectura y dependencias

- Numero de Issue: #50
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/50
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:26:16 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:15 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:15 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:26:16Z
- Cierre UTC: 2026-11-10T17:05:15Z

- Fecha de captura: 2026-11-24 12:06:17 -0600 (CDMX)
- [Captura original](%5BFULL-20%5D%20Auditar%20seguridad%20y%20privacidad%20de%20toda%20la%20arquitectura%20y%20dependencias-original.png)
- [Captura con metadatos](%5BFULL-20%5D%20Auditar%20seguridad%20y%20privacidad%20de%20toda%20la%20arquitectura%20y%20dependencias.png)

## Descripcion original

## Objetivo
Ejecutar una revisión transversal de riesgos de seguridad y protección de archivos educativos, cuentas, claves y servicios de investigación; corregir fallos antes de la entrega.

## Contexto técnico y alcance
La ampliación incorpora datos personales, contraseñas, fotos de cuadernos y salidas que pueden contener información privada. Además, el uso de fuentes web/servicios externos agrega riesgos de filtración y prompt injection.

## Actividades detalladas
- [ ] Inventariar activos, flujos de datos, credenciales y superficies de ataque para script local y Docker.
- [ ] Verificar secretos en historial Git, `.env`, archivos de CI, logs y ejemplos; documentar rotación si algo se filtró.
- [ ] Asegurar límites de carga, validación de contenido real, mitigaciones de ZIP/PDF malicioso y límites de CPU/RAM por procesamiento.
- [ ] Probar CORS con credenciales, CSRF si cookies, cabeceras de seguridad, gestión de sesiones y protección de descargas.
- [ ] Verificar autorización horizontal y vertical, acceso por ID manipulados y listados entre usuarios.
- [ ] Establecer política de retención y borrado de documentos, temporales, backups y datos enviados a proveedores externos.
- [ ] Definir consentimientos explícitos para OCR cloud/investigación, minimización de información enviada y modo sin conexión cuando aplique.
- [ ] Realizar revisión de dependencias/modelos/licencias, fijación de versiones y análisis de vulnerabilidades.
- [ ] Asegurar que texto extraído o encontrado en web se trate como dato NO como instrucción ejecutable; evitar SSRF y ejecución de código.
- [ ] Escribir checklist de seguridad de release y pruebas automatizadas de casos críticos.

## Criterios de aceptación
- [ ] La revisión documenta amenazas y mitigaciones implementadas, no solo una lista teórica.
- [ ] No hay secretos en repo ni archivos privados expuestos por el servidor web.
- [ ] Pruebas de IDOR, CSRF/CORS y validación de uploads pasan en entornos soportados.
- [ ] La investigación externa pide consentimiento y nunca divulga documentos completos sin justificación explícita.
- [ ] Se conocen límites pendientes y no se afirma una seguridad absoluta.

## Pruebas y verificación obligatoria
- Pruebas negativas con dos usuarios y URLs manipuladas.
- Verificar encabezados, cookies, logs, almacenamiento, dependencias y build sin secretos.
- Realizar revisión manual de configuración Docker/local y documentar hallazgos.

## Archivos y entregables esperados
- Modelo de amenazas ligero, política de privacidad, checklist de release.
- Pruebas automatizadas de controles críticos y correcciones.
- Matriz de hallazgos y riesgos residuales.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-13, FULL-15, BACK-24, FULL-18.
- **Área responsable:** fullStack.
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

![Captura del Issue #50](%5BFULL-20%5D%20Auditar%20seguridad%20y%20privacidad%20de%20toda%20la%20arquitectura%20y%20dependencias.png)
