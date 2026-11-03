# Backend de ApuntIA: motor de imágenes (FastAPI + OpenCV)

API que recibe la foto de un pizarrón y la devuelve enderezada, sin ruido y más legible.

- **Contrato de la API** (rutas, campos, códigos de error): [`docs/api.md`](../../docs/api.md)
- **Detalles técnicos** del procesamiento (parámetros, mediciones, decisiones): [`PROCESAMIENTO.md`](PROCESAMIENTO.md)

---

## 1. Requisitos

| Herramienta | Versión | Comprobar con |
|-------------|---------|---------------|
| Python | **3.10 o superior** (probado con 3.13) | `python --version` |
| pip | El incluido con Python | `python -m pip --version` |
| Git | Cualquiera reciente | `git --version` |

> En Windows, al instalar Python marca la casilla **«Add python.exe to PATH»**. En macOS y Linux,
> puede que el comando se llame `python3` en lugar de `python`.

## 2. Instalación paso a paso

### 2.1 Clonar el repositorio y entrar en la carpeta del backend

```bash
git clone https://github.com/victorgaelpch/ApuntIA.git
```

```bash
cd ApuntIA/back/motori_magenes
```

Todos los comandos siguientes se ejecutan **desde `back/motori_magenes`**.

### 2.2 Crear el entorno virtual

```bash
python -m venv .venv
```

### 2.3 Activar el entorno virtual

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows (CMD):

```bat
.venv\Scripts\activate.bat
```

macOS y Linux:

```bash
source .venv/bin/activate
```

Cuando está activo, el indicador de la terminal empieza por `(.venv)`. Para salir, escribe `deactivate`.

### 2.4 Instalar las dependencias

```bash
python -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

| Paquete | Para qué se usa |
|---------|-----------------|
| `fastapi` | Framework de la API |
| `uvicorn[standard]` | Servidor ASGI |
| `python-multipart` | Recibir archivos con `multipart/form-data` (sin él, `/analisis` no arranca) |
| `opencv-python` | Procesamiento de imágenes |
| `numpy` | Matrices de las imágenes |
| `pillow` | Leer las dimensiones antes de decodificar e imagen de ejemplo |

Para desarrollar y ejecutar las pruebas, instala también `requirements-dev.txt` (añade `pytest` y `httpx`):

```bash
pip install -r requirements-dev.txt
```

### 2.5 Configurar las variables de entorno (opcional)

Los valores por defecto sirven para desarrollo. Para cambiarlos, copia la plantilla:

```bash
cp .env.example .env
```

(En Windows: `copy .env.example .env`.) El archivo `.env` está en `.gitignore`: **no lo subas al repositorio**.

| Variable | Por defecto | Uso |
|----------|-------------|-----|
| `MAX_UPLOAD_MB` | `10` | Tamaño máximo del archivo recibido |
| `MAX_MEGAPIXELES` | `50` | Resolución máxima de la imagen recibida |
| `MAX_LADO_PROCESAMIENTO` | `2000` | Lado mayor con el que se procesa; `0` = sin límite |
| `CORS_ORIGINS` | `*` | Orígenes permitidos, separados por comas (p. ej. `http://localhost:5500`) |
| `APP_NAME` | `ApuntIA - Motor de imágenes` | Título que aparece en `/docs` |

Las variables definidas en el sistema tienen prioridad sobre las del `.env`.

## 3. Ejecutar el servidor

```bash
uvicorn main:app --reload
```

- `main:app` es la instancia `app` del archivo `main.py`. `uvicorn index:app` también funciona, por compatibilidad.
- `--reload` reinicia el servidor al guardar cambios; quítalo en producción.
- Para otro puerto o para aceptar conexiones de otros dispositivos de la red (por ejemplo, probar desde el celular):

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Al arrancar verás `Uvicorn running on http://127.0.0.1:8000`. Para detenerlo: `Ctrl + C`.

| Dirección | Contenido |
|-----------|-----------|
| http://127.0.0.1:8000/salud | Estado y límites del servicio |
| http://127.0.0.1:8000/docs | Documentación interactiva (Swagger): permite probar `/analisis` desde el navegador |
| http://127.0.0.1:8000/redoc | Documentación alternativa |

## 4. Rutas

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Comprobación rápida: `{"message": "Hola Mundo"}` |
| `GET` | `/salud` | Estado, versión, formatos y límites |
| `POST` | `/analisis` | Procesa la foto enviada en el campo `file` y devuelve un PNG |
| `POST` | `/imagen-memoria` | PNG de ejemplo generado en memoria |

Parámetros opcionales de `/analisis`: `perspectiva` (bool), `ruido` (`ninguno`, `mediana`, `gaussiano`, `bilateral` o `combinado`), `mejorar` (bool) y `grises` (bool). El detalle está en [`docs/api.md`](../../docs/api.md).

## 5. Ejemplos de solicitud

Con la foto de ejemplo del repositorio (`back/bd/img/image.png`):

**curl** (Linux, macOS, Git Bash; en PowerShell usa `curl.exe`):

```bash
curl -X POST "http://127.0.0.1:8000/analisis" -F "file=@../bd/img/image.png" -o resultado.png -D -
```

Respuesta correcta (las cabeceras se muestran gracias a `-D -`):

