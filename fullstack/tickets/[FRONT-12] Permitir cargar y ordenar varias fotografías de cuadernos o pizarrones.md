# [FRONT-12] Permitir cargar y ordenar varias fotografías de cuadernos o pizarrones

- Numero de Issue: #72
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/72
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:38:02 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:38 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:38 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:38:02Z
- Cierre UTC: 2026-11-10T17:02:38Z

- Fecha de captura: 2026-11-24 12:08:02 -0600 (CDMX)
- [Captura original](%5BFRONT-12%5D%20Permitir%20cargar%20y%20ordenar%20varias%20fotograf%C3%ADas%20de%20cuadernos%20o%20pizarrones-original.png)
- [Captura con metadatos](%5BFRONT-12%5D%20Permitir%20cargar%20y%20ordenar%20varias%20fotograf%C3%ADas%20de%20cuadernos%20o%20pizarrones.png)

## Descripcion original

## Objetivo
Crear interfaz de entrada multipágina para subir imágenes desde dispositivo o cámara, identificar cuaderno/pizarrón, previsualizar, reordenar y descartar páginas antes de procesar.

## Contexto técnico y alcance
El frontend ya valida tipos y tamaños y soporta cámara. Reutilizar esa validación; el backend es la autoridad final. No iniciar procesamiento silencioso antes de aprobación del usuario.

## Actividades detalladas
- [ ] Agregar selector de origen `auto`, `pizarron`, `cuaderno` y descripciones del modo.
- [ ] Permitir elegir múltiples JPEG/PNG/WEBP y agregar fotos de cámara a la misma colección.
- [ ] Mostrar miniaturas, numeración y opción de cambiar orden y eliminar páginas.
- [ ] Validar tipo, tamaño, cantidad y límites actuales consultados desde API; indicar claramente cuándo falla una página.
- [ ] Mostrar advertencias de foto borrosa, incompleta o con poca luz si backend proporciona diagnóstico.
- [ ] Definir persistencia temporal de selección sin exponer archivos al almacenamiento del navegador innecesariamente.
- [ ] Implementar carga progresiva con cancelación, reintento y mensajes asociados al ID de página.
- [ ] Enviar archivos y orden exactamente según contrato v2; evitar nombres de campo inventados.
- [ ] Mantener por separado la ruta legacy de una imagen a PNG.

## Criterios de aceptación
- [ ] Se pueden agregar, ordenar y quitar páginas antes de enviar.
- [ ] La interfaz distingue el origen sin limitarse a pizarrón.
- [ ] Límites y errores concuerdan con la API; no se envían archivos inválidos de forma oculta.
- [ ] El modo anterior de una sola imagen sigue funcionando.

## Pruebas y verificación obligatoria
- Playwright: una página, varias páginas, reordenar, duplicado, archivo inválido y tamaño límite.
- Prueba cámara simulada y reconexión después de error de API.
- Verificar orden conservado por backend.

## Archivos y entregables esperados
- UI multipágina y validación frontend.
- Tests E2E y documentación de flujo.

## Dependencias y coordinación
- **Depende de / coordinar con:** FRONT-11; BACK-11; FULL-15.
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

![Captura del Issue #72](%5BFRONT-12%5D%20Permitir%20cargar%20y%20ordenar%20varias%20fotograf%C3%ADas%20de%20cuadernos%20o%20pizarrones.png)
