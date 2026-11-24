# [BACK-20] Generar PDF académico completo con fórmulas, tablas, esquemas e índice ETIQUETA: backend

- Numero de Issue: #63
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/63
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:34:27 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:25 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:25 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:34:27Z
- Cierre UTC: 2026-11-10T17:02:25Z

- Fecha de captura: 2026-11-24 12:07:23 -0600 (CDMX)
- [Captura original](%5BBACK-20%5D%20Generar%20PDF%20acad%C3%A9mico%20completo%20con%20f%C3%B3rmulas%2C%20tablas%2C%20esquemas%20e%20%C3%ADndice%20ETIQUETA-%20backend-original.png)
- [Captura con metadatos](%5BBACK-20%5D%20Generar%20PDF%20acad%C3%A9mico%20completo%20con%20f%C3%B3rmulas%2C%20tablas%2C%20esquemas%20e%20%C3%ADndice%20ETIQUETA-%20backend.png)

## Descripcion original

## Objetivo
Implementar un generador real de archivos PDF de apuntes que convierta el documento semántico en páginas legibles, con tipografía, saltos adecuados, fórmulas matemáticas, imágenes, diagramas, tablas y referencias verificables.

## Contexto técnico y alcance
El servicio actual devuelve un PNG procesado, no un PDF con notas. Este Issue incorpora exportación auténtica. Evaluar ReportLab, WeasyPrint u otro motor según render seguro de matemáticas y soporte Unicode; no elegir biblioteca por moda.

## Actividades detalladas
- [ ] Definir plantillas para portada, título, fecha, origen, secciones, índice, encabezado/pie, paginación y bibliografía.
- [ ] Renderizar texto seleccionable y Unicode; incluir fuentes legales y manejar caracteres especiales/español.
- [ ] Renderizar fórmulas LaTeX de forma segura (subconjunto permitido o pipeline sandboxed) sin ejecutar instrucciones arbitrarias.
- [ ] Representar tablas con encabezados repetidos, ancho adecuado y saltos entre páginas sin cortar información.
- [ ] Incluir esquemas/diagramas vectoriales si se dispone de estructura; fallback a recortes de imagen con resolución suficiente.
- [ ] Añadir etiquetas visuales para texto extraído, texto corregido y ampliación investigada; mostrar fuentes URL/título/fecha cuando existan.
- [ ] Controlar layout de varias páginas, encabezados huérfanos, imágenes demasiado grandes, márgenes e interlineado.
- [ ] Configurar estilos opcionales (básico/extendido), idioma, inclusión de originales y metadatos del archivo.
- [ ] Proteger contra inyección HTML, rutas remotas no autorizadas, macros LaTeX y archivos temporales sin limpiar.
- [ ] Generar binario `application/pdf`, nombre seguro, checksum y metadatos de versión sin exponer información personal en PDFs de demo.

## Criterios de aceptación
- [ ] El PDF abre en lectores comunes y contiene texto seleccionable, fórmulas legibles, tablas y esquemas.
- [ ] Múltiples páginas no se solapan ni recortan, con formato consistente.
- [ ] El contenido y los cambios del usuario coinciden con la última versión confirmada del apunte.
- [ ] El generador falla de manera controlada ante contenido imposible, sin producir PDF vacío engañoso.

## Pruebas y verificación obligatoria
- Pruebas de apertura/lectura con PyMuPDF/pypdf u otra herramienta, selección de texto y número de páginas.
- Inspección visual de fórmulas, tabla larga, gráfico, tildes, varias páginas y contenido malicioso.
- Pruebas de carga de memoria y limpieza de temporales.

## Archivos y entregables esperados
- Motor PDF, plantilla(s) y API/servicio de exportación.
- PDFs de ejemplo sintéticos y tests automatizados.
- Documentación de fuentes y motor de matemáticas.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-15..BACK-19.
- **Área responsable:** backend.
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

![Captura del Issue #63](%5BBACK-20%5D%20Generar%20PDF%20acad%C3%A9mico%20completo%20con%20f%C3%B3rmulas%2C%20tablas%2C%20esquemas%20e%20%C3%ADndice%20ETIQUETA-%20backend.png)
