# Procesamiento de imágenes – detalles técnicos

Decisiones, parámetros y mediciones de cada etapa del backend. Para instalarlo y ejecutarlo, ver
[`README.md`](README.md); para el contrato HTTP, ver [`docs/api.md`](../../docs/api.md).

Orden del pipeline: **validar → redimensionar → perspectiva → ruido → mejora → (grises) → PNG**.

## Validación de imágenes (BACK-02)

El contrato completo está en [`docs/api.md`](../../docs/api.md). `POST /analisis` comprueba, en este orden:

1. Que exista el campo `file` → si no, `400 ARCHIVO_AUSENTE`.
2. Que no esté vacío → si lo está, `400 ARCHIVO_VACIO`.
3. Que no supere `MAX_UPLOAD_MB` → si lo supera, `413 ARCHIVO_DEMASIADO_GRANDE`. Se leen como máximo `límite + 1` bytes.
4. Que su **firma binaria** sea JPEG, PNG o WEBP; la extensión y el `Content-Type` no bastan → si no, `415 TIPO_NO_PERMITIDO`.
5. Que no supere `MAX_MEGAPIXELES`, leyendo solo la cabecera → si la supera, `413 IMAGEN_DEMASIADO_GRANDE`.
6. Que OpenCV pueda decodificarla → si no puede, `400 IMAGEN_CORRUPTA`.

Todo ocurre en memoria: ya no se escriben archivos en disco, por lo que desaparece la variable `IMAGES_DIR`. El nombre recibido se limpia antes de usarlo en las cabeceras de la respuesta.

## Manejo de errores (BACK-07)

`app/core/errores.py` registra un manejador para cada tipo de fallo, y todos responden `{"error": {"codigo", "mensaje"}}`:

| Origen | HTTP | `codigo` |
|--------|------|----------|
| `ApiError`: validaciones previstas | 400 / 413 / 415 | Según el caso (ver BACK-02) |
| Parámetro de consulta no válido (`RequestValidationError`) | 422 | `PARAMETRO_INVALIDO` |
| Ruta inexistente o método incorrecto | 404 / 405 | `RUTA_NO_ENCONTRADA` / `METODO_NO_PERMITIDO` |
| `ProcesamientoError`: fallo de OpenCV | 500 | `ERROR_PROCESAMIENTO` |
| Cualquier otra excepción | 500 | `ERROR_INTERNO` |

- **Cliente frente a servidor:** los 4xx explican qué corregir; los 5xx dan un mensaje genérico.
- **Sin información sensible:** las trazas, rutas y mensajes de excepción solo se escriben en el log (`apuntia.errores`). El cliente recibe `X-ApuntIA-Error-Id`, que coincide con la línea del log.
- **Archivos temporales:** no hay; la imagen se procesa en memoria y FastAPI cierra el `UploadFile` al terminar la petición.

## Pipeline de procesamiento (BACK-03)

`app/services/procesamiento.py` no depende de FastAPI: trabaja con matrices NumPy en BGR `uint8`.

```python
from app.services.procesamiento import procesar, codificar_png, OpcionesProcesamiento

resultado = procesar(imagen_bgr, OpcionesProcesamiento(grises=True))
png = codificar_png(resultado.imagen)
resultado.tiempos_ms        # {"copia": 0.4, "grises": 1.2, ...}
resultado.perspectiva       # "corregida" | "no_detectada" | "desactivada"
```

- **Decodificación:** `cv2.imdecode`, dentro de la validación (BACK-02). Las imágenes en gris o con canal alfa se normalizan a BGR.
- **Orden fijo de etapas:** `construir_etapas()` devuelve las etapas activas en orden. Cada una mide su tiempo y, si OpenCV falla, se convierte en `ProcesamientoError` (500).
- **El original no se modifica:** el pipeline trabaja sobre una copia.
- **Salida:** PNG sin pérdida, devuelto directamente en la respuesta con las cabeceras `X-ApuntIA-*` del contrato.

## Corrección de perspectiva (BACK-04)

