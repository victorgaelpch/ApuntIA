# [BACK-36] Implementar el pipeline multimodelo de máximo reconocimiento para cuadernos, pizarrones, fórmulas, tablas, diagramas y dibujos

- Numero de Issue: #96
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/96
- Estado: open
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: fullStack
- Creacion GitHub: 2026-11-13 18:40:15 -0600 (CDMX)
- Cierre GitHub: No registrada / no aplica
- Actualizacion GitHub: 2026-11-13 18:40:15 -0600 (CDMX)
- Creacion UTC: 2026-11-14T00:40:15Z
- Cierre UTC: No aplica

- Fecha de captura: 2026-11-24 12:09:48 -0600 (CDMX)
- [Captura original](%5BBACK-36%5D%20Implementar%20el%20pipeline%20multimodelo%20de%20m%C3%A1ximo%20reconocimiento%20para%20cuadernos%2C%20pizarrones%2C%20f%C3%B3rmulas%2C%20tablas%2C%20diagramas%20y%20dibujos-original.png)
- [Captura con metadatos](%5BBACK-36%5D%20Implementar%20el%20pipeline%20multimodelo%20de%20m%C3%A1ximo%20reconocimiento%20para%20cuadernos%2C%20pizarrones%2C%20f%C3%B3rmulas%2C%20tablas%2C%20diagramas%20y%20dibujos.png)

## Descripcion original

## Objetivo — BACK-36
Sustituir la dependencia de Tesseract como único reconocedor con un pipeline escalonado, reversible y evaluable en la RTX 3060 de 12 GB; extraer el máximo contenido fiel posible de fotografías reales difíciles (como los apuntes de agrupamiento, cálculo vectorial y circuitos), incluyendo texto manuscrito, tablas, expresiones matemáticas, flechas, dibujos y relaciones entre componentes. Marcar incertidumbres y conservar recortes originales.

## Contexto real del repositorio
El backend ya usa OpenCV (perspectiva, Otsu, Canny, mejora, OCR) y el editor acepta bloques, fórmulas y recortes. `BACK-28` contempla reconocimiento adaptativo. Ampliar esa lógica, no reemplazar el contrato ni romper evaluaciones anteriores.

## Dependencias
BACK-35; usar la base de evaluación existente (BACK-28, `fullstack/evaluacion/`).

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-11-24 · 18:00–21:00 (America/Mexico_City): Definición de corpus, preprocesamiento, ROI y contratos de bloque.
- [ ] 2026-11-27 · 18:00–22:00 (America/Mexico_City): Pipeline híbrido, OCR/VLM y validación de fórmulas/diagramas.
- [ ] 2026-11-30 · 18:00–21:00 (America/Mexico_City): Benchmark, comparación de motores y corrección de regresiones.

