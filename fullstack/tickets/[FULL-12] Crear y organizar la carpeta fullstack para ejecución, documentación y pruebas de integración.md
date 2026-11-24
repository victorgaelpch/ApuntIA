# [FULL-12] Crear y organizar la carpeta fullstack para ejecución, documentación y pruebas de integración

- Numero de Issue: #42
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/42
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:20:55 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:03 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:03 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:20:55Z
- Cierre UTC: 2026-11-10T17:05:03Z

- Fecha de captura: 2026-11-24 12:05:44 -0600 (CDMX)
- [Captura original](%5BFULL-12%5D%20Crear%20y%20organizar%20la%20carpeta%20fullstack%20para%20ejecuci%C3%B3n%2C%20documentaci%C3%B3n%20y%20pruebas%20de%20integraci%C3%B3n-original.png)
- [Captura con metadatos](%5BFULL-12%5D%20Crear%20y%20organizar%20la%20carpeta%20fullstack%20para%20ejecuci%C3%B3n%2C%20documentaci%C3%B3n%20y%20pruebas%20de%20integraci%C3%B3n.png)

## Descripcion original

## Objetivo
Reorganizar el repositorio para que `fullstack/` concentre las herramientas transversales: arranque y detención, despliegue, pruebas de integración y documentación de arquitectura/despliegue. Mantener el código funcional en sus capas originales y hacer una migración no disruptiva.

## Contexto técnico y alcance
Situación a comprobar: en `main` se observan `index.html`, `front/`, `back/motori_magenes/`, `docs/`, `tests/integracion/`, `requirements.txt` y `package.json`. No asumir que los scripts de FULL-11 están fusionados: buscar también ramas y PR. `fullstack/` NO sustituye a `front/` ni a `back/`, ni debe absorber pruebas unitarias propias de esas capas.

## Actividades detalladas
- [ ] Revisar árbol real, scripts de arranque, workflows, rutas de importación y referencias documentales antes de mover archivos.
- [ ] Crear `fullstack/README.md` y una estructura razonada: `fullstack/scripts/`, `fullstack/docker/` (si procede), `fullstack/tests/integracion/`, `fullstack/docs/` y `fullstack/config/` solo si son útiles.
- [ ] Ubicar bajo `fullstack/` las herramientas transversales de ejecución; mantener `iniciar.bat`/`iniciar.sh` en la raíz como lanzadores compatibles si ya se utilizan.
- [ ] Trasladar o referenciar pruebas transversales preservando los comandos públicos de `package.json` y las referencias a `tests/integracion/`.
- [ ] Definir qué documentos permanecen en `docs/` y cuáles van a `fullstack/docs/`; crear enlaces relativos correctos y evitar duplicados divergentes.
- [ ] Ajustar rutas de `requirements`, imports, configuración de Playwright, scripts y CI sin crear rutas absolutas.
- [ ] Agregar ejemplos de configuración (`.env.example`) sin credenciales, y actualizar `.gitignore` para datos, PDFs, secretos, entornos y archivos temporales.
- [ ] Documentar un mapa de carpetas, propietarios, dependencias entre módulos y reglas de ubicación para nuevos archivos.
- [ ] Actualizar las rutas del README raíz y revisar que el flujo existente `POST /analisis` y `GET /salud` siga funcionando.
- [ ] Preparar migración incremental en PR acotado, sin reescribir innecesariamente la lógica funcional.

## Criterios de aceptación
- [ ] Existe `fullstack/` con propósito definido y estructura documentada, sin copias innecesarias de código del frontend/backend.
- [ ] Los lanzadores públicos y comandos de pruebas anteriores se mantienen o tienen sustitutos con compatibilidad comprobada.
- [ ] Ningún enlace de la documentación apunta a rutas inexistentes y no se incluyen secretos ni datos personales.
- [ ] El endpoint heredado de procesamiento y la interfaz actual siguen operativos.
- [ ] El PR enumera archivos movidos, referencias corregidas y cualquier incompatibilidad justificada.

## Pruebas y verificación obligatoria
- Ejecutar comandos de pruebas backend y frontend existentes antes y después del traslado, registrar resultados.
- Ejecutar la suite de integración real y probar arranque/paro en entorno limpio.
- Comprobar enlaces relativos del README y ausencia de rutas locales o hardcoded.

## Archivos y entregables esperados
- Carpeta `fullstack/` estructurada y documentada.
- Lanzadores de raíz y rutas de pruebas actualizados.
- README raíz y documentación de arquitectura sincronizados.
- PR con evidencia de la regresión.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-11 (scripts existentes o rama/PR donde se desarrollaron).
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

![Captura del Issue #42](%5BFULL-12%5D%20Crear%20y%20organizar%20la%20carpeta%20fullstack%20para%20ejecuci%C3%B3n%2C%20documentaci%C3%B3n%20y%20pruebas%20de%20integraci%C3%B3n.png)
