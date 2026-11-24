# [FULL-29] Reorganizar toda la documentación y centralizar los tickets de trabajo con trazabilidad real

- Numero de Issue: #93
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/93
- Estado: open
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: fullStack
- Creacion GitHub: 2026-11-13 18:33:50 -0600 (CDMX)
- Cierre GitHub: No registrada / no aplica
- Actualizacion GitHub: 2026-11-13 18:33:50 -0600 (CDMX)
- Creacion UTC: 2026-11-14T00:33:50Z
- Cierre UTC: No aplica

- Fecha de captura: 2026-11-24 12:09:31 -0600 (CDMX)
- [Captura original](%5BFULL-29%5D%20Reorganizar%20toda%20la%20documentaci%C3%B3n%20y%20centralizar%20los%20tickets%20de%20trabajo%20con%20trazabilidad%20real-original.png)
- [Captura con metadatos](%5BFULL-29%5D%20Reorganizar%20toda%20la%20documentaci%C3%B3n%20y%20centralizar%20los%20tickets%20de%20trabajo%20con%20trazabilidad%20real.png)

## Descripcion original

## Objetivo — FULL-29
Cumplir la nueva organización solicitada por el profesor: documentación transversal exclusivamente bajo `fullstack/docs/`, documentación específica de la interfaz bajo `front/docs/`, y TODOS los tickets del proyecto consultables en `fullstack/tickets/` con fechas, horas, responsable, estado y evidencia comprobable. Preservar la historia y enlaces sin fabricar bitácoras.

## Contexto real del repositorio
Actualmente existe `docs/` en la raíz con mucha documentación enlazada desde `README.md`, `fullstack/README.md`, backend, frontend y validaciones de CI. `fullstack/` ya contiene scripts, Docker, pruebas y evaluación. No generar copias paralelas ni eliminar archivos sin actualizar cada referencia.

## Dependencias
Ninguna. Es base para todos los demás Issues.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-11-13 · 18:00–20:00 (America/Mexico_City): Auditoría de rutas, documentación, tickets e historial de GitHub.
- [ ] 2026-11-14 · 10:00–12:30 (America/Mexico_City): Migración controlada de documentación y creación del índice de tickets.
- [ ] 2026-11-16 · 18:30–20:30 (America/Mexico_City): Corrección de vínculos, CI y validación de navegación.

## Tareas técnicas detalladas
#### A. Inventario y reglas de ubicación
- [ ] Hacer inventario por ruta de `docs/`, `front/`, `back/`, `fullstack/`, `.github/`, pruebas y archivos `*.md`; clasificar documentos como globales (arquitectura, API, seguridad, pruebas, algoritmos, despliegue, investigación, aceptación), frontend (pantallas, estados, UI, accesibilidad, contratos consumidos) y backend (notas técnicas internas junto al código, enlazadas desde la documentación global).
- [ ] Definir y añadir `fullstack/docs/ESTRUCTURA_DOCUMENTAL.md` con el árbol real y reglas de ubicación; evitar duplicación: una fuente canónica por tema.
- [ ] Migrar la documentación general con `git mv docs fullstack/docs`, preservando historial; crear `front/docs/README.md` y mover allí las guías específicas del frontend sin romper referencias relativas a imágenes o recursos.
- [ ] Actualizar enlaces relativos y absolutos en README raíz, `fullstack/README.md`, `CONTRIBUTING.md`, changelog, API, módulos backend, CI, workflows, scripts, frontend y pruebas de documentación. Comprobar anclas y Mermaid.
- [ ] Considerar impacto en enlaces externos a `docs/`; documentar ruta antigua/nueva y, únicamente si el profesor lo permite, añadir un aviso de migración ligero; no conservar duplicados de documentación global.
#### B. Todos los tickets con fecha y hora
- [ ] Crear `fullstack/tickets/README.md`, `INDICE.md`, `PLANTILLA_TICKET.md` y `cronograma-planeado.md`.
- [ ] Crear `fullstack/scripts/sincronizar_tickets.py` o equivalente para recuperar issues abiertos Y cerrados del repositorio, paginando correctamente y distinguiendo Pull Requests de Issues en la API de GitHub; usar datos públicos o `GITHUB_TOKEN` por variable de entorno si hace falta.
- [ ] Generar un archivo Markdown por identificador lógico (`FULL-*`, `BACK-*`, `FRONT-*`) cuando exista; si no hay identificador, conservar `issue-<numero>.md`. No asumir que `[FULL-29]` equivale a GitHub `#29`.
- [ ] Guardar en cada ficha: título, número real de GitHub, URL, área, etiquetas, responsable, dependencias, estado, `created_at`, `updated_at`, `closed_at` si existe, fecha/hora con zona `America/Mexico_City` y origen exacto de cada dato.
- [ ] Distinguir en campos separados `FECHA PLANIFICADA`, `REGISTRO REAL` y `EVIDENCIA`; la creación de un Issue NO demuestra que se haya trabajado ese día. Registrar horas reales solo durante sesiones efectivas, asociadas a commits, PR y pruebas.
- [ ] Mantener manualmente bitácoras y notas sin que el sincronizador las sobrescriba; usar metadatos/snapshots regenerables y secciones delimitadas, o archivos separados `bitacora/`.
- [ ] Indexar los tickets existentes, no solo los nuevos: usar API GitHub y, si se dispone, referencias de Trello. No exponer claves de GitHub o Trello.
- [ ] Documentar comandos para sincronizar después de un Issue/PR, política de actualizaciones, zona horaria, resolución de conflictos y uso offline con snapshot existente.
#### C. Evidencia y validación
- [ ] Implementar comprobador de enlaces Markdown con fallo explícito y listado de rutas rotas; validar links en CI.
- [ ] Probar sincronizador con Issue abierto, cerrado, sin etiqueta, sin fecha de cierre, paginación, respuesta 403/429, red caída y ejecución repetida sin duplicados.
- [ ] Verificar que toda la documentación del sitio puede encontrarse desde README y `fullstack/docs/README.md`.