`app/services/perspectiva.py`, activada por defecto (`?perspectiva=false` la desactiva):

1. La detección se hace sobre una copia reducida (lado mayor ≤ 800 px); las esquinas se reescalan al original.
2. Se buscan cuadriláteros con dos métodos: **bordes de Canny** dilatados y **umbral de Otsu**, este último para pizarrones claros sobre pared oscura o fotos con poca luz.
3. Un candidato solo se acepta si es **fiable**: 4 vértices, convexo, entre el 10 % y el 98 % del área, ángulos interiores de 45° a 135°, proporción de lados ≤ 6 y como mucho una esquina pegada al borde de la foto.
4. Las esquinas se ordenan (sup-izq, sup-der, inf-der, inf-izq) y se aplica `warpPerspective`. El tamaño de salida es la media de los lados opuestos, así se conservan las proporciones.
5. Si no hay un candidato fiable, se devuelve la imagen sin cambios con `X-ApuntIA-Perspectiva: no_detectada`. **No es un error.**

Resultados con las muestras de `herramientas/muestras.py` (`python -m herramientas.muestras ../bd/muestras`):

| Muestra | Resultado | Error máx. de esquinas |
|---------|-----------|------------------------|
| Inclinada / con sombra / con ruido | `corregida` (bordes) | 4 px en 1600×1200 |
| Oscura | `corregida` (umbral) | — |
| Pizarrón pequeño (~16 % de la foto) | `corregida` | 6 px |
| Frontal (el pizarrón ocupa toda la foto) | `no_detectada`: no hace falta corregir | — |
| Sin pizarrón / 20 fondos de ruido | `no_detectada`, 0 falsos positivos | — |
| Foto real `bd/img/image.png` | `no_detectada` | — |

![Antes y después](../../docs/evidencias/back-04-perspectiva.jpg)

**Limitación conocida:** en la foto real `bd/img/image.png` el pizarrón **se sale del encuadre** por arriba y por abajo, y es blanco sobre pared blanca, así que no hay cuatro esquinas visibles. Se devuelve sin rectificar en lugar de deformarla con un cuadrilátero falso. Para estos casos, una mejora futura sería intersecar las rectas del marco (Hough).

## Eliminación de ruido (BACK-06)

`app/services/ruido.py` se aplica **antes** de la mejora, para que el enfoque no amplifique el ruido. Se elige con `?ruido=`:

| Valor | Filtro |
|-------|--------|
| `combinado` (por defecto) | Mediana 3×3 + bilateral (d=7, sigmaColor=40, sigmaSpace=7) |
| `mediana` | `medianBlur` 3×3 |
| `gaussiano` | `GaussianBlur` 3×3 |
| `bilateral` | `bilateralFilter` (d=7, 40, 7) |
| `ninguno` | Sin filtrar |

Comparación con `python -m herramientas.evaluar_ruido`, sobre un pizarrón de 1600×1066 con ruido gaussiano σ=18 y un 1 % de sal y pimienta. La nitidez es la varianza del laplaciano en la zona del texto, relativa a la imagen limpia; el ruido la infla por encima del 100 %.

| Filtro | PSNR (dB) | Contraste texto | Nitidez bordes | Tiempo (ms) |
|---|---|---|---|---|
| (limpia) | ∞ | 174.2 | 100 % | — |
| (sin filtro) | 21.1 | 168.1 | 209 % | 0 |
| mediana | 30.7 | 169.2 | 78 % | 1 |
| gaussiano | 27.7 | 159.1 | 17 % | 1 |
| bilateral | 23.0 | 170.3 | 194 % | 79 |
| **combinado** | **36.2** | **170.3** | **100 %** | 26 |
| *NL-means h=7 (descartado)* | 23.0 | — | — | 902 |

![Recorte: con ruido, mediana, gaussiano, bilateral, combinado](../../docs/evidencias/back-06-ruido.jpg)

