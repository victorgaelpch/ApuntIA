# Cronograma PLANIFICADO de ApuntIA 3.0

> **Esto es una propuesta para repartir el trabajo, no un registro de actividad.** Que una fecha
> haya pasado no significa que la sesión ocurriera. El trabajo real está en [bitacora/](bitacora/README.md)
> y en la sección «REGISTRO REAL» de cada ficha.

Fuente: documento «ApuntIA 3.0 — Issues para GitHub», preparado el 12/11/2026, y las descripciones
de los Issues #93–#101. Zona horaria: America/Mexico_City.

## Fases y dependencias

| Fase | Issues | Depende de |
|------|--------|------------|
| 1 | FULL-29 | — |
| 2 | FULL-30, BACK-35 (en paralelo) | FULL-29 |
| 3 | FULL-31, BACK-36 | BACK-35, FULL-30 |
| 4 | BACK-37, FRONT-25, FRONT-26 | FULL-31, BACK-36 |
| 5 | BACK-38, FULL-32 | Todo lo anterior |

## Sesiones propuestas

| ID | Issue | Fecha | Horario (CDMX) | Actividad prevista |
|----|-------|-------|----------------|--------------------|
| FULL-29 | [#93](https://github.com/victorgaelpch/ApuntIA/issues/93) | 2026-11-13 | 18:00–20:00 | Auditoría de rutas, documentación, tickets e historial de GitHub |
| FULL-29 | #93 | 2026-11-14 | 10:00–12:30 | Migración controlada de documentación e índice de tickets |
| FULL-29 | #93 | 2026-11-16 | 18:30–20:30 | Corrección de vínculos, CI y validación de navegación |
| FULL-30 | [#94](https://github.com/victorgaelpch/ApuntIA/issues/94) | 2026-11-17 | 18:00–20:00 | Diseño de menú y compatibilidad de scripts |
| FULL-30 | #94 | 2026-11-18 | 18:30–21:00 | Instalador y perfiles |
| FULL-30 | #94 | 2026-11-20 | 17:30–20:30 | Pruebas de arranque/detención y recuperación |
| BACK-35 | **sin Issue en GitHub** | 2026-11-17 | 19:00–21:00 | Inspección de APIs, esquemas y responsabilidades |
| BACK-35 | — | 2026-11-19 | 18:00–21:00 | Servidor de inferencia y adaptadores |
| BACK-35 | — | 2026-11-21 | 10:00–13:00 | Contrato, pruebas simuladas, inferencia real y memoria GPU |
| FULL-31 | [#95](https://github.com/victorgaelpch/ApuntIA/issues/95) | 2026-11-23 | 18:00–21:00 | Contrato de conexión, riesgos y túnel |
| FULL-31 | #95 | 2026-11-25 | 18:00–21:00 | Emparejamiento y credenciales locales |
| FULL-31 | #95 | 2026-11-28 | 10:00–13:00 | Pruebas desde otra red y recuperación manual |
| BACK-36 | [#96](https://github.com/victorgaelpch/ApuntIA/issues/96) | 2026-11-24 | 18:00–21:00 | Corpus, preprocesamiento, ROI y contratos de bloque |
| BACK-36 | #96 | 2026-11-27 | 18:00–22:00 | Pipeline híbrido OCR/VLM, fórmulas y diagramas |
| BACK-36 | #96 | 2026-11-30 | 18:00–21:00 | Benchmark y comparación de motores |
| BACK-37 | [#97](https://github.com/victorgaelpch/ApuntIA/issues/97) | 2026-11-30 | 19:00–21:00 | Estados de trabajos y reanudación |
| BACK-37 | #97 | 2026-12-02 | 18:00–21:00 | Cola y adaptador sin duplicación; códigos de error |
| BACK-37 | #97 | 2026-12-04 | 18:00–20:00 | Pruebas de fallos reales y recuperación |
| FRONT-25 | [#98](https://github.com/victorgaelpch/ApuntIA/issues/98) | 2026-11-28 | 16:00–18:00 | UX de conexión y estados con API simulada |
| FRONT-25 | #98 | 2026-11-30 | 18:00–20:30 | Emparejamiento, perfil y mensajes |
| FRONT-25 | #98 | 2026-12-02 | 18:30–20:30 | E2E, teclado y móvil |
| FRONT-26 | [#99](https://github.com/victorgaelpch/ApuntIA/issues/99) | 2026-12-03 | 18:00–20:30 | Revisión del editor y anotación por región |
| FRONT-26 | #99 | 2026-12-04 | 18:00–21:00 | Revisión, comparación y edición estructurada |
| FRONT-26 | #99 | 2026-12-05 | 10:00–12:30 | E2E y documentación de UI |
| BACK-38 | [#100](https://github.com/victorgaelpch/ApuntIA/issues/100) | 2026-12-04 | 19:00–21:00 | Auditoría de investigación y PDF; esquema de evidencia |
| BACK-38 | #100 | 2026-12-07 | 18:00–21:00 | Bloques multimodales, enriquecimiento y PDF |
| BACK-38 | #100 | 2026-12-08 | 18:00–21:00 | Pruebas de citas, fórmulas, esquemas y regresión |
| FULL-32 | [#101](https://github.com/victorgaelpch/ApuntIA/issues/101) | 2026-12-09 | 17:30–21:00 | Revisión integrada de contratos, CI y seguridad |
| FULL-32 | #101 | 2026-12-10 | 18:00–21:30 | Instalación real y comunicación entre dos redes |
| FULL-32 | #101 | 2026-12-12 | 10:00–14:00 | Aceptación de fotos, PDFs y documentación de entrega |

## Observaciones de la auditoría (13/11/2026)

- **BACK-35 no existe como Issue en GitHub** (se crearon 9 de los 10). Hay que crearlo con el texto
  del documento antes de empezar la fase 2; el sincronizador lo señala en el índice mientras falte.
- El PR #92 (cerrado sin fusionar) y la rama `full-30-ia-motores` usan el prefijo `[FULL-30]` para
  un trabajo distinto (interfaz de motores y VLM opcional). No es el Issue FULL-30 (#94); su
  contenido puede reutilizarse en BACK-35/BACK-36 tras revisarlo.
