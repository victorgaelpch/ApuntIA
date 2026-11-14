# Algoritmos de ApuntIA 3.0 (FULL-32)

Catálogo de **lo que el código usa de verdad** (auditado el 14/11/2026 buscando cada función de
OpenCV en `back/motori_magenes/app/services/` e `ia_servidor/`), con su finalidad, parámetros reales,
coste, por qué se eligió y sus límites. Las explicaciones largas y las mediciones de cada etapa están
en [PROCESAMIENTO.md](../../back/motori_magenes/PROCESAMIENTO.md); las fuentes, en
[referencias.md](referencias.md). *n* = número de píxeles de la imagen.

Estado: **implementado** (en el código y con pruebas), **no implementado** (se explica por qué).

## 1. Preparación de la foto (backend, modo local y vista previa)

| Algoritmo | Dónde | Finalidad | Parámetros reales | Coste | Por qué / alternativas | Límites |
|-----------|-------|-----------|-------------------|-------|------------------------|---------|
| **Desenfoque gaussiano** | `perspectiva.py`, `mejora.py`, `ruido.py` | quitar ruido fino antes de bordes y estimar el fondo | núcleo 5×5 (bordes), 3×3 (ruido), σ = k/2 (fondo a ¼ de resolución) | O(*n*·k) | barato y separable; suaviza también los bordes, por eso no se usa sobre la tinta final | borra trazos muy finos si el núcleo crece |
| **Canny** | `perspectiva.py` | encontrar el borde del pizarrón o de la hoja | umbrales 50/150 tras gaussiano 5×5, bordes dilatados 2 veces | O(*n*) | detector clásico con supresión de no máximos e histéresis; robusto al ruido del sensor | falla si el marco no contrasta con la pared o la hoja no tiene borde visible |
| **Otsu** | `perspectiva.py`, `adaptativo.py`, `manuscrito.py`, `ia_servidor/segmentacion.py` | umbral global automático (papel claro / fondo oscuro; tinta / fondo) | sin parámetros: maximiza la varianza entre clases del histograma | O(*n* + 256) | no hay que ajustar un umbral a mano | supone histograma bimodal; con sombras fuertes se usa el adaptativo |
| **Contornos + Douglas–Peucker** | `perspectiva.py` | elegir el cuadrilátero más grande (8 contornos mayores, ε proporcional al perímetro) | `findContours(RETR_LIST)`, `approxPolyDP` | O(*n*) + O(*m* log *m*) por contorno | 4 vértices dan la transformación exacta | si no hay 4 esquinas, no se endereza (se conserva la foto) |
| **Homografía de 4 puntos** | `perspectiva.py` | enderezar la hoja o el pizarrón | `getPerspectiveTransform` + `warpPerspective` con interpolación cúbica; tamaño de salida = longitud media de los lados | O(*n*) | con 4 correspondencias exactas no hace falta `findHomography`/RANSAC | si las esquinas están mal detectadas, la imagen se deforma; se valida el área |
| **Umbral adaptativo** | `calidad.py`, `preprocesado_ocr.py`, `manuscrito.py` | separar la tinta con iluminación desigual | media local, ventana 25–31 px, C = 10–15; gaussiano (31, 15) en manuscrito | O(*n*) con imagen integral | el pizarrón y las fotos con flash tienen luz no uniforme | ventanas pequeñas rompen letras grandes; por eso se escala la imagen antes |
| **CLAHE** | `mejora.py`, `adaptativo.py` | subir el contraste local sin quemar zonas claras | `clipLimit` 2,0, rejilla 8×8 (canal L de Lab en `mejora.py`) | O(*n*) | evita la sobreamplificación del ecualizado global | amplifica el ruido en zonas planas (limitado por el clip) |
| **Varianza del laplaciano** | `calidad.py`, `preprocesado_ocr.py` | medir nitidez (foto movida) | imagen reducida a 1000 px; borrosa < 40, muy borrosa < 12 | O(*n*) | métrica de enfoque estándar y barata | depende del contenido: una hoja casi vacía parece «borrosa» |
| **Filtros de ruido** | `ruido.py` | quitar sal y pimienta / ruido del sensor | mediana 3×3, gaussiano 3×3, bilateral (d = 7, σcolor 40, σespacio 7) | O(*n*·k) | la mediana conserva bordes ante ruido impulsivo; el bilateral suaviza sin borrar trazos | el bilateral es el más lento |
| **Morfología** | `perspectiva.py`, `mejora.py`, `preprocesado_ocr.py`, `manuscrito.py`, segmentación | cerrar huecos del papel, quitar renglones y cuadrícula, unir letras en palabras | cierre 3 iteraciones; aperturas con líneas de ¼ del ancho/alto; dilataciones proporcionales a la altura de letra | O(*n*·k) | operaciones simples y explicables | parámetros ligados a la altura de letra estimada |
| **Componentes conexas** | `calidad.py`, `preprocesado_ocr.py`, `manuscrito.py`, segmentación | estimar la altura de letra, contar renglones, localizar zonas de tinta | conectividad 8, con estadísticas | O(*n*) | base de la segmentación sin modelos | letras pegadas cuentan como un componente |

## 2. Reconocimiento local (sin servidor IA)