- El **gaussiano** borra escritura: el contraste del texto cae a 159 y la nitidez al 17 %.
- El **bilateral** solo no elimina la sal y pimienta, porque trata esos puntos como bordes.
- La **mediana** quita los puntos, pero deja grano.
- La **combinación** recupera la nitidez original sin perder contraste. Es la opción por defecto; el contrato (`docs/api.md`) se actualizó con este valor.

## Calidad y nitidez (BACK-05)

`app/services/mejora.py`, activada por defecto (`?mejorar=false` la desactiva). Trabaja solo sobre el canal **L de LAB**, así que los colores de los marcadores se conservan.

| Paso | Cuándo | Parámetros |
|------|--------|------------|
| Gamma automática | L medio < 105 (foto oscura) | Lleva la luminancia media al 50 %, con gamma entre 0.4 y 1 |
| Normalización de iluminación | Solo si la perspectiva se **corrigió** | Fondo = cierre morfológico de tamaño lado/40 + desenfoque; L = L / fondo × 235 |
| CLAHE | Si **no** se normalizó la iluminación | clipLimit 2.0, rejilla 8×8 |
| Máscara de enfoque | Siempre | cantidad 0.6, sigma = max(0.8, lado/1500) |

Comparación con `python -m herramientas.evaluar_mejora`. Contraste = diferencia media de L entre el fondo y el texto; más alto es más legible. «En sombra» es la franja del 45 % al 75 % del ancho. «Saturados» es el % de píxeles a 0 o 255:

| Variante | clara | oscura | sombra |
|---|---|---|---|
| sin mejora | 168.9 / 195.0 / 0.0 | 69.2 / 77.6 / 0.0 | 100.6 / 117.9 / 0.0 |
| CLAHE + enfoque (foto con pared) | 177.4 / 201.5 / 1.1 | 87.6 / 98.4 / 0.0 | 111.8 / 125.2 / 0.2 |
| Iluminación + enfoque (pizarrón rectificado) | 169.7 / 194.2 / 0.3 | **156.3 / 179.9** / 0.1 | **172.0 / 198.6** / 0.4 |

![Antes y después: foto real, oscura y con sombra](../../docs/evidencias/back-05-mejora.jpg)

**Decisiones y limitaciones:**
- La normalización de iluminación duplica el contraste en fotos oscuras o con sombra. Pero, aplicada a una foto con pared o muebles, aclara las zonas oscuras y hace visibles los bloques del JPEG. Por eso solo se usa cuando la imagen ya es el pizarrón rectificado.
- Tras normalizar, el CLAHE no añadía contraste y creaba bandas en los degradados, así que se omite.
- Se probaron CLAHE con clipLimit 4 y enfoque de 1.5: ganan unos pocos puntos de contraste, pero duplican los píxeles saturados y crean halos. Se descartaron por sobreprocesamiento.
- En la foto real, que no se rectifica (ver BACK-04), solo se aplican CLAHE y enfoque: la mejora es moderada.

## Optimización del tiempo (BACK-09)

`python -m herramientas.benchmark` mide cada etapa (mediana de 3 repeticiones, en una máquina de 4 núcleos), incluidos la decodificación del JPEG y la codificación del PNG, igual que en la API.

**Cuellos de botella encontrados** en una foto de celular de 12 MP (4032×3024):
1. `mejora`, 490 ms: el cierre morfológico con un núcleo de unos 75 px a resolución completa.
2. `codificar_png`, 122–603 ms: proporcional al número de píxeles y al ruido.
3. `ruido`, 108 ms, y una copia inicial redundante, 10 ms.

**Cambios:**
- **Redimensionamiento controlado** al empezar: lado mayor ≤ `MAX_LADO_PROCESAMIENTO`, por defecto 2000 px, con `INTER_AREA`, que nunca amplía. 2000 px bastan para leer un pizarrón y reducen todas las etapas siguientes.
- **Fondo de iluminación a ¼ de resolución:** el fondo es una superficie suave. Frente al cálculo a resolución completa da 54.4 dB de PSNR, visualmente idéntico, y la etapa pasa de 490 a unos 20 ms.
- **Sin copia inicial:** ninguna etapa modifica su entrada. Solo se copia al final si ninguna etapa actuó.
- Se evaluó bajar la compresión PNG de 3 a 1: el tiempo es el mismo (54 ms frente a 54 ms en 2000×1500), así que se mantiene en 3.

