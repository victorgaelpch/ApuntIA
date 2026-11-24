# [FULL-22] Preparar entrega reproducible, versión de release y arranque en equipos

- Numero de Issue: #52
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/52
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:27:30 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:19 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:19 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:27:30Z
- Cierre UTC: 2026-11-10T17:05:19Z

- Fecha de captura: 2026-11-24 12:06:29 -0600 (CDMX)
- [Captura original](%5BFULL-22%5D%20Preparar%20entrega%20reproducible%2C%20versi%C3%B3n%20de%20release%20y%20arranque%20en%20equipos-original.png)
- [Captura con metadatos](%5BFULL-22%5D%20Preparar%20entrega%20reproducible%2C%20versi%C3%B3n%20de%20release%20y%20arranque%20en%20equipos.png)

## Descripcion original

## Objetivo
Formalizar el procedimiento de entrega: una versión etiquetada del proyecto con scripts y Docker probados, configuración de ejemplo, pruebas y guía de demostración para el profesor.

## Contexto técnico y alcance
La entrega no debe depender de la PC del desarrollador ni de variables ocultas; los modelos OCR pueden ocupar mucho espacio y requerir descargas iniciales, que deben quedar explicitadas.

## Actividades detalladas
- [ ] Definir versiones mínimas/validadas de Python, Node para pruebas, Docker/Compose y bibliotecas OCR/PDF.
- [ ] Fijar versiones de dependencias, licencias y mecanismos de checksum/modelo cuando sean necesarios.
- [ ] Crear smoke test automático de primera ejecución local y Docker, incluyendo salud, imagen, OCR y PDF.
- [ ] Separar datos sintéticos de demo de datos reales de usuarios; documentar restauración segura de demo.
- [ ] Verificar instaladores/arranque bajo Windows y Linux y, si se afirma compatibilidad, macOS; no prometer plataformas sin prueba.
- [ ] Preparar instrucciones claras sobre puertos, permisos, conectividad, tiempo y almacenamiento de la primera ejecución.
- [ ] Generar checklist de release: tests verdes, documentación actualizada, configuración, migraciones, seguridad, respaldo y licencias.
- [ ] Publicar changelog y un tag/versionado cuando la funcionalidad esté lista.
- [ ] Documentar cómo actualizar, conservar archivos, detener y recuperar datos si falla una actualización.

## Criterios de aceptación
- [ ] La entrega funciona desde un clon limpio siguiendo README y con prerequisitos publicados.
- [ ] Ambos métodos de inicio (scripts y Compose) logran el mismo smoke test principal.
- [ ] El release no contiene claves, archivos personales ni dependencias locales ocultas.
- [ ] Existe una guía de demostración reproducible con tiempos/limitaciones realistas.

## Pruebas y verificación obligatoria
- Instalación de cero en Windows/Linux compatibles con grabación de comandos.
- Reinicio después de generar una nota para verificar persistencia.
- Análisis de conflictos de puertos, permisos y fallos de descarga de modelos.

## Archivos y entregables esperados
- Checklist de release, changelog/tag cuando proceda.
- Smoke tests automatizados, guía de demostración y matriz de compatibilidad.
- Evidencias de instalaciones limpias.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-13, FULL-14, FULL-17, FULL-18.
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

![Captura del Issue #52](%5BFULL-22%5D%20Preparar%20entrega%20reproducible%2C%20versi%C3%B3n%20de%20release%20y%20arranque%20en%20equipos.png)
