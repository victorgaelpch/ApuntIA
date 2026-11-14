# Bitácora real — BACK-36 (#96)

- Sesión real: 2026-11-14 00:08–00:10 (America/Mexico_City). Responsable: Claude Code (asistente de
  IA) a petición del equipo; **falta revisión humana**. Actividad: banco de evaluación con corpus
  privado de fotos reales (`python -m ia_servidor.medir --corpus …`, permiso obligatorio por foto,
  carpeta ignorada por Git), métricas de fórmulas (LaTeX normalizado y notación equivalente) y guía
  `fullstack/docs/evaluacion-multimodal.md` con las decisiones pendientes. Evidencia: rama
  `feature/BACK-36-pipeline`; pytest del servidor IA 95 OK.
  **Bloqueado**: faltan las fotos reales con permiso; sin ellas no se elige la segmentación por regiones.
  Inicio = hora del commit de FULL-31 (93cc2b2), cuando empezó esta parte.
