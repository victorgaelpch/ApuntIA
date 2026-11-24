# [FULL-17] Centralizar pruebas unitarias, integración y CI para scripts y contenedores

- Numero de Issue: #47
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/47
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:25:01 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:11 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:11 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:25:01Z
- Cierre UTC: 2026-11-10T17:05:11Z

- Fecha de captura: 2026-11-24 12:06:03 -0600 (CDMX)
- [Captura original](%5BFULL-17%5D%20Centralizar%20pruebas%20unitarias%2C%20integraci%C3%B3n%20y%20CI%20para%20scripts%20y%20contenedores-original.png)
- [Captura con metadatos](%5BFULL-17%5D%20Centralizar%20pruebas%20unitarias%2C%20integraci%C3%B3n%20y%20CI%20para%20scripts%20y%20contenedores.png)

## Descripcion original

## Objetivo
Organizar la estrategia de pruebas continua y la ejecución automatizada en GitHub Actions para detectar regresiones de frontend, backend, API, despliegue y seguridad antes de fusionar cambios.

## Contexto técnico y alcance
Ya existen suites Pytest, Playwright y una estructura `tests/integracion/`, documentadas en el README. NO reemplazarlas ni asumir sus totales como pruebas recién ejecutadas; reutilizarlas y extenderlas con coherencia.

## Actividades detalladas
- [ ] Inventariar suites y comandos de `package.json`, `requirements-dev.txt` y workflows existentes.
- [ ] Definir qué tests son unitarios de backend, unitarios de frontend, contract tests, integración, E2E y smoke de despliegue; ubicarlos por propiedad.
- [ ] Crear un único script de validación fullstack con modos rápidos y completos, compatible con CI y con códigos de salida correctos.
- [ ] Configurar GitHub Actions en PR/push: lint, tests backend, frontend, contratos, integración y build Docker cuando proceda.
- [ ] Crear fixtures sintéticas no personales para OCR, fórmulas, documentos, PDF, login, historial y manejo de errores.
- [ ] Añadir integración real con servicios levantados y wait-for-health robusto, sin sleeps ciegos.
- [ ] Separar tests con APIs externas usando mocks y pruebas opt-in controladas para no consumir claves ni cuotas.
- [ ] Publicar artefactos de fallo (logs saneados, reporte JUnit, capturas y trazas Playwright sin información sensible).
- [ ] Medir cobertura y regresión de casos críticos sin imponer un porcentaje vacío que no evalúe calidad.
- [ ] Documentar cómo ejecutar test rápido/local/CI y cómo reproducir fallos.

## Criterios de aceptación
- [ ] Un PR no puede considerarse validado si fallan los tests obligatorios configurados.
- [ ] Las suites existentes se ejecutan y los nuevos casos cubren OCR, fórmulas, PDF y autenticación conforme se integren.
- [ ] El workflow funciona con la estructura `fullstack/` y no contiene tokens ni secretos.
- [ ] La ejecución de CI puede reproducirse localmente y no depende de servicios personales.

## Pruebas y verificación obligatoria
- Probar un commit con test fallido para confirmar que CI bloquea.
- Verificar tests en PR limpio, ejecución en paralelo sin conflictos de puertos y tratamiento de fallos transitorios.
- Prueba de build Docker y smoke local sin Docker en plataformas soportadas.

## Archivos y entregables esperados
- Scripts de pruebas en `fullstack/`, workflows `.github/workflows`.
- Fixtures y reportes automáticos, guía para contributor.
- Matriz de pruebas y evidencia de CI.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-12, FULL-13, FULL-15.
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

![Captura del Issue #47](%5BFULL-17%5D%20Centralizar%20pruebas%20unitarias%2C%20integraci%C3%B3n%20y%20CI%20para%20scripts%20y%20contenedores.png)