**Antes y después**, mismas condiciones, tiempo total en ms:

| Imagen de referencia | Antes | Después | Mejora | Salida antes → después |
|---|---|---|---|---|
| Foto real 516×387 | 37 | 36 | = | 516×387 (no cambia) |
| Inclinada 1600×1200 | 106 | 72 | 1.5× | 1191×811 (no cambia) |
| Celular 12 MP | 862 | **149** | **5.8×** | 3001×2042, 521 KB → 1489×1013, 165 KB |
| Celular 12 MP con ruido | 1437 | **410** | **3.5×** | 7.3 MB → 1.5 MB |

Solo con el fondo a ¼, sin redimensionar, la foto de 12 MP pasa de 862 a 354 ms; con ambos cambios, el pipeline sin E/S tarda 86 ms.

**Calidad conservada:** las métricas de contraste de BACK-05 no cambian (oscura 156.3, sombra 172.0). Además, la respuesta pesa 3–5 veces menos, lo que también acorta la transferencia al navegador.

## Cambios realizados (BACK-01)

- El código de `index.py` se separó en `core` (configuración), `routers` (rutas) y `services` (lógica).
- La ruta fija `/home/yane/imagenes` se reemplazó por la variable `IMAGES_DIR`; la carpeta se crea automáticamente.
- Los orígenes de CORS ahora son configurables con `CORS_ORIGINS`.
- El nombre del archivo subido se limpia para impedir escribir fuera de la carpeta de imágenes (`../../archivo`).
- Se eliminó la relectura/reescritura redundante con OpenCV (no modificaba la imagen); OpenCV sigue en las dependencias para las siguientes tareas.
- `print` se sustituyó por `logging`.
- Se completó `requirements.txt` (antes vacío) e incluye `python-multipart`, necesario para recibir archivos.
- Se añadió `.gitignore` para no subir `__pycache__`, entornos virtuales, `.env` ni las imágenes generadas, y se quitó el `.pyc` que estaba versionado.

## OCR por bloques (BACK-13)

`app/services/ocr.py`. **No confundir** la limpieza de OpenCV (secciones anteriores) con el OCR: aquí se extrae el texto.

### Elección del motor

| Motor | Español | Licencia | Requisitos | Decisión |
|-------|---------|----------|------------|----------|
| **Tesseract 5** | Sí (`spa`, con tildes y ñ) | Apache-2.0 | Binario de ~30 MB, sin GPU; Windows, Linux, macOS y Docker | **Elegido** |
| PaddleOCR | Sí | Apache-2.0 | PaddlePaddle (~500 MB) y modelos descargados en el primer uso | Descartado por tamaño |
| EasyOCR | Sí | Apache-2.0 | PyTorch (~700 MB+); lento sin GPU | Descartado por tamaño y velocidad |
| TrOCR | Inglés en los modelos públicos | MIT | PyTorch + 1.3 GB de modelo | Descartado (ver BACK-14) |

El motor no está «cableado»: `OCR_MOTOR` lo elige (`tesseract` o `ninguno`) y otro motor puede implementar la clase `MotorOCR`.

### Salida

- Palabras → líneas → **bloques** (párrafos de Tesseract), en orden de lectura, con `bbox`, confianza ponderada por longitud y estado: `reconocido` (≥ 0.80), `incierto` (0.50–0.80) o `no_reconocido` (< 0.50).
- Un bloque de una línea con letra al menos 1.25 veces mayor que la mediana se marca como `titulo`.
- Texto normalizado en Unicode NFC: las tildes y la ñ llegan intactas al PDF.
- Tres resultados distintos: **fallo técnico** → `ErrorOCR` con código (`OCR_NO_DISPONIBLE`, `OCR_TIEMPO_AGOTADO`, `OCR_IDIOMA_NO_DISPONIBLE`), nunca texto vacío; **sin texto** → lista vacía; **confianza baja** → bloques `incierto`/`no_reconocido`.
- `GET /salud` añade `ocr: {disponible, motor, version, idiomas}`; los campos de la v1 no cambian.

