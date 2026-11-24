# [FRONT-15] Permitir ampliar apuntes con investigación y mostrar referencias verificables

- Numero de Issue: #75
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/75
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:40:12 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:42 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:42 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:40:12Z
- Cierre UTC: 2026-11-10T17:02:42Z

- Fecha de captura: 2026-11-24 12:08:17 -0600 (CDMX)
- [Captura original](%5BFRONT-15%5D%20Permitir%20ampliar%20apuntes%20con%20investigaci%C3%B3n%20y%20mostrar%20referencias%20verificables-original.png)
- [Captura con metadatos](%5BFRONT-15%5D%20Permitir%20ampliar%20apuntes%20con%20investigaci%C3%B3n%20y%20mostrar%20referencias%20verificables.png)

## Descripcion original

## Objetivo
Dar al usuario control sobre la investigación opcional: elegir si desea complementar contenido, revisar qué se agregó y consultar citas; separar claramente la nota original de lo encontrado fuera.

## Contexto técnico y alcance
La investigación puede usar servicios remotos y datos privados. Nunca enviar imágenes/texto fuera sin consentimiento informado, y no crear una interfaz que oculte la procedencia de afirmaciones.

## Actividades detalladas
- [ ] Agregar opción desactivada por defecto de `Buscar información complementaria`, con explicación de conectividad, proveedor y datos enviados.
- [ ] Solicitar consentimiento específico antes de investigación que transmitirá contenido a un tercero.
- [ ] Permitir seleccionar profundidad/áreas del tema y mostrar tiempo/estado y opción de cancelar.
- [ ] Presentar resultados en pestañas/secciones diferenciadas: apunte extraído/corregido vs complemento externo.
- [ ] Mostrar junto a cada complemento fuente con título, enlace válido, fecha de consulta y estado de verificación.
- [ ] Avisar cuando una afirmación no tenga referencia suficiente; permitir descartarla del documento.
- [ ] Permitir aceptar/rechazar complementos y editar observaciones sin modificar el origen OCR.
- [ ] Mostrar contradicciones detectadas con opción de revisión, no sustitución automática.
- [ ] Ofrecer flujo de PDF sin investigar cuando no haya internet o fuentes.
- [ ] Cuidar accesibilidad, seguridad de enlaces externos y mensajes de errores/consentimiento.

## Criterios de aceptación
- [ ] La investigación no comienza antes de consentimiento expreso cuando involucra proveedor remoto.
- [ ] Las fuentes son inspeccionables y no se presentan enlaces ficticios.
- [ ] El usuario puede generar PDF sin complemento y aceptar/rechazar agregados.
- [ ] El contenido OCR permanece distinguible y sin cambios silenciosos.

## Pruebas y verificación obligatoria
- Playwright con resultado sin citas, fuente inaccesible, red caída, respuesta lenta y rechazo de complemento.
- Verificar consentimiento en red/mock y enlaces `rel=noopener noreferrer` cuando aplican.
- Prueba PDF con y sin fuentes.

## Archivos y entregables esperados
- Controles de investigación y referencias, pruebas.
- Textos de consentimiento y documentación.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-18, BACK-19; FRONT-13.
- **Área responsable:** frontend.
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

![Captura del Issue #75](%5BFRONT-15%5D%20Permitir%20ampliar%20apuntes%20con%20investigaci%C3%B3n%20y%20mostrar%20referencias%20verificables.png)
