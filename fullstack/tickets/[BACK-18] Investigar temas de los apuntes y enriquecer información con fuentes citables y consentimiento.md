# [BACK-18] Investigar temas de los apuntes y enriquecer información con fuentes citables y consentimiento

- Numero de Issue: #61
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/61
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:33:51 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:22 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:22 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:33:51Z
- Cierre UTC: 2026-11-10T17:02:22Z

- Fecha de captura: 2026-11-24 12:07:15 -0600 (CDMX)
- [Captura original](%5BBACK-18%5D%20Investigar%20temas%20de%20los%20apuntes%20y%20enriquecer%20informaci%C3%B3n%20con%20fuentes%20citables%20y%20consentimiento-original.png)
- [Captura con metadatos](%5BBACK-18%5D%20Investigar%20temas%20de%20los%20apuntes%20y%20enriquecer%20informaci%C3%B3n%20con%20fuentes%20citables%20y%20consentimiento.png)

## Descripcion original

## Objetivo
Implementar enriquecimiento educativo opcional: identificar conceptos de la nota, buscar fuentes confiables, contrastar información y proponer explicaciones complementarias sin alterar ni atribuir al usuario contenido que no estaba en su apunte.

## Contexto técnico y alcance
La investigación puede utilizar búsqueda web/API o repositorio local de materiales con licencias verificadas. No existe garantía de fuentes confiables o internet; el sistema debe funcionar sin investigación. Fotos y apuntes pueden contener información privada: nunca enviarlos sin consentimiento.

## Actividades detalladas
- [ ] Definir extracción de temas, entidades y conceptos desde contenido corregido y consentimiento explícito por documento.
- [ ] Diseñar adaptador de proveedor de investigación con configuración segura, timeout, cuotas, cache limitada y fallback desactivable.
- [ ] Priorizar fuentes educativas confiables y accesibles, almacenar título, URL, autor/editor, fecha de consulta y fragmento mínimo.
- [ ] Verificar que cada afirmación relevante del complemento tenga respaldo en fuente real; no inventar enlaces, DOI, autores ni citas.
- [ ] Distinguir hechos del material original, conocimiento adicional, inferencias y contenidos sin verificación.
- [ ] Agregar criterio de contradicciones: si la fuente externa difiere del apunte, mostrar discrepancia y pedir revisión en vez de reemplazar silenciosamente.
- [ ] Respetar robots/licencias/términos y derechos de autor, parafrasear con atribución y evitar copiar artículos completos.
- [ ] Tratar páginas externas, HTML y el OCR como datos no confiables; ignorar instrucciones incrustadas y bloquear SSRF/URLs internas.
- [ ] Ofrecer modo sin internet/proveedor no configurado y permitir crear PDF solo con texto de origen.
- [ ] Loguear solo métricas técnicas sin almacenar búsquedas privadas innecesariamente; exponer origen de cada sección al frontend.

## Criterios de aceptación
- [ ] Cada ampliación muestra una fuente comprobable o se marca como sin verificar/no se incluye.
- [ ] Una nota puede generarse sin conexión y sin credenciales externas.
- [ ] El usuario autoriza antes de enviar contenido privado a proveedores.
- [ ] No se reemplazan transcripciones originales ni se inventan referencias.

## Pruebas y verificación obligatoria
- Tests con respuestas mock verificadas, sin resultados, fuentes caídas, contradicciones y prompt injection en página.
- Revisión manual de citas y enlaces en casos de prueba controlados.
- Pruebas de privacidad y de funcionamiento offline.

## Archivos y entregables esperados
- Adaptador de investigación, esquema de citas y pruebas.
- Política de privacidad/consentimiento, documentación de fuente y costos.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-17; FULL-15; FULL-20.
- **Área responsable:** backend.
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

![Captura del Issue #61](%5BBACK-18%5D%20Investigar%20temas%20de%20los%20apuntes%20y%20enriquecer%20informaci%C3%B3n%20con%20fuentes%20citables%20y%20consentimiento.png)