## Errores previsibles y recuperación manual
- API GitHub inaccesible o límite de peticiones: usar snapshot local, mostrar aviso y ofrecer reintentar sin generar fechas inventadas.
- Dos Issues con prefijo igual: NO sobrescribir; registrar colisión y resolver contra URLs/número real.
- Vínculo roto después de mover `docs/`: bloquear aceptación hasta reparar o registrar excepción documentada.
- Historias previas sin fecha de sesión: mostrar `no registrada`, nunca estimarla como ejecutada.

## Pruebas y evidencia obligatoria
- `git diff --find-renames` verifica preservación de documentos; script de enlaces detecta rutas inexistentes; `npm run test:front`, `npm run test:integracion`, `python -m pytest` y CI no fallan por migración.
- Crear fixtures sintéticos de 4 Issues (abierto/cerrado/PR/duplicado), ejecutar sincronización dos veces y verificar idempotencia.
- Demostrar con capturas el índice de tickets y al menos una bitácora REAL fechada en la hora efectiva de trabajo.

## Entregables
- `fullstack/docs/` con índice y arquitectura documental; `front/docs/` con guías de UI.
- `fullstack/tickets/` con todos los tickets sincronizados, plan de sesiones y plantilla de bitácora real.
- Script de sincronización y pruebas; README y enlaces actualizados; PR con evidencia de migración.

## Criterios de aceptación (Definition of Done)
- [ ] No queda documentación general duplicada en `docs/` raíz.
- [ ] Todos los tickets existentes en GitHub se reflejan o quedan listados con razón de exclusión explícita.
- [ ] Cada ticket muestra fecha y hora de creación/actualización reales, zona horaria y fuente; progreso/horas solo si hay evidencia.
- [ ] No hay vínculos rotos introducidos y los comandos públicos siguen funcionando.
- [ ] Sin secretos ni datos personales en tickets/bitácoras.

### Instrucciones obligatorias para Claude (aplican a este Issue)
- ANTES DE MODIFICAR: inspeccionar el estado real de `main`, ramas/PR abiertos, issues anteriores, rutas y contratos; presentar mapa de archivos afectados, dependencias y riesgos. El repositorio tiene `front/`, `back/motori_magenes/`, `fullstack/`, `docs/` (que se migrará), `iniciar.bat`, `iniciar.sh` y `fullstack/compose.yaml`. No asumir Spring Boot: el backend actual es FastAPI.
- REUTILIZAR: preservar endpoints `/analisis` (v1), `/apuntes`, `/trabajos/{id}`, el editor, autenticación, almacenamiento/versiones, PDF y pruebas de regresión. No duplicar lógica ni migrar funcionalidades de manera destructiva.
- DESARROLLO INCREMENTAL: rama `feature/<ID>-descripcion`, cambios pequeños, pruebas antes/después; PR enlazado a este Issue, descripción de archivos, capturas o logs saneados, resultados verificables. No fusionar si CI está roja. No sobrescribir correcciones humanas.
- SEGURIDAD: sin claves, tokens, contraseñas, datos privados, fotografías reales de estudiantes ni modelos pesados en Git. Utilizar `.env.example`, `.gitignore` y almacenamiento seguro del sistema operativo cuando proceda; nunca registrar el contenido de los apuntes ni encabezados de autorización.
- FALLOS: para todo punto crítico, definir comportamiento normal, fallo detectado, reintento acotado, alternativa manual o modo degradado, mensaje útil, código de error, prueba reproducible y forma de recuperación sin pérdida de datos.
- DOCUMENTACIÓN: actualizar las secciones aplicables en `fullstack/docs/`, `front/docs/` y enlaces del `README.md` raíz (una vez hecha la migración del Issue FULL-29); documentar razones técnicas y límites reales, no prometer reconocimiento perfecto.
- BITÁCORA: registrar hora REAL de ejecución y evidencias (commit, PR, test) en `fullstack/tickets/`; los horarios propuestos de este archivo son PLANIFICACIÓN, no trabajo realizado. No inventar fechas históricas ni resultados de pruebas.

## Registro de trabajo (rellenar únicamente al ejecutarlo)
- [ ] Sesión real: YYYY-MM-DD HH:MM–HH:MM (America/Mexico_City). Responsable: ____. Actividad realizada: ____. Evidencia Git SHA / PR / prueba: ____.
- [ ] PR de entrega: URL real: ____. Resultado CI: ____. Riesgos pendientes y plan de reversión: ____.



## Evidencia visual

![Captura del Issue #93](%5BFULL-29%5D%20Reorganizar%20toda%20la%20documentaci%C3%B3n%20y%20centralizar%20los%20tickets%20de%20trabajo%20con%20trazabilidad%20real.png)