```http
HTTP/1.1 200 OK
content-type: image/png
content-disposition: inline; filename*=UTF-8''image_apuntia.png
x-apuntia-archivo: image.png
x-apuntia-perspectiva: no_detectada
x-apuntia-dimensiones: 516x387
x-apuntia-tiempo-ms: 40
```

Con parámetros:

```bash
curl -X POST "http://127.0.0.1:8000/analisis?ruido=mediana&grises=true" -F "file=@../bd/img/image.png" -o resultado.png
```

**Python** (con `httpx`, incluido en `requirements-dev.txt`):

```python
import httpx

with open("../bd/img/image.png", "rb") as f:
    r = httpx.post("http://127.0.0.1:8000/analisis", files={"file": ("image.png", f, "image/png")})

if r.status_code == 200:
    open("resultado.png", "wb").write(r.content)
    print("Perspectiva:", r.headers["x-apuntia-perspectiva"])
else:
    print(r.status_code, r.json()["error"])
```

**Error** (archivo que no es una imagen):

```bash
curl -X POST "http://127.0.0.1:8000/analisis" -F "file=@README.md"
```

```json
{"error":{"codigo":"TIPO_NO_PERMITIDO","mensaje":"Formato no admitido. Usa una imagen JPEG, PNG o WEBP."}}
```

## 6. Pruebas

```bash
python -m pytest
```

Resultado esperado: `70 passed`. Las pruebas cubren todas las rutas, todos los errores del contrato y el pipeline (ver [`PROCESAMIENTO.md`](PROCESAMIENTO.md)).

Herramientas de medición (desde `back/motori_magenes`):

```bash
python -m herramientas.benchmark
```

```bash
python -m herramientas.evaluar_mejora
```

```bash
python -m herramientas.evaluar_ruido
```

```bash
python -m herramientas.muestras ../bd/muestras
```

El último comando guarda en `back/bd/muestras` las fotos sintéticas de prueba (inclinada, oscura, con sombra y con ruido).

## 7. Estructura

```
back/motori_magenes/
├── main.py                  # Punto de entrada: uvicorn main:app
├── index.py                 # Alias por compatibilidad (uvicorn index:app)
├── requirements.txt         # Dependencias de ejecución
├── requirements-dev.txt     # + pytest y httpx
├── .env.example             # Plantilla de variables de entorno
├── PROCESAMIENTO.md         # Detalles técnicos y mediciones
├── app/
│   ├── main.py              # create_app(): FastAPI, CORS, manejadores de error y routers
│   ├── core/
│   │   ├── config.py        # Configuración desde el entorno o .env
│   │   └── errores.py       # ApiError, ProcesamientoError y respuestas JSON de error
│   ├── routers/
│   │   ├── general.py       # GET /, GET /salud
│   │   └── imagenes.py      # POST /analisis, POST /imagen-memoria
│   └── services/            # Lógica sin dependencias de HTTP
│       ├── validacion.py    # Tamaño, formato real y decodificación
│       ├── procesamiento.py # Orquesta el pipeline y codifica el PNG
│       ├── perspectiva.py   # Detección y rectificación del pizarrón
│       ├── ruido.py         # Filtros de ruido
│       └── mejora.py        # Brillo, iluminación, CLAHE y enfoque
├── herramientas/            # Muestras sintéticas, benchmark y evaluaciones
└── tests/                   # Pruebas con pytest
```

## 8. Errores comunes

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `'python' no se reconoce como un comando` | Python no está en el PATH | Reinstala Python marcando «Add to PATH», o usa `py` (Windows) o `python3` (macOS/Linux). |
| `Activate.ps1 no se puede cargar porque la ejecución de scripts está deshabilitada` | Política de PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` o usa CMD. |
| `ModuleNotFoundError: No module named 'fastapi'` (o `cv2`) | El entorno virtual no está activo o faltan dependencias | Activa `.venv` y ejecuta `pip install -r requirements.txt`. |
| `Form data requires "python-multipart" to be installed` | Falta `python-multipart` | `pip install -r requirements.txt`. |
| `Error loading ASGI app. Could not import module "main"` | Uvicorn se ejecutó desde otra carpeta | Ejecútalo desde `back/motori_magenes`. |
| `[Errno 98] / [WinError 10048] address already in use` | El puerto 8000 está ocupado | Cierra el otro servidor o usa `--port 8001`; en ese caso, cambia también la URL de la API en el frontend. |
| `ImportError: libGL.so.1` (Linux sin entorno gráfico) | `opencv-python` necesita librerías gráficas | `pip uninstall opencv-python` y `pip install opencv-python-headless`. |
| El navegador muestra un error de CORS | El origen del frontend no está permitido | Añádelo a `CORS_ORIGINS` (o deja `*` en desarrollo) y reinicia uvicorn. |
| `413 ARCHIVO_DEMASIADO_GRANDE` | La foto pesa más de `MAX_UPLOAD_MB` | Usa una foto más ligera o sube el límite en `.env`. |
| `415 TIPO_NO_PERMITIDO` con fotos de iPhone | Formato HEIC | En el iPhone: Ajustes → Cámara → Formatos → «Más compatible» (JPEG), o exporta la foto como JPEG. |
| `X-ApuntIA-Perspectiva: no_detectada` | El pizarrón no tiene sus 4 esquinas visibles o se confunde con la pared | Encuadra el pizarrón completo con algo de margen. La imagen se mejora igualmente. |
