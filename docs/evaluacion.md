# Banco de evaluación y métricas (FULL-19)

Mide la calidad **real** del reconocimiento, la estructura y el PDF con un corpus etiquetado, para
decidir con datos y no con impresiones.

```bash
python fullstack/evaluacion/evaluar.py --comparar fullstack/evaluacion/linea-base.json
```

Sube cada muestra como un apunte por la API (en proceso, con datos temporales), espera al análisis
de producción y compara con la verdad de referencia. Escribe `informe.json`, `informe.csv` e
`informe.md` en `fullstack/evaluacion/resultados/<fecha>/` (ignorada por Git) y **sale con 1** si algo
empeora frente a la línea base. Con `--guardar-linea-base` actualiza `fullstack/evaluacion/linea-base.json`
(hacerlo solo cuando una mejora esté revisada, y en el mismo commit). Se ejecuta en
`fullstack/scripts/validar.sh` (y por tanto en la CI) cuando hay Tesseract. Tarda ~11 s.

## 1. Corpus

Todas las muestras son **sintéticas** y se generan con código (`back/motori_magenes/herramientas/corpus.py`)
con las fuentes DejaVu (licencia libre) que trae matplotlib: no hay fotos de personas ni apuntes reales.
La única foto real del repositorio (`back/bd/img/image.png`, un pizarrón del proyecto) se usa en las
pruebas de integración, no aquí.

| Categoría | Muestras |
|-----------|----------|
| Cuaderno rayado / cuadriculado | `impreso_cuaderno`, `cuaderno_cuadriculado` |
| Iluminación: sombra / poca luz | `cuaderno_con_sombra`, `pizarron_con_ruido` |
| Pizarrón blanco inclinado / verde de tiza | `impreso_pizarron`, `pizarron_oscuro` |
| Manuscrito claro / difícil | `manuscrito_cuaderno`, `manuscrito_dificil` |
| Fórmulas en línea / en dos dimensiones | `formulas_pizarron`, `formulas_2d` |
| Diagramas | `diagrama` |
| Varias páginas | cuaderno + pizarrón en un mismo apunte |
| Archivos inválidos o grandes | HTML disfrazado, vacío, demasiado grande, PNG truncado |

## 2. Métricas (todas calculadas)

| Métrica | Definición |
|---------|------------|
| CER / WER | Distancia de edición por caracteres / palabras entre lo reconocido y la referencia |
| Reconocidos / inciertos / sin leer | Estado de los bloques (confianza ≥ 0,80 / 0,50–0,80 / < 0,50 o sin texto) |
| **Reconocidos con errores** | Bloques marcados como reconocidos cuyo texto NO está en la referencia: lo peor (un error que no se avisa) |
| Como imagen | Bloques sin texto conservados con su recorte (manuscrito ilegible, fórmula 2D, dibujo) |
| Líneas exactas | Líneas de la referencia que aparecen tal cual |
| Orden de lectura | Entre las líneas encontradas, cuántas están en el orden correcto |
| Fórmulas | Exactas (LaTeX igual a la referencia), LaTeX válidos y **falsas reconocidas** |
| PDF | Abre y cuadran las páginas, texto seleccionable, Unicode, tabla completa, fórmula e imágenes visibles, enlace de la fuente, metadatos, orden de las páginas (leído con pypdf) |
| Robustez | Código HTTP y de error ante archivos inválidos o grandes |
| Rendimiento | ms por muestra, PDF, tiempo total y memoria máxima del proceso |

## 3. Línea base (2026-11-10)

Python 3.13.18 · OpenCV 5.0.0 · ReportLab 5.0.1 · Tesseract 5.3.4 (eng, spa).

