# Bitácora real — FULL-32 (#101)

- Sesión real: 2026-11-14 04:01–04:20 y 07:20–07:25 (America/Mexico_City; entre medias, pausa por límite
  de uso: no se trabajó), tras el commit de BACK-38; los arreglos de
  Windows se encontraron antes, al correr la batería completa durante BACK-38 (~03:40). Responsable:
  Claude Code (asistente de IA) con autorización del dueño del proyecto; **falta revisión humana**.
  Actividad: batería completa en Windows; respaldo corregido para Windows (conexiones SQLite y rutas);
  pruebas portables; aviso de idiomas de Tesseract en `/api/v2/listo`; `validar.ps1` con niveles
  rápido/completo/GPU/remoto; CI con backend en Windows y `pip-audit` del servidor IA; revisión de
  seguridad (secretos, dependencias, puertos, registros, licencia del modelo); README con dos perfiles
  y guías algoritmos, modelos-y-requisitos, exposición, pruebas-y-métricas y referencias.
  Evidencia: rama `feature/FULL-32-cierre`; backend 471 OK + 6 de OCR que necesitan `spa` (también
  fallan en la base); servidor IA 129 OK; `validar.ps1 -Gpu`: 11/11 casos con CER 0, 2,3–7,0 s, pico
  9 971 MB; `validar.ps1 -Remoto http://127.0.0.1:8100`: 200 en 72 ms; pip-audit y npm audit sin
  vulnerabilidades; secretos limpios (513 rutas). **Pendiente** (no se marca el Issue como hecho): prueba
  entre dos redes con el túnel real, laptop real del profesor y más fotos reales con permiso
  (`fullstack/docs/pruebas-y-metricas.md` §3).
