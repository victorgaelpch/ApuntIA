# [FRONT-18] Crear panel Mis apuntes con historial, búsqueda, filtros y acceso a PDFs

- Numero de Issue: #78
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/78
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:41:04 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:46 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:46 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:41:04Z
- Cierre UTC: 2026-11-10T17:02:46Z

- Fecha de captura: 2026-11-24 12:08:33 -0600 (CDMX)
- [Captura original](%5BFRONT-18%5D%20Crear%20panel%20Mis%20apuntes%20con%20historial%2C%20b%C3%BAsqueda%2C%20filtros%20y%20acceso%20a%20PDFs-original.png)
- [Captura con metadatos](%5BFRONT-18%5D%20Crear%20panel%20Mis%20apuntes%20con%20historial%2C%20b%C3%BAsqueda%2C%20filtros%20y%20acceso%20a%20PDFs.png)

## Descripcion original

## Objetivo
Ofrecer un dashboard privado donde cada usuario consulte sus apuntes anteriores, revise estado, entre a editar, regenere PDF, descargue y borre documentos con confirmaciones.

## Contexto técnico y alcance
Los apuntes pueden estar en progreso, incompletos o fallidos; no mostrar siempre `listo`. El backend debe paginar y filtrar por propietario para evitar cargar datos de otros usuarios.

## Actividades detalladas
- [ ] Diseñar página `Mis apuntes` con lista/tarjetas que incluyan título, fecha, tipo de fuente, páginas y estado.
- [ ] Integrar lista paginada, búsqueda por título y filtros de fecha/estado conforme a API real.
- [ ] Ofrecer acciones Ver, Editar, Continuar proceso, Exportar PDF y Eliminar, solo donde permisos y estados lo permitan.
- [ ] Implementar confirmación de borrado y feedback de éxito/error; evitar borrar accidentalmente por un clic.
- [ ] Crear vistas vacías con CTA de crear primer apunte, skeletons y reintento para fallos de red.
- [ ] Cargar detalle completo bajo demanda, no incrustar imágenes privadas en listados.
- [ ] Gestionar 401/403, sesión expirada y recurso borrado sin filtrar datos.
- [ ] Mantener scroll/navegación y estado al regresar desde el editor.
- [ ] Implementar diseño accesible y responsive para dispositivos de poco ancho.

## Criterios de aceptación
- [ ] Una persona ve solo sus notas y puede consultarlas tras cerrar/reabrir sesión.
- [ ] Los controles están conectados a API real, con errores de borrado/edición manejados.
- [ ] No hay notas de otro usuario, incluso si se manipula la URL.
- [ ] Los estados pendientes o fallidos se representan correctamente.

## Pruebas y verificación obligatoria
- E2E con usuario A/B, paginación/búsqueda, nota vacía, nota borrada y reintento.
- Descarga de PDF desde historial y acceso después de refrescar.
- Test accesibilidad teclado y móvil.

## Archivos y entregables esperados
- Dashboard privado y componentes reutilizables.
- Pruebas, capturas y documentación del historial.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-22, BACK-26, FRONT-17.
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

![Captura del Issue #78](%5BFRONT-18%5D%20Crear%20panel%20Mis%20apuntes%20con%20historial%2C%20b%C3%BAsqueda%2C%20filtros%20y%20acceso%20a%20PDFs.png)
