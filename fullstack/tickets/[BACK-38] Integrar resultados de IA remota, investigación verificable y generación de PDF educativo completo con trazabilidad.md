# [BACK-38] Integrar resultados de IA remota, investigación verificable y generación de PDF educativo completo con trazabilidad

- Numero de Issue: #100
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/100
- Estado: open
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-13 18:44:35 -0600 (CDMX)
- Cierre GitHub: No registrada / no aplica
- Actualizacion GitHub: 2026-11-13 18:44:35 -0600 (CDMX)
- Creacion UTC: 2026-11-14T00:44:35Z
- Cierre UTC: No aplica

- Fecha de captura: 2026-11-24 12:10:07 -0600 (CDMX)
- [Captura original](%5BBACK-38%5D%20Integrar%20resultados%20de%20IA%20remota%2C%20investigaci%C3%B3n%20verificable%20y%20generaci%C3%B3n%20de%20PDF%20educativo%20completo%20con%20trazabilidad-original.png)
- [Captura con metadatos](%5BBACK-38%5D%20Integrar%20resultados%20de%20IA%20remota%2C%20investigaci%C3%B3n%20verificable%20y%20generaci%C3%B3n%20de%20PDF%20educativo%20completo%20con%20trazabilidad.png)

## Descripcion original

## Objetivo — BACK-38
Conectar el análisis remoto con el sistema existente de apuntes/versiones/PDF; producir material educativo legible y rico (portada, índice, explicaciones, fórmulas, tablas, diagramas, figuras y bibliografía) manteniendo fiel la fuente fotografiada y diferenciando estrictamente la investigación agregada.

## Contexto real del repositorio
Ya existen guardado/versiones, editor, enriquecimiento opcional con Wikipedia y generación ReportLab. No crear una segunda base de datos, editor o exportador; ampliar sus entradas, estilos y verificaciones.

## Dependencias
BACK-36 + BACK-37 + FRONT-26; reutilizar flujos actuales de investigación/PDF.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-12-04 · 19:00–21:00 (America/Mexico_City): Auditar investigación Wikipedia y PDF actuales, esquema de evidencia.
- [ ] 2026-12-07 · 18:00–21:00 (America/Mexico_City): Integración de bloque multimodal, enriquecimiento y PDF.
- [ ] 2026-12-08 · 18:00–21:00 (America/Mexico_City): Pruebas de citas, fórmulas, esquemas y regresión.

## Tareas técnicas detalladas
#### A. Integración fiel
- [ ] Inspeccionar contratos de `/apuntes`, `/trabajos`, versiones y exportaciones; mapear bloques remotos a entidad existente sin romper IDs, propietario, `If-Match`, texto original y ediciones del usuario.
- [ ] Guardar metadatos de procedencia (página, región, motor, revisión, fecha, versión) sin enviar credenciales ni datos personales al servidor IA.
- [ ] Mantener imágenes/recortes para regiones incompletas, tablas, gráficas y circuitos, no reemplazarlas por texto inferido sin validación.
#### B. Enriquecimiento con fuentes reales
- [ ] Auditar integración actual con Wikipedia y conservar la condición «opt-in» explícita; extender de manera modular a fuentes verificables apropiadas (universidades, libros abiertos, documentación oficial, artículos con DOI), respetando licencias y robots/ToS.
- [ ] Habilitar búsqueda y recuperación CONTROLADA de contenidos: sanitizar consulta y URLs, evitar SSRF/redirecciones a IPs internas, validar HTTP/respuesta, dominio y fecha, límites de longitud y timeout. No permitir URLs arbitrarias aportadas por el modelo.
- [ ] Construir plan de temas a ampliar a partir de bloques confirmados; recuperar textos de fuentes, sintetizar SOLO lo respaldado, registrar título, autor/organización, URL, fecha de consulta y fragmento que respalda afirmación.
- [ ] Diferenciar `transcripcion_original`, `explicacion_verificada`, `ejemplo_generado`, `observacion` y `no_confirmado`; etiquetar y exigir aceptación por usuario antes de incorporar complementos.
- [ ] No crear citas ficticias, DOI falsos ni afirmar información sin fuente; cuando no hay Internet o fuentes adecuadas, producir PDF con el contenido original y aviso claro.
#### C. PDF académico
- [ ] Utilizar la generación existente y enriquecer estilos: portada, tema, fecha, índice, jerarquía de encabezados, bloques de fórmulas (LaTeX renderizado o imagen segura), tablas con saltos correctos, esquemas/crops preservados, numeración de páginas, bibliografía, anexos y enlace a fotografías originales según elección del usuario.
- [ ] Validar que los signos matemáticos no cambien respecto de la edición confirmada; cuando no pueda renderizarse una fórmula, mostrar su imagen o LaTeX literal y un aviso, no inventar expresión alternativa.
- [ ] Hacer diagramas reconstruidos solo si la topología fue validada; si no, conservar recorte original y explicación delimitada.
- [ ] Proteger el generador contra HTML/Markdown/LaTeX malicioso, desbordes, consumo excesivo y fuentes externas no confiables.
- [ ] Generar desde versión almacenada exacta y opciones de exportación; exportación idempotente; verificar acceso del propietario a PDF y documentos.
- [ ] Mantener salida usable sin conexión de investigación o servidor IA si el usuario ya tiene un apunte guardado.

## Errores previsibles y recuperación manual
- Fuente 404/429/sitio fuera de línea: omitir fuente y avisar, sin citarla.
- Resumen no respaldado: marcar `no_confirmado` y excluir automáticamente de «verificado».
- Fallo de render PDF/LaTeX/imagen: fallback de recorte y conservar apunte/versiones.
- Imagen muy pesada o recurso externo: límites y limpieza; PDF parcial con evidencia si procede.
- Trato de contenido sensible/personal en apuntes: no enviar búsquedas con datos privados de usuario a Internet sin consentimiento claro.

## Pruebas y evidencia obligatoria
- Pruebas offline con fuentes simuladas y online opcional; citar fuente existente, rechazar cita inventada, 404, 429, timeouts, contenido engañoso y SSRF.
- Generación PDF con vectores, fórmulas, tablas anchas, circuito original, 20 páginas, índice/bibliografía; validar apertura y extracción de texto; revisar visualmente al menos 3 PDFs de referencia.
- Verificar que el resultado respeta los cambios del editor y el propietario; historial y versiones regresión.

## Entregables
- Integración remota→apuntes→investigación→PDF, contratos de procedencia/citas, suite de pruebas, ejemplos de PDF sintéticos.
- `fullstack/docs/investigacion-verificada.md`, `generacion-pdf.md`, `trazabilidad-contenido.md` con flujos, parámetros, fuentes y casos de error.

## Criterios de aceptación (Definition of Done)
- [ ] Las tres fotos de referencia producen un PDF con todo lo recuperable o imágenes señaladas para revisión.
- [ ] Ninguna cita se incorpora sin fuente verificable; enriquecimiento es opcional y trazable.
- [ ] Tabla, fórmula y diagrama conservan fidelidad; PDFs legibles y sin errores de exportación silenciosos.
- [ ] PDF/historial funcionan incluso si la investigación o IA remota no está disponible.

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

![Captura del Issue #100](%5BBACK-38%5D%20Integrar%20resultados%20de%20IA%20remota%2C%20investigaci%C3%B3n%20verificable%20y%20generaci%C3%B3n%20de%20PDF%20educativo%20completo%20con%20trazabilidad.png)
