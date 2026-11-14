# Bitácora real — FULL-31 (#95)

- Sesión real: 2026-11-13 23:48 – 2026-11-14 00:08 (America/Mexico_City). Responsable: Claude Code
  (asistente de IA) a petición del equipo, en la PC servidor; **falta revisión humana y la prueba
  entre dos redes reales**. Actividad: vinculación y autorización en `ia_servidor` (registro con
  hashes, consola de administración, límites), cliente remoto del backend (DPAPI, vínculo al
  origen, sin redirecciones, reintentos, circuit breaker), rutas `/api/v2/ia`, consola de
  vinculación, integración en el menú y guías. Evidencia: rama `feature/FULL-31-conexion-segura`;
  pytest servidor IA 88 OK, cliente 41 OK, backend completo sin regresiones (mismos 10 fallos del
  entorno que `origin/main`); prueba real en esta PC con `qwen3-vl:8b-instruct`: vinculación
  aprobada en vivo (2,8 s), retomar solicitud, diagnóstico 5/5, análisis de fórmulas, revocación
  y cambio de URL sin filtrar la credencial (`fullstack/docs/conexion-remota.md`).
  Inicio = creación de `ia_servidor/dispositivos.py` (primer archivo de FULL-31); el análisis previo
  de unos minutos no tiene marca de tiempo verificable.
