# [FRONT-11] Actualizar concepto visual de ApuntIA para pizarrones y cuadernos

- Numero de Issue: #71
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/71
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:37:19 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:36 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:36 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:37:19Z
- Cierre UTC: 2026-11-10T17:02:36Z

- Fecha de captura: 2026-11-24 12:07:57 -0600 (CDMX)
- [Captura original](%5BFRONT-11%5D%20Actualizar%20concepto%20visual%20de%20ApuntIA%20para%20pizarrones%20y%20cuadernos-original.png)
- [Captura con metadatos](%5BFRONT-11%5D%20Actualizar%20concepto%20visual%20de%20ApuntIA%20para%20pizarrones%20y%20cuadernos.png)

## Descripcion original

## Objetivo
Rediseñar textos, navegación y experiencia de bienvenida para reflejar que ApuntIA transforma tanto pizarrones como apuntes de cuaderno en documentos digitales completos, no solo imágenes más nítidas.

## Contexto técnico y alcance
Partir de `index.html` y componentes de `front/`. Mantener funcionalidades actuales de cámara, carga de imagen, comparación y descarga PNG; no crear otra interfaz desconectada o eliminar opciones existentes.

## Actividades detalladas
- [ ] Auditar estructura HTML/CSS/JS, componentes, accesibilidad y flujo actual para no perder eventos.
- [ ] Actualizar nombre/descripción y textos de `pizarrón` a `pizarrón o cuaderno` de manera consistente, sin alterar contratos API viejos.
- [ ] Diseñar navegación clara: Inicio, Crear apuntes, Mis apuntes, Perfil y Ayuda; elementos privados solo según sesión.
- [ ] Crear un recorrido por pasos: elegir fuente, procesar, revisar, ampliar opcionalmente, generar PDF, guardar.
- [ ] Mostrar qué funciones están operativas y cuáles aún no; no reemplazar backend con mocks presentados como reales.
- [ ] Conservar opción de obtener imagen limpiada para quienes solo la necesitan.
- [ ] Implementar diseño responsive y estados vacíos/accesibles para computador y móvil.
- [ ] Centralizar textos/constantes y rutas de la UI para evitar enlaces rotos.
- [ ] Actualizar descripciones, metadatos y ayuda de privacidad.

## Criterios de aceptación
- [ ] La interfaz permite entender dos tipos de fuente y el resultado esperado de PDF.
- [ ] Carga/cámara/procesamiento PNG anteriores siguen siendo utilizables.
- [ ] La navegación responde correctamente en equipos y resoluciones soportadas.
- [ ] No hay opciones que aparenten producir OCR o PDF si el backend no está listo.

## Pruebas y verificación obligatoria
- Regresión Playwright de carga, cámara simulada y comparación.
- Pruebas de navegación con/sin sesión, teclado y pantalla reducida.
- Revisión manual del flujo con usuario nuevo.

## Archivos y entregables esperados
- Cambios HTML/CSS/JS consistentes con front existente.
- Capturas y pruebas UI, textos de ayuda actualizados.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-15, BACK-11.
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

![Captura del Issue #71](%5BFRONT-11%5D%20Actualizar%20concepto%20visual%20de%20ApuntIA%20para%20pizarrones%20y%20cuadernos.png)
