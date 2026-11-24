# [FRONT-22] Añadir revisión de versiones, autosalvado controlado y comparación de cambios de apuntes

- Numero de Issue: #82
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/82
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:42:40 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:52 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:52 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:42:40Z
- Cierre UTC: 2026-11-10T17:02:52Z

- Fecha de captura: 2026-11-24 12:08:50 -0600 (CDMX)
- [Captura original](%5BFRONT-22%5D%20A%C3%B1adir%20revisi%C3%B3n%20de%20versiones%2C%20autosalvado%20controlado%20y%20comparaci%C3%B3n%20de%20cambios%20de%20apuntes-original.png)
- [Captura con metadatos](%5BFRONT-22%5D%20A%C3%B1adir%20revisi%C3%B3n%20de%20versiones%2C%20autosalvado%20controlado%20y%20comparaci%C3%B3n%20de%20cambios%20de%20apuntes.png)

## Descripcion original

## Objetivo
Mejorar la edición de documentos largos permitiendo identificar cambios de texto, fórmulas y tablas, confirmar su guardado y recuperar versiones anteriores sin sobrescribir trabajo reciente.

## Contexto técnico y alcance
Este Issue complementa el editor y el historial; no implementar una segunda base de datos en navegador ni prometer edición simultánea en tiempo real si el backend no la soporta.

## Actividades detalladas
- [ ] Mostrar fecha/versión guardada y estado de cambios locales en editor de notas.
- [ ] Implementar guardado explícito y autosalvado con debounce solo si el contrato lo soporta y con confirmación del servidor.
- [ ] Prevenir sobrescritura con tokens de versión/ETag, detectar conflictos 409 y ofrecer recuperar/copiar cambios.
- [ ] Permitir ver revisiones anteriores y comparar fragmentos (texto, fórmulas, tablas) según API de historial.
- [ ] Diferenciar contenido OCR original, cambios del usuario y ampliaciones externas en la comparación.
- [ ] Informar si el PDF disponible corresponde a una versión anterior y ofrecer regenerarlo.
- [ ] Gestionar cambios sin conexión temporal de forma explícita, sin afirmar que se guardaron en servidor.
- [ ] Evitar duplicación de peticiones y fugas de temporizadores/objetos Blob al navegar entre notas.

## Criterios de aceptación
- [ ] El editor indica correctamente cambios sin guardar y versión persistida.
- [ ] Una edición concurrente no se pierde silenciosamente.
- [ ] Se puede consultar una revisión anterior y generar PDF de versión seleccionada según contrato.
- [ ] El usuario distingue contenido original, edición y complemento investigado.

## Pruebas y verificación obligatoria
- Dos pestañas editan misma nota y se detecta conflicto.
- Corte de conexión al guardar, recuperación y aviso antes de salir.
- Regeneración de PDF tras cambios, sin documento obsoleto presentado como nuevo.

## Archivos y entregables esperados
- UI de historial/versiones y lógica de guardado.
- Tests E2E y documentación del comportamiento.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-17, BACK-26, FRONT-13, FRONT-18.
- **Área responsable:** frontend.
- **Prioridad:** Media.

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

![Captura del Issue #82](%5BFRONT-22%5D%20A%C3%B1adir%20revisi%C3%B3n%20de%20versiones%2C%20autosalvado%20controlado%20y%20comparaci%C3%B3n%20de%20cambios%20de%20apuntes.png)
