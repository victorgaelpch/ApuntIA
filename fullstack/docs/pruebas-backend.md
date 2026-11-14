# Pruebas del backend (BACK-25)

Cómo se prueba el backend, qué cubre cada archivo y cómo comprobar que la suite
detecta regresiones. Todo se ejecuta sin credenciales ni servicios externos: la
investigación usa respuestas simuladas de Wikipedia y cada prueba usa una carpeta
de datos y una base SQLite temporales (fixture `datos_tmp`).

## 1. Ejecución

Desde `back/motori_magenes`, con el entorno de `requirements-dev.txt`:

| Qué | Comando | Duración (equipo de desarrollo) |
|-----|---------|---------------------------------|
| Suite rápida (la de CI) | `pytest` | ~45 s, 368 pruebas |
| Con cobertura | `pytest --cov=app --cov-report=term-missing` | ~35 s |
| Evaluación real de OCR y fórmulas (opt-in) | `pytest -m evaluacion` | ~5 s, necesita Tesseract |
| Tiempos y memoria (opt-in) | `pytest -m rendimiento -s` | ~8 s |
| Mutaciones (¿la suite detecta fallos?) | `python herramientas/mutaciones.py` | ~3 min |
| Informe de OCR por muestra | `python herramientas/evaluar_ocr.py` | ~5 s |

`pytest.ini` excluye por defecto los marcadores `evaluacion` y `rendimiento`, porque
dependen del equipo (Tesseract instalado, velocidad de la CPU). Si Tesseract no está
instalado, las pruebas que lo necesitan se **omiten** (aparecen como `skipped`), no pasan
en falso.

## 2. Línea base e inventario

La suite v1 (`test_api.py` y `test_procesamiento.py`, 74 pruebas) **no se modificó**
en la v2: sigue pasando igual, lo que garantiza el contrato de `POST /analisis`,
`GET /salud` y el formato de errores. `conftest.py` solo ganó fixtures nuevas.

| Archivo | Pruebas | Qué cubre |
|---------|--------:|-----------|
| `test_api.py` | 39 | Contrato v1: PNG, cabeceras, errores, CORS, límites |
| `test_procesamiento.py` | 35 | OpenCV v1: perspectiva, mejora, ruido |
| `test_regresion.py` | 8 | Disco lleno (507), OCR agotado, investigación lenta, migración 0004, contrato v1 congelado |
| `test_datos.py` | 7 | Migraciones (repetibles, modificadas, fallidas), cascadas, almacén aislado |
| `test_cuentas.py` | 21 | Registro, sesión, CSRF, fuerza bruta, recuperación, tokens caducados, borrado |
| `test_seguridad_api.py` | 73 | IDOR en cada ruta con id, traversal, contenido disfrazado, LaTeX/HTML, 413, CORS, límites, cabeceras, logs |
| `test_entrada.py` | 10 | Subida multipágina y validación por página |
| `test_trabajos.py` | 9 | Trabajos durables: estados, cancelación, reintento, recuperación, límites |
| `test_ocr.py` | 7 | Adaptador de OCR, bloques, estados por confianza, motor ausente |
| `test_preprocesado_ocr.py` | 8 | Preprocesado de cuaderno y pizarrón |
| `test_manuscrito.py` | 7 | Respaldo de manuscritos sin inventar texto |
| `test_formulas.py` | 39 | Detección, conversión a LaTeX, lista blanca, render |
| `test_documento.py` | 16 | Esquema intermedio y reglas de procedencia |
| `test_analisis.py` | 6 | Análisis completo, parcial, cancelado, idempotente |
| `test_historial.py` | 9 | Listado, búsqueda, versiones y conflictos |
| `test_estructura.py` | 8 | Apunte estructurado sin contenido inventado |
| `test_investigacion.py` | 20 | Consentimiento, privacidad, fuentes, inyección, discrepancias, caídas |
| `test_pdf.py` | 16 | PDF legible, Unicode, tablas largas, imágenes dañadas, exportación idempotente |
| `test_evaluacion.py` | 12 | (opt-in) CER del corpus real y fórmulas |
| `test_rendimiento.py` | 3 | (opt-in) tiempos y memoria |

## 3. Cobertura

`pytest --cov=app` (noviembre de 2026): **95 %** de las líneas de `app/` (3061
sentencias, 164 sin cubrir). Los módulos por debajo del 90 %: `config.py` (81 %, ramas de
variables de entorno), `ocr.py` (87 %, errores raros de Tesseract) y `main.py` (88 %,
ciclo de vida del servidor real). La cobertura no es el objetivo: lo es que las
mutaciones de la sección 4 se detecten.

## 4. ¿Detecta regresiones? (mutaciones)

