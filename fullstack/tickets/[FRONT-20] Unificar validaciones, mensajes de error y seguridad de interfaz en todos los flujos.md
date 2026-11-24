# [FRONT-20] Unificar validaciones, mensajes de error y seguridad de interfaz en todos los flujos

- Numero de Issue: #80
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/80
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:42:08 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:49 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:49 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:42:08Z
- Cierre UTC: 2026-11-10T17:02:49Z

- Fecha de captura: 2026-11-24 12:08:42 -0600 (CDMX)
- [Captura original](%5BFRONT-20%5D%20Unificar%20validaciones%2C%20mensajes%20de%20error%20y%20seguridad%20de%20interfaz%20en%20todos%20los%20flujos-original.png)
- [Captura con metadatos](%5BFRONT-20%5D%20Unificar%20validaciones%2C%20mensajes%20de%20error%20y%20seguridad%20de%20interfaz%20en%20todos%20los%20flujos.png)

## Descripcion original

## Objetivo
Garantizar mensajes en español útiles, consistentes y accesibles para OCR, fórmulas, PDF, autenticación, cuenta e historial, y bloquear inyección de contenido no confiable.

## Contexto técnico y alcance
Actualmente existen módulos `mensajes.js`, `validacion.js` y un esquema `{error:{codigo,mensaje}}`; ampliarlos sin crear manejadores distintos y contradictorios en cada página.

## Actividades detalladas
- [ ] Auditar catálogo de códigos y mensajes existentes; conservar códigos previos y añadir nuevos agrupados por etapa.
- [ ] Definir patrón uniforme para errores de validación (archivo, tipo, tamaño, páginas, correo, contraseña, fórmula inválida).
- [ ] Distinguir error recuperable, advertencia de calidad OCR, mensaje informativo y error crítico sin exponer stacktrace.
- [ ] Implementar avisos accesibles `aria-live`, foco, estados de loading, botón reintentar y opción cancelar cuando proceda.
- [ ] Sanitizar y mostrar como texto el contenido de OCR, citas, LaTeX, nombres de archivo y respuestas del servidor; evitar `innerHTML` con datos no confiables.
- [ ] Asegurar cliente fetch coherente en auth, CORS, timeout y errores de red, sin loops de reintentos.
- [ ] Proteger estados al logout/expiración: borrar datos privados de memoria y evitar compartir entre cuentas.
- [ ] Gestionar fallos de servicios externos indicando claramente que se puede continuar sin investigación.
- [ ] Corregir mensajes inconsistentes, faltas de ortografía y descripciones heredadas solo del pizarrón.

## Criterios de aceptación
- [ ] Todas las pantallas usan el mismo catálogo y proporcionan recuperación apropiada.
- [ ] Datos maliciosos no se convierten en HTML ejecutable ni filtran secretos.
- [ ] Error 401 cierra/renueva sesión según contrato sin mezclar contenidos de usuarios.
- [ ] Las advertencias de OCR no se presentan como éxitos definitivos.

## Pruebas y verificación obligatoria
- Unit tests de catálogo por código y fallback de error desconocido.
- Playwright XSS con texto OCR/citas, red cortada, 401, 413, 422, 429 y 500.
- Pruebas de navegación por teclado y anuncios de errores.

## Archivos y entregables esperados
- Catálogo de errores y componentes comunes actualizados.
- Pruebas de seguridad y accesibilidad.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-15; FRONT-12..FRONT-19.
- **Área responsable:** frontend.
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

![Captura del Issue #80](%5BFRONT-20%5D%20Unificar%20validaciones%2C%20mensajes%20de%20error%20y%20seguridad%20de%20interfaz%20en%20todos%20los%20flujos.png)