| Algoritmo | Dónde | Qué hace | Límites conocidos |
|-----------|-------|----------|-------------------|
| **OCR Tesseract 5 (LSTM)** | `ocr.py`, `reconocimiento.py`, `adaptativo.py` | texto por palabras con confianza; idiomas `spa+eng`; PSM según el perfil | manuscrito y fórmulas 2D: se marcan y se conservan como imagen. **Sin `spa.traineddata` pierde tildes** (`/api/v2/listo` lo avisa desde FULL-32) |
| **Reconocimiento adaptativo** | `adaptativo.py` (BACK-28) | prueba variantes de preprocesado y PSM y se queda con la de mejor confianza media, con procedencia de cada decisión | más lento que una sola pasada; `RECONOCIMIENTO_MODO=clasico` lo desactiva |
| **Fórmulas a LaTeX** | `formulas.py` | heurísticas para fórmulas en una línea; **validación** con lista blanca de comandos y dibujo con mathtext | no hay verificación simbólica (ver §5) |

## 3. Servidor IA (PC con GPU)

| Algoritmo | Dónde | Qué hace | Parámetros reales | Límites medidos |
|-----------|-------|----------|-------------------|-----------------|
| **Máscara de tinta** | `ia_servidor/segmentacion.py` `mascara_tinta` | fondo por mediana grande, diferencia y Otsu; color por saturación; apertura 2×2 | núcleo de mediana proporcional al tamaño | tinta muy clara se pierde |
| **Quitar renglones y marco** | `quitar_lineas_y_marco`, `_sin_lineas_largas` | aperturas con líneas horizontales/verticales largas y resta | ¼ del ancho/alto; 9 y 5 alturas de letra | una raya de fracción muy larga puede borrarse (se conserva en el recorte) |
| **Segmentación por regiones** | `regiones_opencv` | dilatación según la altura de letra → componentes → cajas → **fusión de cajas que se solapan** (deduplicación de recortes, contención ≥ 0,5) → unión de líneas del mismo párrafo → orden de lectura | `union_h` 1,6, `union_v` 1,1, `max_area` 0,06, `IA_SEG_HUECO_LINEAS` = **0,2** (medido, [evaluacion-multimodal.md §5.2](evaluacion-multimodal.md)) | en la foto real todavía une zonas distintas (definiciones + ley de senos + gráfica) |
| **VLM por región** | `servicio.py` + Ollama | cada recorte va a `qwen3-vl:8b-instruct` con un prompt corto según la tarea (región, fórmula, diagrama); respuesta en texto plano | `temperature` 0, `seed` 0, `num_ctx` 8192, `num_predict` acotado; respaldo `4b-instruct` si falta VRAM | no es determinista del todo (dos pasadas de la misma foto dieron 0 y 4 bloques inciertos); puede «corregir» la ortografía |
| **Validación del resultado** | `esquemas.py` (Pydantic) | limpia `<think>` y bloques de código, detecta «ilegible», marca `[?]` y llaves desbalanceadas, limita el tamaño (30 000 caracteres) | — | una respuesta inválida deja **esa región** «sin leer»; el documento sigue |

## 4. De la respuesta al apunte y al PDF (backend)

| Algoritmo | Dónde | Qué hace |
|-----------|-------|----------|
| **División de regiones multilínea** | `analisis_remoto.py` `dividir_lineas` (BACK-38) | una línea matemática → un bloque fórmula; líneas de texto seguidas → un bloque texto; dudas por línea a su parte; mismo recorte |
| **Reconciliación de ediciones** | `documento.py` `fusionar` | aplica la edición del usuario conservando los campos inmutables del OCR (`procedencia`, `revision`, originales, `bbox`, recorte) y marca `editado` |
| **Validación del documento** | `documento.py` (Pydantic, `extra="forbid"`) | rechaza campos desconocidos, ids inválidos y tamaños excesivos |
| **Resumen extractivo** | `estructura.py` | puntúa frases por frecuencia de términos (sin palabras vacías) normalizada por longitud; elige 3 en su orden original; solo de bloques confirmados |
| **Detección de discrepancias** | `investigacion.py` | compara números de las frases del apunte que nombran el concepto con los de la fuente, y definiciones en negativo |

## 5. Lo que NO está implementado (y por qué)

| Pedido en el ticket | Estado | Motivo |
|---------------------|--------|--------|
| Transformada de Hough | no implementado | la detección de bordes + contornos cubre el enderezado; el deskew fino usa proyecciones (`preprocesado_ocr.py`, ±15°) |
| Verificación simbólica (SymPy) | no implementado | `formulas.py` evita a propósito `sympy.parse_expr`/`eval` (ejecutan la entrada); la validación es sintáctica (lista blanca + mathtext). Equivalencias de notación solo en la evaluación (`ia_servidor/medir.py`) |
| Asociación espacial de diagramas (nodos/aristas) | no implementado | la tarea «diagrama» devuelve descripción y etiquetas; el diagrama se conserva como recorte |
| PaddleOCR-VL 1.6 | no integrado | no se probó su compatibilidad en Windows/RTX 3060 en esta versión; Tesseract queda como respaldo local |
| Tablas estructuradas desde la foto | parcial | el VLM devuelve la tabla como texto con « \| »; la estructura se arma en el editor |

## 6. Ejemplo con una foto real

La sesión del 14/11/2026 con la foto real del pizarrón (privada, fuera de Git) recorrió §3 y §4:
17 regiones → 35 bloques, 23 por división multilínea; resultados y fallos que siguen abiertos en
[generacion-pdf.md §7](generacion-pdf.md) y [evaluacion-multimodal.md](evaluacion-multimodal.md). Las
imágenes de ese ejemplo no se publican (contienen la letra de una persona); los ejemplos ilustrados son
sintéticos ([back-38-ejemplo-ia.pdf](evidencias/back-38-ejemplo-ia.pdf)).
