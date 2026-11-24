# [FRONT-13] Mostrar OCR y permitir corregir texto por bloques antes de generar apuntes

- Numero de Issue: #73
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/73
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:39:37 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:39 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:39 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:39:37Z
- Cierre UTC: 2026-11-10T17:02:39Z

- Fecha de captura: 2026-11-24 12:08:07 -0600 (CDMX)
- [Captura original](%5BFRONT-13%5D%20Mostrar%20OCR%20y%20permitir%20corregir%20texto%20por%20bloques%20antes%20de%20generar%20apuntes-original.png)
- [Captura con metadatos](%5BFRONT-13%5D%20Mostrar%20OCR%20y%20permitir%20corregir%20texto%20por%20bloques%20antes%20de%20generar%20apuntes.png)

## Descripcion original

## Objetivo
Construir editor claro del texto extraído, asociado a las regiones de cada página, para que el usuario corrija letras, acentos, líneas, títulos y errores de reconocimiento antes de exportar.

## Contexto técnico y alcance
El OCR automático no es infalible. El usuario debe poder comparar la fotografía con la transcripción y distinguir texto reconocido, incierto y no reconocido.

## Actividades detalladas
- [ ] Crear vista lado a lado: imagen original/procesada y bloques OCR en orden de lectura.
- [ ] Resaltar bloque seleccionado en la imagen mediante bounding boxes escalables sin romper zoom/responsive.
- [ ] Mostrar texto por bloques y orden; indicar confianza/fallback cuando el backend la proporcione.
- [ ] Permitir edición, borrado, división/unión básica y reclasificación de bloque cuando esté definida en el contrato.
- [ ] Marcar segmentos dudosos y permitir conservar imagen original o dejarlos pendientes.
- [ ] Persistir correcciones explícitamente usando ID/versión de nota y gestionar conflicto de edición.
- [ ] Mostrar estado guardando/guardado/error sin afirmar éxito antes de respuesta del servidor.
- [ ] Evitar XSS al visualizar contenido extraído o corregido (textContent/sanitización); no interpretar OCR como HTML.
- [ ] Proteger contra pérdida de cambios al cambiar de página, cerrar ventana o expirar sesión.
- [ ] Integrar accesibilidad teclado/lectores y errores en español coherentes.

## Criterios de aceptación
- [ ] Las correcciones se guardan y aparecen tras recargar la nota.
- [ ] Cada bloque está asociado a la región y página correctas.
- [ ] Un texto OCR malicioso se muestra como texto, no ejecuta scripts.
- [ ] El PDF generado después usa la corrección, no una transcripción anterior.

## Pruebas y verificación obligatoria
- Playwright: editar/tildes/guardar/recargar, imagen con regiones ambiguas, error 409 de versión.
- Test XSS con texto `<script>` mostrado como contenido inerte.
- Verificar consistencia con API y PDF de integración.

## Archivos y entregables esperados
- Editor OCR responsive y pruebas.
- Capturas de revisión con segmentos de confianza baja.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-13, BACK-14, BACK-17; FRONT-12.
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

![Captura del Issue #73](%5BFRONT-13%5D%20Mostrar%20OCR%20y%20permitir%20corregir%20texto%20por%20bloques%20antes%20de%20generar%20apuntes.png)
