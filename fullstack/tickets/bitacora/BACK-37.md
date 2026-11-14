# Bitácora real — BACK-37 (#97)

- Sesión real: 2026-11-14 hasta 02:40 (America/Mexico_City). Responsable: Claude Code (asistente de IA)
  con autorización del dueño del proyecto; **falta revisión humana**. Actividad: cola asíncrona del
  servidor IA, cliente con retomar/cancelar/backoff, motor en el trabajo «analisis», clave idempotente
  y tabla `ia_resultados` (migración 0005), re-análisis protegido, códigos AI_* en API e interfaz.
  Evidencia: rama `feature/BACK-37-trabajos-remotos`; pytest servidor IA 129 OK; backend 18 nuevas
  OK; catálogo de la interfaz 9/9 (Node 26); prueba real en la PC con el backend matado a mitad del
  análisis: 1 trabajo en la GPU, 17 bloques, 6/6 trampas fieles (`fullstack/docs/trabajos-remotos.md`).
