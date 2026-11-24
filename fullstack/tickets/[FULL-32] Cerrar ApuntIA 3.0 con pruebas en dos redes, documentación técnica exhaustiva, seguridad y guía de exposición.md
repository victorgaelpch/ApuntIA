# [FULL-32] Cerrar ApuntIA 3.0 con pruebas en dos redes, documentación técnica exhaustiva, seguridad y guía de exposición

- Numero de Issue: #101
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/101
- Estado: open
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: fullStack
- Creacion GitHub: 2026-11-13 18:45:49 -0600 (CDMX)
- Cierre GitHub: No registrada / no aplica
- Actualizacion GitHub: 2026-11-13 18:45:49 -0600 (CDMX)
- Creacion UTC: 2026-11-14T00:45:49Z
- Cierre UTC: No aplica

- Fecha de captura: 2026-11-24 12:10:14 -0600 (CDMX)
- [Captura original](%5BFULL-32%5D%20Cerrar%20ApuntIA%203.0%20con%20pruebas%20en%20dos%20redes%2C%20documentaci%C3%B3n%20t%C3%A9cnica%20exhaustiva%2C%20seguridad%20y%20gu%C3%ADa%20de%20exposici%C3%B3n-original.png)
- [Captura con metadatos](%5BFULL-32%5D%20Cerrar%20ApuntIA%203.0%20con%20pruebas%20en%20dos%20redes%2C%20documentaci%C3%B3n%20t%C3%A9cnica%20exhaustiva%2C%20seguridad%20y%20gu%C3%ADa%20de%20exposici%C3%B3n.png)

## Descripcion original

## Objetivo — FULL-32
Demostrar con evidencia reproducible que el mismo repositorio funciona en dos modos separados: cliente ApuntIA instalable en la laptop del profesor y servidor IA ejecutándose en PC Windows de casa (Ryzen 7 5700X, 24 GB RAM, RTX 3060 12 GB), ambos en redes distintas; explicar algoritmos, decisiones y límites con suficiente detalle para que otra persona replique todo el sistema.

## Contexto real del repositorio
Ya hay `README.md`, `fullstack/scripts/validar.sh`, tests pytest/Playwright/CI, Docker Compose, contratos y documentación extensa; el objetivo es evolucionarlos, mover docs y demostrar instalación Windows REAL, actualmente pendiente de verificar.

## Dependencias
FULL-29/30/31, BACK-35/36/37/38, FRONT-25/26.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-12-09 · 17:30–21:00 (America/Mexico_City): Revisión integrada de contratos, CI y seguridad.
- [ ] 2026-12-10 · 18:00–21:30 (America/Mexico_City): Prueba de instalación real y comunicación entre dos redes.
- [ ] 2026-12-12 · 10:00–14:00 (America/Mexico_City): Pruebas de aceptación de fotos, PDFs y documentación para entrega.

