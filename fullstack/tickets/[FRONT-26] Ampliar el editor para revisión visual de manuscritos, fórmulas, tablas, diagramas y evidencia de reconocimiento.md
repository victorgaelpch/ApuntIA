# [FRONT-26] Ampliar el editor para revisión visual de manuscritos, fórmulas, tablas, diagramas y evidencia de reconocimiento

- Numero de Issue: #99
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/99
- Estado: open
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-13 18:43:28 -0600 (CDMX)
- Cierre GitHub: No registrada / no aplica
- Actualizacion GitHub: 2026-11-13 18:43:28 -0600 (CDMX)
- Creacion UTC: 2026-11-14T00:43:28Z
- Cierre UTC: No aplica

- Fecha de captura: 2026-11-24 12:10:02 -0600 (CDMX)
- [Captura original](%5BFRONT-26%5D%20Ampliar%20el%20editor%20para%20revisi%C3%B3n%20visual%20de%20manuscritos%2C%20f%C3%B3rmulas%2C%20tablas%2C%20diagramas%20y%20evidencia%20de%20reconocimiento-original.png)
- [Captura con metadatos](%5BFRONT-26%5D%20Ampliar%20el%20editor%20para%20revisi%C3%B3n%20visual%20de%20manuscritos%2C%20f%C3%B3rmulas%2C%20tablas%2C%20diagramas%20y%20evidencia%20de%20reconocimiento.png)

## Descripcion original


## Objetivo — FRONT-26
Evitar que el usuario acepte reconocimientos equivocados: cada bloque debe enlazarse con su región original y su nivel de incertidumbre; permitir corregir texto y LaTeX, reconstruir tablas y conservar/explicar diagramas antes de generar un PDF fiel.

## Contexto real del repositorio
El editor ya ofrece corrección de texto, vista previa de LaTeX, tablas, esquemas, versiones y recortes. Extender sus controles de revisión sin reemplazarlos.

## Dependencias
BACK-36 para contrato de bloques; FRONT-25 para mensajes.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-12-03 · 18:00–20:30 (America/Mexico_City): Revisión del editor y prototipos de anotación por región.
- [ ] 2026-12-04 · 18:00–21:00 (America/Mexico_City): Implementar revisión, comparación y edición estructurada.
- [ ] 2026-12-05 · 10:00–12:30 (America/Mexico_City): Pruebas E2E y documentación de UI.

## Tareas técnicas detalladas
- [ ] Consumir bloques versionados del servidor con `pagina`, `bbox`, `texto_original`, alternativas, `origen_modelo`, `estado_revision`, `latex`, celdas y diagramas; adaptarse a bloques antiguos donde no existan campos nuevos.
- [ ] Mostrar foto y región seleccionada resaltada con zoom, contraste ajustable solo para vista, opción de ver original/recorte y orden por páginas.
- [ ] Distinguir claramente «extraído de la foto», «corregido por usuario» e «información añadida por investigación»; evitar que lo añadido reemplace transcripción original.
- [ ] Resaltar regiones dudosas: confusiones entre símbolos (6/8, +/−, i/j/k, exponente), fórmulas no renderizables y conectividad dudosa de diagramas; permitir marcar revisado/pendiente.
- [ ] Editor LaTeX con previsualización, validación y alternativa «conservar recorte»; al modificar fórmula conservar original, historial y posibilidad de revertir.
- [ ] Vista de tabla con editar celdas, fusionar/separar, detectar cuadrícula de cuaderno confundida, y exportación estructurada; sin HTML no confiable.
- [ ] Vista de diagramas/esquemas: mostrar descripción/relaciones identificadas, edición de etiquetas, confirmación de conexión y opción de conservar dibujo original cuando no sea reconstruible.
- [ ] Reconciliar correctamente bloques de páginas múltiples, id único, duplicados por recorte, guardado con `If-Match`, conflictos de versión y sesión expirada.
- [ ] En PDF, permitir elegir incluir imágenes originales o recortes de baja confianza; advertir de datos sin verificar, sin impedir generar el apunte parcial.
- [ ] Documentar `front/docs/EDITOR_MULTIMODAL.md` (estados, componentes, accesibilidad y flujo de corrección) y tests.

## Errores previsibles y recuperación manual
- LaTeX inválido: no romper la página/PDF; mostrar texto plano o imagen original.
- Sin bbox o sin confianza: modo compatibilidad con bloque antiguo y revisión manual.
- Guardado concurrente: resolver conflicto sin borrar la edición actual.
- Tabla incompleta o diagrama ambiguo: conservar imagen/fuente y permitir notas manuales.
- Pérdida de red durante edición: cambios locales temporales protegidos, aviso de sincronización y no marcar como guardado hasta confirmación.

## Pruebas y evidencia obligatoria
- Playwright con 3 páginas y regiones, selección de bbox, revisión de fórmula compleja, tabla con celdas, imagen/diagrama, guardado/reapertura, conflictos de versión y PDF.
- Comprobar sanitización contra XSS en texto/Markdown/LaTeX provisto por modelo o fotografía.
- Pruebas en móvil y teclado sin bloquear acciones anteriores.

## Entregables
- Editor ampliado sin regresión, pruebas E2E y `front/docs/EDITOR_MULTIMODAL.md` con capturas.
- Evidencia de que una corrección de una fórmula aparece igual en PDF e historial.

## Criterios de aceptación (Definition of Done)
- [ ] Todo bloque incierto es rastreable a la imagen de origen y editable.
- [ ] Fórmulas, tablas y diagramas pueden corregirse o conservarse como imagen.
- [ ] La versión editada es la que llega al PDF.
- [ ] Soporta datos antiguos y no pierde correcciones anteriores.

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

![Captura del Issue #99](%5BFRONT-26%5D%20Ampliar%20el%20editor%20para%20revisi%C3%B3n%20visual%20de%20manuscritos%2C%20f%C3%B3rmulas%2C%20tablas%2C%20diagramas%20y%20evidencia%20de%20reconocimiento.png)
