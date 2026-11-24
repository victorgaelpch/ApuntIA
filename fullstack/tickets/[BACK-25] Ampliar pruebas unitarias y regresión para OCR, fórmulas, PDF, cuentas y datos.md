# [BACK-25] Ampliar pruebas unitarias y regresión para OCR, fórmulas, PDF, cuentas y datos

- Numero de Issue: #68
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/68
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:36:14 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:32 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:32 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:36:14Z
- Cierre UTC: 2026-11-10T17:02:32Z

- Fecha de captura: 2026-11-24 12:07:45 -0600 (CDMX)
- [Captura original](%5BBACK-25%5D%20Ampliar%20pruebas%20unitarias%20y%20regresi%C3%B3n%20para%20OCR%2C%20f%C3%B3rmulas%2C%20PDF%2C%20cuentas%20y%20datos-original.png)
- [Captura con metadatos](%5BBACK-25%5D%20Ampliar%20pruebas%20unitarias%20y%20regresi%C3%B3n%20para%20OCR%2C%20f%C3%B3rmulas%2C%20PDF%2C%20cuentas%20y%20datos.png)

## Descripcion original

## Objetivo
Construir una suite sólida que pruebe los servicios nuevos y preserve los resultados actuales de OpenCV/API, con fixtures estables y fallos claros.

## Contexto técnico y alcance
El README menciona pruebas Pytest existentes; reutilizarlas, no eliminarlas. Los servicios de reconocimiento pueden ser pesados y no deterministas: separar tests unitarios con doubles de tests de evaluación reales.

## Actividades detalladas
- [ ] Inventariar y ejecutar tests actuales para establecer línea base antes de cambios.
- [ ] Probar validación, multipágina y preprocesamiento de cuaderno/pizarrón.
- [ ] Crear unit tests para adaptadores OCR, HTR, fórmulas, layout y esquema intermedio con mocks.
- [ ] Crear integration tests reales para generar documentos/PDF a partir de fixtures controladas.
- [ ] Probar fallos por ausencia de modelo, disco lleno, timeout, latencia excesiva y servicio de investigación inactivo.
- [ ] Cubrir almacenamiento, migraciones, historial y autorización con base de datos temporal aislada.
- [ ] Probar seguridad de login/recuperación, tokens expirados, CSRF, IDOR y uploads maliciosos.
- [ ] Comparar la API legacy (tipo `image/png`, errores, `/salud`) antes/después.
- [ ] Registrar tiempos y memoria de casos representativos para detectar regresiones fuertes.
- [ ] Documentar ejecución rápida sin modelos gigantes y evaluación profunda opt-in.

## Criterios de aceptación
- [ ] Existe suite ejecutable que falla al detectar una regresión en contratos y seguridad críticos.
- [ ] Los tests no dependen de credenciales personales ni de servicios externos obligatorios.
- [ ] Se cubren tanto caminos exitosos como inválidos y parciales.
- [ ] Hay evidencia de ejecución y reporte de fallos claro.

## Pruebas y verificación obligatoria
- Ejecutar suite sobre rama limpia y en CI, comprobar fixtures y aislamiento.
- Forzar fallos en un mock para confirmar detección.
- Ejecutar benchmark OCR real con ground truth y reporte independiente.

## Archivos y entregables esperados
- Tests Pytest y fixtures, reporte de cobertura y calidad.
- Documentación y comandos reproducibles.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-11..BACK-24; FULL-19.
- **Área responsable:** backend.
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

![Captura del Issue #68](%5BBACK-25%5D%20Ampliar%20pruebas%20unitarias%20y%20regresi%C3%B3n%20para%20OCR%2C%20f%C3%B3rmulas%2C%20PDF%2C%20cuentas%20y%20datos.png)