## Tareas técnicas detalladas
#### A. Pruebas con matrices de aceptación
- [ ] Extender validador global de `fullstack/scripts/validar.sh` y su equivalente Windows (si no existe, crearlo) para separar pruebas rápidas (sin GPU), contratos falsos, integrales de cliente, servidor IA con GPU real y conexión de redes distintas.
- [ ] Añadir GitHub Actions sin descargar modelos de 6 GB ni usar credenciales reales: mocks de Ollama, simulación HTTP/errores, validaciones de seguridad, docs/linkcheck, scripts PowerShell, pytest, Playwright y Docker del cliente.
- [ ] Probar `iniciar.bat` en Windows físico con Python disponible, ruta con espacios/acento, usuario sin admin, puerto ocupado, segunda instancia, primer arranque y reinicio; conservar datos SQLite.
- [ ] Probar desde red diferente: laptop sin GPU → HTTPS con Cloudflare Tunnel → PC casa → respuesta JSON → editor → investigación consentida → PDF; registrar pasos y capturas reales sanitizadas.
- [ ] Probar primer emparejamiento, reconexión automática posterior, URL manual, cambio de servidor, credencial revocada, token caducado, túnel caído, PC suspendida, DNS/TLS, VRAM agotada, cola llena y caída de Internet.
- [ ] Probar PDF con las tres categorías de fotografía (agrupamiento, vectorial, circuitos), más imágenes sintéticas y 20 páginas; validar no inventar información, revisiones de contenido, citas y recuperación tras fallos.
- [ ] Probar Docker Compose existente, reconfiguración del cliente y persistencia del volumen, sin añadir Ollama obligatoriamente al cliente Docker.
- [ ] Ejecutar escaneo de secretos, dependencias vulnerables, CORS/CSRF, acceso cruzado (IDOR), SSRF, logs, exposición de puertos, rate limiting, tamaño archivos, tokens por cliente y licencias de modelos.
#### B. Documentación para el profesor
- [ ] Reescribir README raíz como índice de instalación de 2 perfiles (App cliente / Servidor IA), modo Windows con menú, requisitos concretos, espacio y memoria, Docker cliente, Linux si soportado, enlace a guías extendidas, comandos verificables y limitaciones reales.
- [ ] Crear/actualizar en `fullstack/docs/`: `README.md`, `arquitectura-apuntia-3.md`, `instalacion-cliente.md`, `instalacion-servidor-ia.md`, `conexion-remota.md`, `seguridad.md`, `contrato-api-ia.md`, `pipeline-ocr.md`, `algoritmos.md`, `modelos-y-requisitos.md`, `flujo-apunte-pdf.md`, `investigacion-y-citas.md`, `pruebas-y-metricas.md`, `errores-y-recuperacion.md`, `operacion-servidor.md`, `respaldo-y-restauracion.md`, `despliegue-docker.md`, `exposicion-paso-a-paso.md`, `referencias.md` (crear solo los necesarios, agrupar si simplifica).
- [ ] En cada algoritmo, explicar finalidad, entradas/salidas, fórmula/pseudocódigo si aplica, parámetros, complejidad aproximada, condiciones de uso, por qué se eligió sobre alternativas, limitaciones, ejemplo con imágenes reales anonimizadas y fuente técnica.
- [ ] Documentar explícitamente Canny, Otsu, umbral adaptativo, CLAHE, Laplaciano, homografía, Hough, filtrado, segmentación layout, OCR, VLM, reconocimiento matemático, verificación simbólica, asociación espacial de diagramas, deduplicación de crops, reconciliación y validación JSON.
- [ ] Describir elección y licencias de Qwen3-VL 8B, Ollama, PaddleOCR-VL 1.6 opcional (compatibilidad real), Tesseract fallback; RAM/VRAM medidas, pesos de modelos NO subidos a GitHub, instalación/reinstalación y limitaciones de la RTX 3060.
- [ ] Documentar seguridad de conexión: qué se publica (hostname), qué NO (Ollama y claves), primer emparejamiento, renovación/revocación, qué pasa si tu PC está apagada; diagramas de secuencia real con red distinta.
- [ ] En `front/docs/`, mantener documentación técnica de pantallas, UX, accesibilidad y mensajes; en `fullstack/tickets/`, actualizar índices, estado REAL, fechas/horas de trabajo efectivas y evidencia de PRs.
- [ ] Incorporar bibliografía verificable de documentación oficial, papers de modelos y algoritmos y licencias; distinguir implementado/propuesto/no verificado con fecha de revisión.
#### C. Entrega reproducible
- [ ] Crear «demostración de 10 minutos» con pasos exactos, datos de prueba y plan B si la red universitaria falla; incluir cómo mostrar status, GPU y modelo.
- [ ] Mantener un checklist de puesta en marcha en casa: encendido, evitar suspensión, Ollama, tunnel, modelo listo, firewall, energía/Internet, espacio y logs.
- [ ] Medir tiempo de OCR por página, tamaño archivos, VRAM máxima, tasa de error por tipo y tasa de fallos; reportar cifras REALES, no estimaciones como resultados.
- [ ] Preparar procedimiento de restauración de SQLite y datos, detención ordenada, limpieza sin borrar documentos, y reversión del despliegue (volver al modo clásico).

## Errores previsibles y recuperación manual
- CI falla por GPU inaccesible: usar mocks en CI y test manual de GPU con evidencia etiquetada, no saltar toda la suite.
- Sin Internet durante exposición: mostrar un apunte guardado, edición y PDF offline; anunciar límites reales del reconocimiento remoto.
- Instalación en Windows sin permisos: requerimientos claros y alternativas soportadas; no desactivar antivirus, seguridad ni políticas del equipo.
- Incompatibilidad API/modelos tras actualización: pin de versiones, comprobación de capacidades, rollback documentado.
- Documentación incorrecta o rutas rotas: CI bloquea hasta corregir.
- Resultado de imagen ilegible: no simular éxito; mostrar bloque incierto y PDF fiel con recorte.

## Pruebas y evidencia obligatoria
- Validación integral CI (pytest, Playwright, tests scripts, Docker, links, seguridad) y matriz manual firmada en dos Windows/redes.
- Evidencia: versión Git SHA, fecha/hora local real, sistema operativo, modelo exacto, VRAM, IDs de trabajos, tiempo, resultado y referencia a artefactos (sin secretos ni datos privados).
- Documentar todos los fallos encontrados y su corrección; los fallos no resueltos quedan explícitos como limitaciones conocidas y no se marca el Issue completo.

## Entregables
- README 3.0 y documentación técnica exhaustiva en `fullstack/docs/`, frontend en `front/docs/`, tickets en `fullstack/tickets/`.
- CI/matrices de pruebas y reporte de evaluación; guía de exposición, plan de contingencia y evidencia Windows/red real.
- PR final que enumere revisiones, cobertura funcional y errores conocidos.

## Criterios de aceptación (Definition of Done)
- [ ] Profesor puede instalar/apuntar desde laptop sin GPU utilizando scripts existentes, con autorización inicial controlada.
- [ ] Servidor IA en casa produce análisis de páginas reales desde otra red; config manual/fallback probado.
- [ ] El sistema produce PDF fiel con transcripción, fórmulas/tablas/diagramas conservados y citas verificadas si se autorizaron.
- [ ] Toda documentación y tickets están en las rutas pedidas, sin duplicación ni fecha de trabajo inventada.
- [ ] Pruebas automáticas y manuales documentadas, riesgos y limitaciones declaradas, rollback posible.

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

![Captura del Issue #101](%5BFULL-32%5D%20Cerrar%20ApuntIA%203.0%20con%20pruebas%20en%20dos%20redes%2C%20documentaci%C3%B3n%20t%C3%A9cnica%20exhaustiva%2C%20seguridad%20y%20gu%C3%ADa%20de%20exposici%C3%B3n.png)
