# [FRONT-14] Visualizar y corregir fórmulas, tablas y esquemas antes del PDF

- Numero de Issue: #74
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/74
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:39:55 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:40 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:40 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:39:55Z
- Cierre UTC: 2026-11-10T17:02:40Z

- Fecha de captura: 2026-11-24 12:08:12 -0600 (CDMX)
- [Captura original](%5BFRONT-14%5D%20Visualizar%20y%20corregir%20f%C3%B3rmulas%2C%20tablas%20y%20esquemas%20antes%20del%20PDF-original.png)
- [Captura con metadatos](%5BFRONT-14%5D%20Visualizar%20y%20corregir%20f%C3%B3rmulas%2C%20tablas%20y%20esquemas%20antes%20del%20PDF.png)

## Descripcion original

## Objetivo
Crear herramientas de revisión de contenido estructurado para fórmulas matemáticas, tablas comparativas, diagramas y dibujos procedentes de cuadernos o pizarrones.

## Contexto técnico y alcance
No sustituir reconocimiento por un campo de texto genérico. Se necesita previsualización matemática segura y alternativa cuando el reconocimiento no sea confiable.

## Actividades detalladas
- [ ] Mostrar fórmula original recortada junto con LaTeX reconocido y su renderizado seguro (KaTeX/MathJax u opción justificada).
- [ ] Permitir editar código LaTeX dentro del subconjunto permitido y visualizar advertencias por sintaxis inválida.
- [ ] Añadir edición sencilla de celdas, filas y columnas de tablas reconocidas, respetando IDs del backend.
- [ ] Visualizar esquemas/diagramas reconstruidos, y ofrecer conservar imagen de origen si la reconstrucción es incierta.
- [ ] Mantener orden de bloques y relación con su página/región al editar.
- [ ] Evitar ejecutar macros LaTeX/HTML no confiables en navegador; no insertar contenido sin sanitizar.
- [ ] Guardar cambios de manera versionada y avisar de conflictos de concurrencia.
- [ ] Mostrar estado de conversión matemática y mensajes accesibles por cada bloque.
- [ ] Verificar que vista previa y salida PDF usen la misma versión de contenido.

## Criterios de aceptación
- [ ] El usuario puede corregir una fórmula y verla renderizada antes de generar PDF.
- [ ] Una tabla editable conserva filas/columnas en guardado y PDF.
- [ ] Un diagrama difícil puede preservarse como imagen en lugar de información inventada.
- [ ] No se ejecuta contenido malicioso dentro de LaTeX/HTML.

## Pruebas y verificación obligatoria
- Casos de fracciones, raíces, super/subíndices, tabla 3x4 y diagrama fallback.
- Test de LaTeX inválido, XSS, guardar/recargar y PDF posterior.
- Revisión responsive/teclado de editores.

## Archivos y entregables esperados
- Componentes de fórmula/tabla/diagrama y estilos.
- Pruebas y ejemplos accesibles.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-15..BACK-17; FRONT-13.
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

![Captura del Issue #74](%5BFRONT-14%5D%20Visualizar%20y%20corregir%20f%C3%B3rmulas%2C%20tablas%20y%20esquemas%20antes%20del%20PDF.png)
