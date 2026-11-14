<!-- SINCRONIZADO:INICIO -->
<!-- Bloque generado por fullstack/scripts/sincronizar_tickets.py: no editar a mano (se reescribe). -->

# FULL-29 — [FULL-29] Reorganizar toda la documentación y centralizar los tickets de trabajo con trazabilidad real

| Campo | Valor |
|-------|-------|
| Identificador lógico | FULL-29 |
| Número en GitHub | [#93](https://github.com/victorgaelpch/ApuntIA/issues/93) |
| Área | Full stack |
| Etiquetas | fullStack |
| Responsable(s) | victorgaelpch |
| Estado | Abierto |
| Dependencias | Ninguna. Es base para todos los demás Issues. |
| `created_at` | 2026-11-14 00:33:50 UTC · 2026-11-13 18:33 (CDMX) |
| `updated_at` | 2026-11-14 00:33:50 UTC · 2026-11-13 18:33 (CDMX) |
| `closed_at` | — (abierto) |

Origen de los datos: la API REST de GitHub (`GET /repos/victorgaelpch/ApuntIA/issues?state=all`), snapshot [`datos/issues.json`](datos/issues.json). Zona horaria: America/Mexico_City (UTC−06:00, sin horario de verano desde 2022). Las fechas de GitHub son metadatos
del Issue (creación, última modificación, cierre), **no** horas de trabajo.

## FECHA PLANIFICADA (propuesta, no es trabajo realizado)

| Fecha | Horario (CDMX) | Actividad prevista |
|-------|----------------|--------------------|
| 2026-11-13 | 18:00–20:00 | Auditoría de rutas, documentación, tickets e historial de GitHub. |
| 2026-11-14 | 10:00–12:30 | Migración controlada de documentación y creación del índice de tickets. |
| 2026-11-16 | 18:30–20:30 | Corrección de vínculos, CI y validación de navegación. |

## REGISTRO REAL

[bitacora/FULL-29.md](bitacora/FULL-29.md) — 1 sesión(es) real(es) registrada(s)

## EVIDENCIA

ningún PR declara «Closes #93»
<!-- SINCRONIZADO:FIN -->

## Notas manuales

_Esta sección y todo lo que esté fuera del bloque sincronizado se conserva al volver a sincronizar._

### Estado por criterio de aceptación (13/11/2026)

| Criterio | Estado |
|----------|--------|
| No queda documentación general duplicada en `docs/` raíz | implementado y comprobado (`docs/` ya no existe; `git diff --find-renames` muestra 57 renombrados) |
| Todos los Issues de GitHub reflejados o excluidos con razón | implementado y probado contra la API real: 83 Issues con ficha; 18 PRs listados aparte (no son Issues) |
| Fechas reales con zona y fuente; horas solo con evidencia | implementado; las horas reales solo constan en `bitacora/` |
| Sin vínculos rotos; comandos públicos funcionan | comprobador sin errores; pytest sin regresiones en Windows; **pendiente**: `npm run test:front` y `test:integracion` (Node no está instalado en el equipo usado) → los ejecuta la CI del PR |
| Sin secretos ni datos personales | `buscar_secretos.py` sin hallazgos; solo usuarios públicos de GitHub |

- Decisión: los tres documentos de pruebas/páginas de la interfaz pasan a `front/docs/`; las
  capturas siguen en una sola carpeta (`fullstack/docs/evidencias/`) para no duplicarlas.
  Alternativa descartada: mover las capturas `front-10-*` a `front/docs/`, que partiría la carpeta
  de evidencias en dos.
- Decisión: no se deja una carpeta `docs/` con avisos de migración (evita duplicados); la tabla de
  correspondencia está en `fullstack/docs/ESTRUCTURA_DOCUMENTAL.md`.
- Pendiente fuera del código: crear el Issue **BACK-35** en GitHub (no existe) y capturas del
  índice para la evidencia del profesor.
