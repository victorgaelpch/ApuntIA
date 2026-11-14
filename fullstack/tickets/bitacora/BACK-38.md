# Bitácora real — BACK-38 (#100)

- Sesión real: 2026-11-14 03:02–04:01 (America/Mexico_City): del commit de FRONT-26 (03:02) al de
  BACK-38 `f1beac4` (04:01). Responsable: Claude Code (asistente de IA) con autorización del dueño del proyecto; **falta
  revisión humana**. Actividad: auditoría de investigación (Wikipedia opt-in) y PDF; etiquetas y recortes
  de propuestas de IA en el PDF; división de regiones multilínea; derivados y conceptos solo de lo
  confirmado; Wikilibros como fuente y bloqueo de redirecciones; tres guías y PDFs sintéticos.
  Evidencia: rama `feature/BACK-38-ia-pdf`; pytest backend 471 OK (6 fallos de calidad OCR que también
  fallan en el commit base por faltar `spa.traineddata` en el Tesseract local); servidor IA 129 OK;
  integración v2 98/105 (los 7 fallos ocurren igual en la base; FULL-32 corrige 5 de los 8 casos —texto
  UTF-8 de pdftotext y borrado con reintentos— y los 3 restantes dependen del OCR en español); prueba real con la foto
  del pizarrón → servidor IA → PDF de 10 páginas (35 bloques, 23 de regiones divididas), revisada
  visualmente junto con dos PDFs sintéticos (`fullstack/docs/generacion-pdf.md` §7); comprobación en
  línea de Wikipedia y Wikilibros con el término genérico «Derivada».