## Tareas técnicas detalladas
#### A. Corpus y criterios objetivos (antes de cambiar el modelo)
- [ ] Crear 3 casos reales CON permiso y anonimizados (agrupamiento/Nmap/tabla, Cálculo III con vectores y derivadas, circuitos con mallas); añadir fotos difíciles adicionales con baja luz, sombras, tachones, cuadrícula y escritura muy pequeña. No subir fotografías privadas al repo público; usar corpus sintético o fixtures con derechos/autorización.
- [ ] Crear verdad-terreno revisada manualmente por región y por tipo: transcripción literal, orden de lectura, coordenadas normalizadas, fórmula LaTeX, celdas de tabla, aristas/nodos de diagramas, dibujos preservados; separar puntuación de lectura y corrección matemática.
- [ ] Medir línea base actual Tesseract/BACK-28: CER y WER en texto; exactitud de fórmulas o edición matemática (por estructura); celdas/filas/columnas; relaciones de diagramas; bloques omitidos/añadidos; porcentaje marcado correctamente como incierto, tiempo/página y VRAM pico.
#### B. Análisis visual no destructivo
- [ ] Utilizar copia de imagen original y probar calidad: desenfoque (varianza Laplaciana), brillo/contraste/histograma, sombras, resolución, ángulo y orientación; registrar qué ajustes ayudan sin alterar el original.
- [ ] Evaluar corrección de perspectiva existente con contornos Canny/Otsu + homografía; deskew; CLAHE, normalización de iluminación, balance y denoise bilateral/NLMeans solo cuando la calidad lo requiera; evitar binarizar permanentemente dibujos, colores y símbolos delicados.
- [ ] Generar múltiples vistas controladas: original a color, corregida, grises, contraste y recortes de alta resolución; recortes solapados para letra pequeña preservando coordenadas/página y orden; límites para evitar multiplicación de GPU.
- [ ] Detectar layout y orden lógico: títulos, párrafos, listas, columnas, fórmulas en línea/bloque, tablas, figuras, leyendas, flechas, conectores, cajas, gráficas y circuitos. Evaluar PaddleOCR-VL 1.6/PP-StructureV3 como motor de layout, sujeto a compatibilidad Windows o ejecución en WSL2 y consumo real. No imponer un framework pesado que no corra en la PC.
#### C. Reconocimiento y enrutamiento por región
- [ ] Motor principal Qwen3-VL 8B (cuantizado en Ollama); prompts por región para transcribir fielmente, sin completar palabras ilegibles por contexto; exportar JSON con coordenadas, clase de bloque, texto original, LaTeX, notas de incertidumbre y `source='imagen'`.
- [ ] Segundo motor evaluable PaddleOCR-VL o PP-StructureV3 para parsing/tabla/fórmula; usarlo únicamente si supera la línea base o corrige errores; cargar modelos secuencialmente dentro de 12 GB VRAM.
- [ ] Mantener Tesseract para texto impreso y como fallback; decidir motor por evaluación, no por «confianza» autodeclarada de LLM. En caso de discrepancia entre motores, conservar ambas hipótesis y pedir revisión.
- [ ] Reconocer matemáticas con expresiones LaTeX (fracciones apiladas, raíces, super/subíndices, integrales, matrices, vectores, límites, trigonometría), preservar el crop y probar renderizado (KaTeX/MathJax o motor actual); validar sintaxis LaTeX y, cuando aplicable, equivalencia con SymPy; no «corregir» automáticamente la ecuación escrita en la imagen.
- [ ] Tablas: reconstruir filas, columnas, celdas combinadas, encabezados y relaciones; conservar incertidumbre por celda y referencias a su región original. Validar contra cuadrículas del cuaderno para no confundirlas con bordes de tabla.
- [ ] Diagramas y dibujos: detectar primitivas con OpenCV (líneas con Hough, contornos, flechas, símbolos) y semántica con VLM; producir representación estructurada para esquemas, circuitos (nodos, componentes, polaridades, conexiones), gráficas de vectores (ejes, curvas) y diagramas de agrupamiento. Nunca inventar conectividad o valores: conservar fotografía/recorte ante ambigüedad.
- [ ] Respetar colores, marcas/leyendas relevantes y orden de lectura; combinar múltiples páginas con referencias a página y bbox.
#### D. Fusión y fidelidad
- [ ] Diseñar reconciliador: orden de lectura, deduplicación de recortes superpuestos, procedencia por motor, estados `verificado`, `dudoso`, `ilegible`, alternativos y versión del pipeline; confidence model calibrated con datos, no porcentajes arbitrarios de un LLM.
- [ ] Nunca reemplazar `texto_original` de usuario ya corregido; preservar IDs `p{n}b{m}`, `bbox`, enlaces a recortes y compatibilidad del editor.
- [ ] Introducir presupuesto de GPU, imágenes/página y tiempos; ejecutar 1 inferencia pesada a la vez, 4B/recortes pequeños cuando hay OOM; medir desempeño en RTX 3060 real.
- [ ] Evaluar cada tipo de contenido por separado, comparar 8B vs 4B y segundo OCR, e incluir tabla de regresiones; no prometer 100 %.

## Errores previsibles y recuperación manual
- Texto irreconocible: bloque `ilegible` con recorte y opción de escribir manualmente; no inventar transcripción.
- Fórmula ambigua o LaTeX inválido: mostrar crop e hipótesis; usar imagen original en PDF si no se corrige.
- Diagrama con conexiones dudosas: mantener fotografía o esquema parcial sin asumir topología.
- GPU OOM/timeout: pasar a recortes menores, modelo 4B o motor local donde aplique; estado `parcial` con causa.
- Múltiples modelos en desacuerdo: registrar discrepancia y pedir confirmación humana.
- Falta PaddleOCR-VL en Windows: documentar instalación compatible en WSL2 o desactivar solo ese componente, sin romper Qwen/Tesseract.

## Pruebas y evidencia obligatoria
- Corpus reproducible con métricas por tipo y comparación con línea base; umbrales acordados que impidan regresión silenciosa en impreso/v1 y fórmulas.
- Test de coordenadas/crops, detección de cuadrícula, tablas, fracción vs división, signo ±, índices, flechas y esquemas con valores falsos; validar LaTeX renderizable.
- Test del mismo documento con modelo caído, segunda lectura y fallback. Capturar tiempos y VRAM reales sin inflar métricas.

## Entregables
- Pipeline modular con estrategias y adaptadores, prompts versionados, schemas JSON, fixtures/suite de evaluación, informe comparativo de exactitud/VRAM/rendimiento.
- `fullstack/docs/algoritmos-procesamiento.md`, `modelos-ia.md`, `evaluacion-multimodal.md`: algoritmos, ecuaciones, por qué se usan, parámetros, fuentes oficiales y limitaciones.

## Criterios de aceptación (Definition of Done)
- [ ] Tres categorías (manuscrito, matemática, diagrama) se procesan de extremo a extremo con bloques vinculados a la imagen.
- [ ] Tablas y fórmulas complejas se reconocen o quedan señaladas sin alucinaciones.
- [ ] Métricas y casos negativos quedan documentados; no hay regresión no explicada de OCR impreso.
- [ ] Procesamiento se mantiene dentro de recursos y alternativas probadas en RTX 3060 de 12 GB.

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

![Captura del Issue #96](%5BBACK-36%5D%20Implementar%20el%20pipeline%20multimodelo%20de%20m%C3%A1ximo%20reconocimiento%20para%20cuadernos%2C%20pizarrones%2C%20f%C3%B3rmulas%2C%20tablas%2C%20diagramas%20y%20dibujos.png)
