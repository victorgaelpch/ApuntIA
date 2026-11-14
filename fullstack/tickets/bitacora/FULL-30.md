# Bitácora real — FULL-30 (#94)

- Sesión real: 2026-11-13 21:55–22:08 (America/Mexico_City). Responsable: Claude Code (asistente de
  IA) a petición del equipo, en la PC servidor (Windows 11 Pro 10.0.26200, RTX 3060 12 GB);
  **falta revisión humana y la prueba en la laptop sin GPU**. Actividad: menú de `iniciar.bat`,
  `-Modo`, `ia.ps1` (instalar/iniciar/detener/diagnosticar/configurar), módulo común, `detener`
  del servidor IA, pruebas PowerShell, job de CI en Windows y guías de instalación.
  Evidencia: rama `feature/FULL-30-instalador-menu`; ejecuciones reales en esta PC:
  `iniciar.bat -Comprobar` → 0 (clásico intacto); `-Modo diagnostico` → 0; `-Modo instalar-ia`
  → 5 (falta Ollama), 37 s y luego 1 s sin reinstalar; `-Modo servidor-ia` → 0 «no listo» con
  causa; doble inicio sin duplicar; `detener.bat` detuvo solo su PID; `-Modo configurar` rechazó
  URLs inseguras; `windows.pruebas.ps1` → 38 OK.
  Pendiente: instalar Ollama + `qwen3-vl:8b` (requiere confirmación del dueño), probar en la laptop.
