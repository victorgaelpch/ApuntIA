# [FULL-15] Diseñar arquitectura y contratos API v2 para OCR, fórmulas, PDF y cuentas sin romper /analisis

- Numero de Issue: #45
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/45
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:24:17 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:08 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:08 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:24:17Z
- Cierre UTC: 2026-11-10T17:05:08Z

**Captura no disponible:** Locator.wait_for: InvalidSelectorError: Error while parsing selector `heading[name=/\[FULL\-15\]\ Diseñar\ arquitectura\ y\ contratos\ API\ v2\ para\ OCR,\ fórmulas,\ PDF\ y\ cuentas\ sin\ romper\ /analisis/i]` - unexpected symbol "a" at position 128 during parsing attribute value
    at syntaxError (<anonymous>:2050:11)
    at readAttribute (<anonymous>:2182:7)
    at parseAttributeSelector (<anonymous>:2195:28)
    at Object.queryAll (<anonymous>:5578:22)
    at InjectedScript._queryEngineAll (<anonymous>:7292:49)
    at InjectedScript.querySelectorAll (<anonymous>:7279:30)
    at eval (eval at evaluate (:370:30), <anonymous>:2:42)
    at UtilityScript.evaluate (<anonymous>:372:16)
    at UtilityScript.<anonymous> (<anonymous>:1:44)
Call log:
  - waiting for internal:role=heading[name=/\[FULL\-15\]\ Diseñar\ arquitectura\ y\ contratos\ API\ v2\ para\ OCR,\ fórmulas,\ PDF\ y\ cuentas\ sin\ romper\ /analisis/i] >> nth=0 to be visible


## Descripcion original

## Objetivo
Acordar un diseño integral, incremental y versionado de los nuevos flujos antes de que Claude implemente piezas incompatibles. Mantener compatibilidad con el endpoint original de procesamiento de imagen.

## Contexto técnico y alcance
Contrato actual: `POST /analisis` acepta `multipart/form-data` con campo `file`, entrega `image/png`; `GET /salud` informa estado/límites y errores tienen `{error:{codigo,mensaje}}`. El nuevo sistema requerirá JSON estructurado, recursos por usuario, estado de trabajos y exportaciones.

## Actividades detalladas
- [ ] Revisar `docs/api.md`, `docs/arquitectura.md`, código de enrutadores y cliente `front/js/api.js`.
- [ ] Definir el dominio: fuentes (pizarrón/cuaderno), páginas, regiones, bloques, texto, fórmulas, tablas, diagramas, citas, notas, versiones, exportaciones y usuarios.
- [ ] Diseñar contratos OpenAPI para subir fuentes, lanzar análisis, consultar estado, recuperar segmentos y correcciones, generar PDF, listar notas e iniciar sesión.
- [ ] Elegir nombres coherentes de endpoints versionados `/api/v2/...` o equivalente sin eliminar ni cambiar de tipo la respuesta de `/analisis`.
- [ ] Documentar esquema JSON con IDs estables, orden de lectura, confianza, bounding boxes, origen de cada bloque, fechas y versiones.
- [ ] Estandarizar paginación, filtros, tiempos de expiración, idempotencia de trabajos, estados y códigos HTTP.
- [ ] Definir esquema seguro de autenticación, CSRF si hay cookies, autorizaciones por recurso, protección de descargas y consentimientos para servicios externos.
- [ ] Diseñar errores consistentes con el formato existente, catálogo de códigos nuevos y reglas de mensajes localizables.
- [ ] Precisar manejo de archivos grandes, páginas múltiples, timeouts y reintentos; distinguir fallo parcial de fallo total.
- [ ] Guardar ejemplos de peticiones/respuestas reales, esquema de flujo, decisiones y tabla de compatibilidad.

## Criterios de aceptación
- [ ] Existe contrato publicado con ejemplos válidos para cada nuevo recurso y formato de contenido.
- [ ] Frontend y backend pueden implementar el contrato sin inventar campos ni estados divergentes.
- [ ] El endpoint legacy `/analisis` mantiene su comportamiento actual para clientes existentes.
- [ ] Los modelos establecen separación de contenido extraído, corregido, investigado y generado.
- [ ] El contrato documenta privacidad, autenticación, errores y control de versiones.

## Pruebas y verificación obligatoria
- Validación automática de OpenAPI y esquemas JSON con ejemplos.
- Tests de contrato sobre la respuesta heredada y las rutas nuevas.
- Revisión cruzada de responsable frontend/backend antes de fusionar.

## Archivos y entregables esperados
- `docs/api-v2.md` o documento equivalente y OpenAPI actualizado.
- Diagramas de arquitectura y secuencia, ejemplos de JSON, tabla de compatibilidad.
- Aprobación técnica en PR y matriz de dependencias entre Issues.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-12; revisión BACK-11..BACK-16 y BACK-21..BACK-24.
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

