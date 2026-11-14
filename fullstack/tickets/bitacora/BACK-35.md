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
