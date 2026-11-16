# Bitácora real — BACK-35 (sin Issue en GitHub todavía)

- Sesión real: 2026-11-13 21:46–21:55 (America/Mexico_City). Responsable: Claude Code (asistente
  de IA) a petición del equipo, en la PC servidor (Windows 11, RTX 3060 12 GB); **falta revisión
  humana**. Actividad: servicio `ia_servidor/` (FastAPI + adaptador Ollama, contrato v1, errores,
  límites, cola de 1 inferencia, respaldo 4B ante OOM, OpenCV compartido con el backend) y
  `fullstack/docs/servidor-ia.md`. Evidencia: rama `feature/BACK-35-servidor-ia`;
  `python -m pytest ia_servidor/tests` → 40 pruebas OK (Ollama simulado); arranque real con
  `python -m ia_servidor`: `/salud` 200, `/listo` 503 (Ollama no instalado, GPU detectada),
  análisis 503 `NO_DISPONIBLE`, `IA_HOST=0.0.0.0` rechazado con salida 2.
  Pendiente: inferencia real con `qwen3-vl:8b` (requiere instalar Ollama y descargar 6,2 GB).
- Sesión real: 2026-11-13 22:20–23:01 (America/Mexico_City). Responsable: Claude Code a petición del
  dueño del equipo, que autorizó instalar Ollama y `qwen3-vl:8b`. Actividad: instalación con
  `winget` (Ollama 0.40.16, hash verificado) y `ia.ps1 -Accion instalar -AceptarDescarga`
  (593 s); medición real con `python -m ia_servidor.medir`; diagnóstico de la variante «thinking»
  (ignora `think:false`, agota el contexto en fórmulas); `IA_NUM_CTX`/`IA_MAX_TOKENS`.
  Evidencia: `fullstack/docs/servidor-ia.md` §8; pytest 40 OK.
- Sesión real: 2026-11-13 23:00–23:35 (America/Mexico_City). Responsable: Claude Code a petición del
  dueño del equipo, que autorizó descargar las variantes instruct. Actividad: pipeline 1.1 (prompt
  corto por tarea, texto plano, el servidor construye el resultado), modelos por defecto
  `qwen3-vl:8b-instruct` y `4b-instruct`, métricas de fórmulas (LaTeX normalizado y notación
  equivalente) y comparación real de 3 modelos. Evidencia: `fullstack/docs/servidor-ia.md` §8.2;
  8b-instruct 11/11 en 3–6 s; pytest 59 OK; pruebas PowerShell 38 OK.