### Línea base (sin preprocesar), con el corpus sintético

`python -m herramientas.evaluar_ocr --sin-preprocesar` (Tesseract 5.3.4, `spa+eng`). CER/WER: porcentaje de caracteres/palabras mal reconocidos (menor es mejor).

| Muestra | Escritura | CER | WER | Bloques (rec./inc./no rec.) |
|---|---|---|---|---|
| impreso_cuaderno | impreso | 0.7 % | 3.8 % | 5/0/0 |
| impreso_pizarron (inclinado) | impreso | **53.7 %** | 69.2 % | 3/1/0 |
| pizarron_oscuro (tiza) | impreso | 0.7 % | 3.8 % | 5/0/0 |
| manuscrito_cuaderno | manuscrito sintético | 0.0 % | 0.0 % | 3/0/0 |
| formulas_pizarron | fórmula | 22.9 % | 64.7 % | 2/2/0 |

El pizarrón fotografiado en ángulo pierde líneas enteras: es lo que corrige el preprocesado por perfil (BACK-12). La «escritura manuscrita» sintética es mucho más fácil que la real (ver BACK-14).

## Preprocesado para OCR por perfil (BACK-12)

`app/services/preprocesado_ocr.py`. Reutiliza la perspectiva (BACK-04) y la normalización de iluminación (BACK-05), pero con perfiles distintos:

| Paso | Pizarrón | Cuaderno |
|------|----------|----------|
| Perspectiva | Sí | Sí (hoja sobre la mesa) |
| Resolución para OCR | Lado entre 1400 y 2400 px (amplía las fotos pequeñas) | Igual |
| Color → gris | Luminancia; **se invierte** si es de tiza (fondo oscuro) | **Canal rojo**: el rayado azul y el margen rojo casi desaparecen y la tinta oscura se mantiene |
| Iluminación | Normalizar **solo si es desigual** (fondo con más de 45 niveles de diferencia) | Igual |
| Ruido | Mediana 3×3 **solo si hay ruido** (estimación MAD del laplaciano > 6) | No |
| Renglones | — | Se quitan solo las líneas que cruzan más del 60 % de la hoja **y** se repiten a intervalos regulares (≥ 4); `inpaint` rellena donde un trazo las cruza |
| Segmentación de Tesseract | `psm 3` | `psm 4` |

- **Trazos finos:** sin erosiones ni umbrales duros. Las líneas de tabla y las barras de fracción no son periódicas ni ocupan toda la hoja, así que se conservan (probado).
- **Original intacto:** se guarda aparte; el OCR trabaja sobre una copia.
- **Advertencias de calidad** en la página del documento: `BAJA_RESOLUCION` (lado menor < 600 px), `IMAGEN_BORROSA` (varianza del laplaciano < 40) e `IMAGEN_OSCURA`.

**Por qué las etapas son adaptativas.** La primera versión las aplicaba siempre y se midió una regresión en las fotos limpias: la mediana borraba la tilde de «rápido» en el pizarrón de tiza (CER de 0.7 % a 1.4 %), y la normalización adelgazaba trazos en el cuaderno limpio (de 0.7 % a 1.4 %). Por eso ahora solo se aplican cuando la imagen las necesita.

### Antes y después (`python -m herramientas.evaluar_ocr` con y sin `--sin-preprocesar`)

| Muestra | CER sin preprocesar | CER con preprocesado |
|---|---|---|
| impreso_cuaderno | 0.7 % | 0.7 % |
| cuaderno_con_sombra | 7.5 % | **0.7 %** |
| impreso_pizarron (inclinado) | 53.7 % | **0.7 %** |
| pizarron_con_ruido | 74.8 % | **0.7 %** |
| pizarron_oscuro (tiza) | 0.7 % | 0.7 % |
| manuscrito_cuaderno (sintético) | 0.0 % | 0.0 % |
| formulas_pizarron | 22.9 % | 22.9 % (las fórmulas se tratan en BACK-15) |

