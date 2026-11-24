# [FULL-16] Integrar flujo completo de imagen/cuaderno a apunte editable, ampliado y PDF descargable

- Numero de Issue: #46
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/46
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:24:46 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:09 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:09 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:24:46Z
- Cierre UTC: 2026-11-10T17:05:09Z

**Captura no disponible:** Locator.wait_for: InvalidSelectorError: Error while parsing selector `heading[name=/\[FULL\-16\]\ Integrar\ flujo\ completo\ de\ imagen/cuaderno\ a\ apunte\ editable,\ ampliado\ y\ PDF\ descargable/i]` - unexpected symbol "c" at position 66 during parsing attribute value
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
  - waiting for internal:role=heading[name=/\[FULL\-16\]\ Integrar\ flujo\ completo\ de\ imagen/cuaderno\ a\ apunte\ editable,\ ampliado\ y\ PDF\ descargable/i] >> nth=0 to be visible


## Descripcion original

## Objetivo
Orquestar la experiencia extremo a extremo para que una o varias fotos de pizarrón/cuaderno produzcan texto, fórmulas, notas estructuradas y un PDF descargable, con corrección humana y resultados parciales recuperables.

## Contexto técnico y alcance
Integración transversal; no duplicar las rutinas OCR, PDF ni las pantallas que pertenecen a BACK y FRONT. Partir del flujo de imagen actual conservando la posibilidad de obtener la imagen mejorada.

## Actividades detalladas
- [ ] Diseñar máquina de estados para cada trabajo: validando, procesando, OCR, revisión, enriquecimiento optativo, maquetando, completado, fallido, cancelado.
- [ ] Coordinar entrada multipágina y normalización de IDs entre interfaz, API, almacenamiento y generador PDF.
- [ ] Enlazar resultado OCR en bloques editables y garantizar que la corrección del usuario prevalezca sobre el texto automático.
- [ ] Preservar fórmulas e imágenes/esquemas aun cuando no exista transcripción confiable; marcar incertidumbres.
- [ ] Permitir enriquecimiento externo solo con autorización explícita y fuentes verificables, sin bloquear generación básica cuando falle internet.
- [ ] Definir reintentos idempotentes, manejo de trabajos lentos y recuperación después de refrescar página.
- [ ] Evitar generación de PDF vacío/obsoleto: invalidar y regenerar si cambian las notas antes de exportar.
- [ ] Registrar correlación de `job_id`, `nota_id`, `version_id` y `export_id` sin filtrar información privada.
- [ ] Mantener modo heredado `POST /analisis` intacto y documentar el nuevo flujo por separado.
- [ ] Preparar demostración con fotos reales de pizarrón y cuaderno, con y sin fórmula y con varias páginas.

## Criterios de aceptación
- [ ] Un usuario carga cuaderno o pizarrón, revisa contenido, obtiene PDF legible y lo descarga correctamente.
- [ ] Las correcciones de texto/fórmulas se reflejan en el PDF final y en la vista previa.
- [ ] La indisponibilidad del motor de investigación no impide generar notas basadas en la fuente original.
- [ ] Trabajos con error muestran causa accionable, pueden reintentarse sin duplicaciones ni mezclas de usuarios.
- [ ] El procesamiento básico anterior no presenta regresiones.

## Pruebas y verificación obligatoria
- Pruebas E2E con imagen impresa, manuscrita, dos páginas, fórmula, tabla, error OCR y caída de red.
- Verificar que el PDF incluye las correcciones y que no aparece contenido de otra sesión.
- Ejecutar regresión de `POST /analisis` y la suite actual.

## Archivos y entregables esperados
- Orquestación completa por API y UI con diagrama de estados actualizado.
- Pruebas integrales automatizadas y evidencias de PDFs generados.
- Contrato, README y bitácora técnica actualizados.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-15; BACK-11..BACK-21; FRONT-11..FRONT-16.
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