`herramientas/mutaciones.py` copia el backend a una carpeta temporal, introduce **un**
fallo típico, ejecuta la suite y exige que falle por una prueba (no por un error de
recolección). Antes ejecuta la suite sin mutar para comprobar que parte de verde.

| Mutación | Detectada | Primera prueba que falla |
|----------|-----------|--------------------------|
| IDOR: el apunte no se filtra por propietario | sí | `test_historial.py::test_otro_usuario_no_ve_ni_encuentra_nada` |
| CSRF: no se comprueba el token | sí | `test_cuentas.py::test_csrf_obligatorio_en_cambios` |
| Procedencia: el cliente puede reescribir lo que dijo la foto | sí | `test_documento.py::test_la_edicion_conserva_la_procedencia` |
| PDF: el texto del usuario no se escapa | sí | `test_pdf.py::test_unicode_y_html_no_se_interpretan` |
| OCR: una palabra dudosa ya no vuelve incierto el bloque | sí | `test_manuscrito.py::test_una_palabra_dudosa_hace_incierto_el_bloque` |
| Abuso: sin límite de trabajos por usuario | sí | `test_trabajos.py::test_limite_por_usuario_y_aislamiento` |
| Investigación: se aceptan páginas con instrucciones incrustadas | sí | `test_investigacion.py::test_desambiguacion_e_inyeccion_se_descartan` |
| Cabeceras: sin nosniff | sí | `test_seguridad_api.py::test_cabeceras_de_seguridad[/salud]` |
| Contrato v1: /analisis deja de devolver PNG | sí | `test_api.py::test_formatos_permitidos[PNG-image/png-a.png]` |
| Archivos: se sirven archivos de otro apunte del mismo usuario | sí | `test_seguridad_api.py::test_archivo_de_otro_apunte_propio_no_se_sirve` |

Resultado: **10/10**. La primera versión del script daba 10/10 en 10 s porque las
pruebas no encontraban `fullstack/docs/api-v2.md` en la copia (error de recolección, no
detección); se corrigió copiando `fullstack/docs/` y exigiendo un `FAILED` real.

## 5. Rendimiento (`pytest -m rendimiento -s`)

| Caso | Tiempo | Pico de memoria (tracemalloc) | Límite de alarma |
|------|-------:|------------------------------:|------------------|
| v1 `/analisis` con una foto de 12 MP | 0,28 s | 74 MB | 10 s / 600 MB |
| OCR de una página (preprocesado + Tesseract) | 0,32 s | 14 MB | 6 s / 300 MB |
| PDF con 20 fotos de 4 MP en el anexo | 6,6 s (con tracemalloc; 2,5 s sin él) | 67 MB | 12 s / 400 MB |

Los límites son ~3× lo medido: sirven para detectar regresiones fuertes (por ejemplo,
dejar de reducir las imágenes), no como prueba de velocidad.

## 6. Evaluación real (`pytest -m evaluacion`)

Usa el corpus etiquetado de `herramientas/corpus.py` y Tesseract 5.3.4. Umbrales (línea
base de PROCESAMIENTO.md con margen): CER ≤ 2 % en impresos de cuaderno y pizarrón,
≤ 5 % en manuscrito claro, ≤ 12 % en manuscrito difícil, 0 manuscritos «reconocidos con
errores», 0 fórmulas 2D inventadas, ≥ 3/4 fórmulas en línea exactas, cuadrícula ≤ 2 % y diagrama ≤ 10 %. Resultado: 12/12. El banco completo de punta a punta está en `fullstack/evaluacion/` (fullstack/docs/evaluacion.md).

## 7. Fallos de infraestructura cubiertos

| Fallo | Comportamiento comprobado |
|-------|---------------------------|
| Tesseract no instalado | El análisis falla con `OCR_NO_DISPONIBLE`, nunca con texto vacío |
| OCR agotado en una página | Trabajo `parcial` con la página señalada |
| Disco lleno al subir | `507 ALMACENAMIENTO_LLENO`, sin apunte ni archivos huérfanos |
| Disco lleno durante el análisis o el PDF | Trabajo `fallido` con `ALMACENAMIENTO_LLENO`; no se guarda un PDF a medias |
| Investigación caída o lenta | Trabajo `fallido` con `INVESTIGACION_NO_DISPONIBLE` dentro del límite de tiempo; el apunte no cambia |
| Proveedor desactivado (sin Internet) | `503` al pedir investigación; el resto funciona |
| Reinicio a mitad de un trabajo | Se vuelve a encolar (`test_trabajos.py`) |
| Migración modificada o fallida | Se detecta y no deja cambios a medias (`test_datos.py`) |
