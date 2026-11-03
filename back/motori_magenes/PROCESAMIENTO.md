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