El 0.7 % restante es el superíndice «²», que Tesseract lee como «?». `tests/test_preprocesado_ocr.py` comprueba que ninguna muestra empeora frente a la línea base.

**Limitación:** una tabla con 4 o más filas equiespaciadas que ocupen más del 60 % del ancho de la hoja se confundiría con el rayado.

## Escritura a mano con alternativa segura (BACK-14)

`app/services/manuscrito.py`. Estrategia híbrida sobre Tesseract, **sin transcribir por imaginación**:

1. **Una palabra dudosa vuelve `incierto` el bloque.** Se midió que, en escritura irregular, Tesseract daba una media alta (0.85) a bloques con palabras mal leídas («inte grates», confianza 0.70) y los marcaba como `reconocido`. Ahora basta una palabra por debajo de 0.80 para que el bloque sea `incierto`, y esas palabras se listan en `palabras_dudosas`. Para que el bloque sea `no_reconocido` (y se descarte su texto) hace falta que la **media** sea baja: en BACK-21 se detectó que, si la palabra más dudosa decidía también eso, un símbolo mal leído («f'(x)», 0.45) vaciaba un párrafo de tres líneas correctas.
2. **Segundo intento** para lo que no quedó reconocido: recorte ampliado ×2, binarizado con Otsu y `psm 6`. Se queda la lectura con más confianza.
3. **Ilegible = sin texto:** un bloque `no_reconocido` queda vacío, de tipo `manuscrito`, y conserva su **recorte** con la ubicación, para transcribirlo a mano. Los `inciertos` conservan su texto y también el recorte, para comparar.
4. **Tinta no detectada por el OCR:** se conserva como `manuscrito` (trazos del tamaño del texto) o `imagen` (dibujos y esquemas, más altos y poco densos), siempre como recorte.
5. Los bloques `reconocidos` **no se tocan**, y las fórmulas se tratan aparte (BACK-15).

### Evaluación por tipo de escritura (`python -m herramientas.evaluar_ocr`)

«Reconocidos con errores» = bloques marcados como `reconocido` cuyo texto no es exacto: es el error más peligroso, porque el usuario confiaría en él sin revisar.

| Muestra | CER | Bloques (rec./inc./no rec.) | Reconocidos con errores |
|---|---|---|---|
| Impresas (5 muestras) | 0.7 % cada una | todas reconocidas | 1 por muestra: la línea «f(x) = x²», leída «x?» (se resuelve en BACK-15) |
| manuscrito_cuaderno (sintético regular) | 0.0 % | 2/0/0 | 0 |
| manuscrito_dificil (sintético irregular) | 11.1 % → **5.6 %** con el segundo intento | 1/1/0 | **0** (antes de limitar la confianza: 2) |

**Limitaciones declaradas:**
- La escritura sintética (tipografías Hershey de OpenCV) es más regular que la real: con fotos reales de cuadernos el CER será mayor y habrá más bloques `incierto`/`no_reconocido`. Hay que evaluarlo con fotos reales cedidas con permiso (ver FULL-19).
- **No se adoptaron motores específicos de manuscritos:** TrOCR (modelos públicos en inglés, 1.3 GB y PyTorch) y PaddleOCR (~500 MB). Se pueden añadir como otro `MotorOCR` sin cambiar este flujo.
- El texto en cursiva muy unida o con mala letra quedará, en general, como recorte para transcribir a mano: es el comportamiento buscado frente a inventar texto.

## Fórmulas a LaTeX verificable (BACK-15)

`app/services/formulas.py`.

| Paso | Cómo |
|------|------|
| Detección | Una línea es fórmula si tiene muchos símbolos matemáticos (`= + - * / ^ √ ∫ Σ ²`…) y como mucho una palabra corta. «Si f(x) = x², entonces…» es una **frase** y se queda como texto |
| Normalización del OCR | Comillas leídas en vez de `^` («c”2»), `*` entre letra y número sin espacios («x*2» → `x^2`), `-=` → `=`, `²`/`³`, letras griegas Unicode |
| Conversión | Analizador sintáctico **propio** (descenso recursivo): sumas, productos implícitos, fracciones con `/` → `\frac`, potencias, subíndices, `sqrt`/`√`, funciones, `lim`, `Σ`, `∫`, relaciones (`≤`, `≠`…). **No usa `eval` ni `sympy.parse_expr`**: la entrada nunca se ejecuta |
| Verificación | Lista blanca de comandos LaTeX (rechaza `\input`, `\write`, `\def`, `\href`…, además de `$`, `%` y saltos de línea; máximo 500 caracteres y llaves equilibradas) y dibujo con **mathtext** de matplotlib, que no es un motor TeX. Si no se dibuja → `latex_valido: false` |
| Estado | Una fórmula es `reconocido` solo si se convirtió y ninguna palabra bajó de 0.90; si no, `incierto`. **Siempre** conserva su recorte para compararla con la foto |
| Vista previa | `POST /api/v2/formulas/validar` (`{latex}` o `{texto}`) → PNG en base64, para corregir antes del PDF (FRONT-14) |

### Evaluación (`python -m herramientas.evaluar_formulas`)

| Muestra | Exactas | Fórmulas «reconocidas» incorrectas | Lo que no se reconoce |
|---------|---------|------------------------------------|-----------------------|
| `formulas_pizarron`: escritas **en línea** (`x^2 + 2x + 1 = 0`, `a/b + c/d`, `sqrt(x + 1)`, `E = m c^2`) | **3/4** (2 inciertas, 1 reconocida) | **0** | `E = m c^2` queda como recorte |
| `formulas_2d`: dibujadas en 2D (superíndice, barra de fracción, radical) | **0/4** | **0** | Las 4 se conservan como recorte |

**Limitación importante:** Tesseract es un OCR de texto, no matemático. Las fórmulas en 2D (fracciones con barra, radicales, superíndices pequeños) **no se convierten automáticamente**: se conservan como imagen con su ubicación y el usuario escribe el LaTeX con vista previa. Los motores de OCR matemático (pix2tex/LaTeX-OCR, ~100 MB con PyTorch; Mathpix, de pago y externo) no se adoptaron por tamaño y privacidad; se podrían añadir como un paso más para los recortes `incierto`.

## Apunte estructurado (BACK-19)

`app/services/estructura.py` convierte el documento editado en un apunte organizado
(portada, índice por títulos, secciones, resumen, conceptos clave, glosario, ejemplos,
fórmulas, tablas y esquemas). Es una función pura que se recalcula para cualquier
versión, así que regenerar nunca pierde contenido.

Regla de fidelidad, verificada en `tests/test_estructura.py`:

| Parte | De dónde sale | Lo que NO hace |
|-------|---------------|----------------|
| Secciones | Bloques de tipo `titulo` | No inventa títulos (sin títulos → una sección «Contenido») |
| Resumen | Hasta 3 frases **del apunte**, elegidas por frecuencia de términos | No redacta frases nuevas |
| Conceptos clave | Palabras que se repiten (≥ 2 veces, sin palabras vacías) | — |
| Glosario | Líneas «Concepto: definición» / «X es …» escritas en el apunte | No define nada que el apunte no defina |
| Tabla comparativa | Tablas del apunte, o el glosario si define ≥ 2 conceptos | No rellena celdas |
| Fórmulas | LaTeX solo si es válido; si no, el recorte | No presenta LaTeX inválido como bueno |
| Manuscrito ilegible | Se cuenta en `pendientes` y va como imagen, con aviso | No se transcribe |
| Complementos | Solo ampliaciones **aceptadas**, con su fuente | No se mezclan con el resumen |

Limitación conocida: el resumen es extractivo (no reescribe); en apuntes muy cortos
coincide con el texto completo.
