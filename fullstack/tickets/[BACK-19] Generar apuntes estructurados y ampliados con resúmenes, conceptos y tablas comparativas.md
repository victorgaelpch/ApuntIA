# [BACK-19] Generar apuntes estructurados y ampliados con resúmenes, conceptos y tablas comparativas

- Numero de Issue: #62
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/62
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:34:06 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:24 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:24 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:34:06Z
- Cierre UTC: 2026-11-10T17:02:24Z

- Fecha de captura: 2026-11-24 12:07:20 -0600 (CDMX)
- [Captura original](%5BBACK-19%5D%20Generar%20apuntes%20estructurados%20y%20ampliados%20con%20res%C3%BAmenes%2C%20conceptos%20y%20tablas%20comparativas-original.png)
- [Captura con metadatos](%5BBACK-19%5D%20Generar%20apuntes%20estructurados%20y%20ampliados%20con%20res%C3%BAmenes%2C%20conceptos%20y%20tablas%20comparativas.png)

## Descripcion original

## Objetivo
Transformar el documento editado en un apunte académico coherente con portada, índice/secciones, objetivos, explicaciones, resúmenes, ejemplos, conceptos clave, tablas comparativas y esquemas cuando los datos lo justifiquen.

## Contexto técnico y alcance
La generación debe respetar fidelidad, procedencia, legibilidad y control del usuario. No agregar hechos inventados para rellenar el PDF ni presentar contenido investigado como si fuera una transcripción exacta.

## Actividades detalladas
- [ ] Definir un esquema de salida semántica (título, subtítulos, contenido fuente, fórmulas, imágenes, tabla, notas, ampliación, citas, conclusiones).
- [ ] Crear una etapa de planificación del documento basada en lo extraído/corregido y las preferencias de longitud/detalle del usuario.
- [ ] Agregar resumen, glosario o definiciones solo cuando haya información suficiente o referencia verificable.
- [ ] Generar tablas comparativas solo si hay elementos comparables y atributos claros, evitando completar celdas con datos supuestos.
- [ ] Proponer esquemas/diagramas con relaciones respaldadas; incluir ilustración original cuando el gráfico no se pueda reconstruir.
- [ ] Distinguir visualmente secciones `Transcripción del apunte` y `Información complementaria`.
- [ ] Permitir configurar nivel de detalle, idioma, inclusión de investigación, portada y uso de imágenes originales.
- [ ] Validar consistencia de fórmulas, nombres técnicos, unidades y orden de secciones antes del render.
- [ ] No destruir edición del usuario cuando se regenere; generar nueva versión y guardar diff.
- [ ] Producir un formato intermedio HTML/AST validado, independiente del motor PDF.

## Criterios de aceptación
- [ ] Se genera una estructura con secciones apropiadas a cada nota, sin párrafos de relleno inventados.
- [ ] La información investigada aparece separada y citada.
- [ ] Fórmulas, tablas e imágenes mantienen sentido y procedencia.
- [ ] Se puede editar contenido y regenerar sin perder versiones anteriores.

## Pruebas y verificación obligatoria
- Caso de ciencias con fórmula, historia con resumen, tema con tabla comparativa y nota mínima que no permite ampliación.
- Revisión de trazabilidad origen -> sección, coherencia y ausencia de citas inexistentes.
- Tests de salida estructurada y validación.

## Archivos y entregables esperados
- Generador de apunte estructurado y plantillas de estilo.
- Esquemas, fixtures y tests de coherencia.
- Documentación de secciones opcionales y restricciones.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-17, BACK-18.
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

![Captura del Issue #62](%5BBACK-19%5D%20Generar%20apuntes%20estructurados%20y%20ampliados%20con%20res%C3%BAmenes%2C%20conceptos%20y%20tablas%20comparativas.png)
