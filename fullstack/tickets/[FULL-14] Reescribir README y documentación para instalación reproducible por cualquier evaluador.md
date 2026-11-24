# [FULL-14] Reescribir README y documentación para instalación reproducible por cualquier evaluador

- Numero de Issue: #44
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/44
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:23:39 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:06 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:06 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:23:39Z
- Cierre UTC: 2026-11-10T17:05:06Z

- Fecha de captura: 2026-11-24 12:05:55 -0600 (CDMX)
- [Captura original](%5BFULL-14%5D%20Reescribir%20README%20y%20documentaci%C3%B3n%20para%20instalaci%C3%B3n%20reproducible%20por%20cualquier%20evaluador-original.png)
- [Captura con metadatos](%5BFULL-14%5D%20Reescribir%20README%20y%20documentaci%C3%B3n%20para%20instalaci%C3%B3n%20reproducible%20por%20cualquier%20evaluador.png)

## Descripcion original

## Objetivo
Convertir el README principal en una guía verificable, precisa y apta para una persona que nunca trabajó con ApuntIA; documentar las modalidades script local y Docker, el nuevo alcance cuaderno/pizarrón y la ampliación posterior de funcionalidades.

## Contexto técnico y alcance
El README actual describe el procesamiento de pizarrón mediante `/analisis`, el frontend estático, Pytest/Playwright y comandos separados; algunos paths históricos pueden estar desactualizados. Documentar únicamente comandos y versiones realmente probadas.

## Actividades detalladas
- [ ] Auditar los README y `docs/` existentes, versiones efectivas, scripts, variables, rutas, tests y puertos; identificar contradicciones.
- [ ] Explicar qué hace y qué NO hace aún ApuntIA; actualizar el alcance progresivamente sin vender OCR/PDF/login como terminado antes de existir.
- [ ] Crear tabla de requisitos por modo (Python, Git, Node solo pruebas, Docker solo contenedores, espacio y acceso a internet para modelos).
- [ ] Escribir inicio rápido Windows PowerShell/CMD y Linux/macOS según soporte verificado, especificando directorio desde el cual se ejecuta cada comando.
- [ ] Explicar con ejemplos reales la opción script local y la opción Docker, junto con detención, reinicio, actualización y primera descarga de modelos.
- [ ] Documentar variables de entorno mediante `.env.example`, valores seguros, persistencia, rutas, límites de subida y configuración de origen de API.
- [ ] Describir flujo completo foto/archivo -> extracción -> edición -> enriquecimiento -> PDF -> historial según funcionalidades integradas.
- [ ] Agregar troubleshooting por puertos ocupados, Python incorrecto, permisos, CORS, modelos faltantes, disco insuficiente, Docker sin iniciar y dependencias.
- [ ] Incluir arquitectura, endpoints, seguridad, privacidad, pruebas, criterios de éxito, licencias de dependencias/modelos y notas de datos de ejemplo.
- [ ] Validar todos los comandos desde cero, arreglar enlaces rotos y añadir control de cambios de documentación por cada PR futuro.

## Criterios de aceptación
- [ ] Un evaluador puede ejecutar ApuntIA siguiendo exclusivamente el README y prerequisitos declarados en cada método.
- [ ] Los comandos y rutas son correctos, distintos por plataforma cuando sea necesario y no contienen credenciales reales.
- [ ] Quedan documentados PDF/OCR/login como disponibles o futuros según su estado comprobado; sin afirmaciones falsas.
- [ ] Todo ejemplo de endpoint y los enlaces internos se resuelve correctamente.
- [ ] La guía documenta recuperación ante los fallos más comunes y cómo ejecutar pruebas.

## Pruebas y verificación obligatoria
- Pedir a alguien ajeno al proyecto que reproduzca el arranque siguiendo solo el README.
- Probar una instalación local y una Docker en ambientes limpios, guardar salida de comandos y capturas.
- Validar documentación y enlaces mediante herramienta/linter cuando sea viable.

## Archivos y entregables esperados
- `README.md` principal reescrito, `fullstack/docs/instalacion.md` o ubicación equivalente.
- Tabla de compatibilidad y troubleshooting, .env.example verificable.
- Lista de comandos realmente ejecutados y sus resultados.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-11, FULL-12, FULL-13.
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

![Captura del Issue #44](%5BFULL-14%5D%20Reescribir%20README%20y%20documentaci%C3%B3n%20para%20instalaci%C3%B3n%20reproducible%20por%20cualquier%20evaluador.png)
