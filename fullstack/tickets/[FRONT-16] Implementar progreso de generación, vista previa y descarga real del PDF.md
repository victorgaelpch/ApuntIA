# [FRONT-16] Implementar progreso de generación, vista previa y descarga real del PDF

- Numero de Issue: #76
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/76
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:40:28 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:43 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:43 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:40:28Z
- Cierre UTC: 2026-11-10T17:02:43Z

- Fecha de captura: 2026-11-24 12:08:23 -0600 (CDMX)
- [Captura original](%5BFRONT-16%5D%20Implementar%20progreso%20de%20generaci%C3%B3n%2C%20vista%20previa%20y%20descarga%20real%20del%20PDF-original.png)
- [Captura con metadatos](%5BFRONT-16%5D%20Implementar%20progreso%20de%20generaci%C3%B3n%2C%20vista%20previa%20y%20descarga%20real%20del%20PDF.png)

## Descripcion original

## Objetivo
Permitir que el usuario solicite y descargue un PDF académico completo con vista previa, elección de contenido y progreso real, sin confundir la exportación PNG anterior con la nueva funcionalidad.

## Contexto técnico y alcance
El backend puede tardar minutos si realiza OCR/fórmulas/investigación; la UI no debe bloquear ni decir `completado` antes de recibir una exportación válida.

## Actividades detalladas
- [ ] Agregar asistente/opciones de exportación: título, portada, nivel de detalle, incluir originales, referencias y diseño disponible.
- [ ] Mostrar etapas y estado desde API (`pendiente`, `procesando`, `completado`, `fallido`, `cancelado`) con progreso solo si backend lo informa.
- [ ] Permitir cancelar/reintentar de forma segura y recuperar exportación al refrescar una página autenticada.
- [ ] Mostrar vista previa PDF accesible, alternativa de descargar sin preview y miniaturas de páginas si hay soporte.
- [ ] Descargar con nombre correcto y tipo MIME, evitando URLs públicas de archivos privados y limpiando Blob URLs temporales.
- [ ] Distinguir descarga de imagen mejorada PNG vs PDF con contenido estructurado.
- [ ] Informar si faltan fórmulas o bloques sin revisar antes de exportar, sin impedir que el usuario elija fallback.
- [ ] Invalidar vista previa obsoleta cuando la nota fue editada y requerir regeneración.
- [ ] Manejar 401/403/404/409/413/429/500, timeout y errores de PDF sin mostrar detalles internos.
- [ ] Actualizar estados vacíos, navegación y ayuda del frontend.

## Criterios de aceptación
- [ ] Un usuario puede ver y descargar un PDF válido de la versión actual de sus notas.
- [ ] Estado y mensajes reflejan verdaderos resultados del backend.
- [ ] No se publican URLs permanentes accesibles por otros usuarios.
- [ ] La exportación sigue funcionando tras un refresco y no reutiliza PDFs obsoletos.

## Pruebas y verificación obligatoria
- Playwright: éxito, falla, cancelación, reintento, PDF obsoleto, sesión expirada.
- Verificar MIME, firma `%PDF`, nombre seguro, tamaño mayor que cero y apertura del archivo.
- Prueba móvil y descarga desde historial.

## Archivos y entregables esperados
- UI exportación/progreso/preview y tests.
- Documentación de opciones PDF y estados.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-19..BACK-21; BACK-27; FRONT-13..FRONT-15.
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

![Captura del Issue #76](%5BFRONT-16%5D%20Implementar%20progreso%20de%20generaci%C3%B3n%2C%20vista%20previa%20y%20descarga%20real%20del%20PDF.png)