| Muestra | Fuente | Escritura | CER | WER | Rec. / inc. / sin leer | Rec. con errores | Como imagen | Líneas exactas | Orden |
|---|---|---|---:|---:|---|---:|---:|---:|---:|
| impreso_cuaderno | cuaderno | impreso | 0.7% | 3.9% | 3 / 0 / 0 | 1 | 0 | 80% | 100% |
| cuaderno_con_sombra | cuaderno | impreso | 0.7% | 3.9% | 3 / 0 / 0 | 1 | 0 | 80% | 100% |
| cuaderno_cuadriculado | cuaderno | impreso | 0.7% | 3.9% | 5 / 0 / 0 | 1 | 0 | 80% | 100% |
| impreso_pizarron | pizarron | impreso | 0.7% | 3.9% | 5 / 0 / 0 | 1 | 0 | 80% | 100% |
| pizarron_con_ruido | pizarron | impreso | 0.7% | 3.9% | 5 / 0 / 1 | 1 | 1 | 80% | 100% |
| pizarron_oscuro | pizarron | impreso | 0.7% | 3.9% | 5 / 0 / 0 | 1 | 0 | 80% | 100% |
| manuscrito_cuaderno | cuaderno | manuscrito | 0.0% | 0.0% | 2 / 0 / 0 | 0 | 0 | 100% | 100% |
| manuscrito_dificil | cuaderno | manuscrito | 5.6% | 40.0% | 1 / 1 / 0 | 0 | 0 | 50% | 100% |
| formulas_pizarron | pizarron | formula | 35.4% | 64.7% | 1 / 2 / 1 | 0 | 1 | 50% | 100% |
| formulas_2d | pizarron | formula | 100.0% | 100.0% | 0 / 0 / 4 | 0 | 4 | 0% | — |
| diagrama | cuaderno | diagrama | 0.0% | 0.0% | 1 / 0 / 2 | 0 | 2 | 100% | 100% |

- **Fórmulas:** 3/8 exactas, 3 LaTeX válidos, 0 falsas. Las 4 en dos dimensiones no se reconocen y se conservan como imagen.
- **Dos páginas + PDF:** análisis completado; PDF de 5 páginas y 207 KB en 293 ms; todas las comprobaciones en verde.
- **Robustez: html_disfrazado → 400 TIPO_NO_PERMITIDO; vacio → 400 ARCHIVO_VACIO; demasiado_grande → 400 ARCHIVO_DEMASIADO_GRANDE; png_truncado → 400 IMAGEN_CORRUPTA;
- **Regresiones vigiladas:** 6/6 en verde.
- Tiempo total 11.4 s; memoria máxima 390 MB.

**Lectura:** el texto impreso se lee con CER 0,7 % en todas las condiciones; el único error es «x²»
leído como «x?», y aparece como «reconocido con errores» (se informa, no se oculta). El manuscrito
difícil baja a 5,6 % de CER sin ningún error presentado como seguro. Las fórmulas en dos dimensiones
son la limitación principal: se conservan como imagen y se pueden escribir a mano en el editor.

## 4. Metas acordadas

Son los umbrales de `tests/test_evaluacion.py` y de la comparación (`--comparar`):

| Meta | Valor |
|------|-------|
| CER texto impreso (cuaderno, pizarrón, sombra, ruido, cuadrícula) | ≤ 2 % |
| CER manuscrito claro / difícil | ≤ 5 % / ≤ 12 % |
| Manuscritos «reconocidos con errores» | 0 |
| Fórmulas falsas reconocidas | 0 |
| Fórmulas en línea exactas | ≥ 3 de 4 |
| Empeoramiento tolerado frente a la línea base | ≤ 2 puntos de CER por muestra, ningún bloque más «reconocido con errores», ninguna comprobación del PDF que deje de pasar |

## 5. Regresiones de errores ya vistos

| Error observado | Comprobación |
|-----------------|--------------|
| BACK-12: la mediana borraba la tilde de «rápido» en el pizarrón de tiza | «rápido» aparece en `pizarron_oscuro` |
| BACK-21: un símbolo dudoso vaciaba un párrafo bueno | `impreso_cuaderno` sin bloques sin leer |
| BACK-15: fórmulas 2D dadas por buenas | 0 reconocidas en `formulas_2d` |
| BACK-14: manuscrito mal leído presentado como seguro | 0 «reconocidos con errores» en manuscritos |
| FULL-19: la cuadrícula se lee como texto | CER ≤ 2 % en `cuaderno_cuadriculado` |
| FULL-19: un dibujo genera texto inventado | `diagrama` conservado como imagen y CER ≤ 10 % |

## 6. Comprobaciones manuales y limitaciones

- **Manual:** los PDF se revisaron como imagen (pdftoppm) y con dos lectores de texto (pypdf y
  pdftotext de poppler): fórmula centrada, tablas con encabezado repetido, tildes y símbolos. Con un
  lector gráfico (Evince, Acrobat, el visor del navegador) no se pudo revisar en este entorno.
- El manuscrito del corpus está **simulado** con fuentes y deformaciones, no es letra real: el
  reconocimiento de letra real de alumnos será peor. Para medirlo hacen falta fotos con autorización
  de sus autores, que no deben subirse a un repositorio público (FULL-24).
- Las cifras dependen de la versión de Tesseract (5.3.4); la CI y Docker usan esa misma versión.
- Antes/después: cada cambio de OCR o PDF debe ejecutar `--comparar` y, si mejora, actualizar la
  línea base en el mismo commit con el informe en la descripción.
