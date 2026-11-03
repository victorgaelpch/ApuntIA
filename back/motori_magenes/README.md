# Backend – Motor de imágenes (FastAPI)

## Estructura

```
back/motori_magenes/
├── main.py                 # Punto de entrada: uvicorn main:app --reload
├── index.py                # Compatibilidad con el antiguo "uvicorn index:app"
├── requirements.txt        # Dependencias del backend
├── .env.example            # Plantilla de variables de entorno (copiar a .env)
└── app/
    ├── main.py             # create_app(): instancia FastAPI, CORS y routers
    ├── core/
    │   └── config.py       # Configuración leída de variables de entorno / .env
    ├── routers/            # Rutas HTTP (solo reciben y responden)
    │   ├── general.py      # GET  /
    │   └── imagenes.py     # POST /analisis, POST /imagen-memoria
    ├── core/errores.py     # ApiError y respuesta JSON de error común
    └── services/           # Lógica reutilizable, sin dependencias de rutas
        ├── validacion.py       # Validación de la imagen recibida (BACK-02)
        └── procesamiento.py    # Procesamiento de imágenes
```

## Rutas disponibles

| Método | Ruta              | Descripción                                                     |
|--------|-------------------|-----------------------------------------------------------------|
| GET    | `/`               | Comprobación de estado. Responde `{"message": "Hola Mundo"}`.   |
| GET    | `/salud`          | Estado del servicio, versión y límites vigentes.                |
| POST   | `/analisis`       | Recibe `file` (multipart), lo valida y lo devuelve procesado.   |
| POST   | `/imagen-memoria` | Devuelve una imagen PNG de ejemplo generada en memoria.         |

Las rutas y sus respuestas no cambiaron, por lo que `front/js/fastapi.js`
sigue funcionando contra `http://localhost:8000/analisis`.

## Variables de entorno

| Variable       | Por defecto                    | Uso                                                  |
|----------------|--------------------------------|------------------------------------------------------|
| `MAX_UPLOAD_MB` | `10`                          | Tamaño máximo del archivo recibido.                  |
| `MAX_MEGAPIXELES` | `50`                        | Resolución máxima de la imagen recibida.             |
| `CORS_ORIGINS` | `*`                            | Orígenes permitidos, separados por comas.            |
| `APP_NAME`     | `ApuntIA - Motor de imágenes`  | Título mostrado en `/docs`.                          |

```bash
cp .env.example .env
```

## Ejecución

```bash
pip install -r requirements.txt
```

```bash
uvicorn main:app --reload
```

## Cómo comprobarlo

```bash
curl http://127.0.0.1:8000/
```

```bash
curl -X POST -F "file=@../bd/img/image.png" http://127.0.0.1:8000/analisis -o resultado.png
```

También puede probarse desde `http://127.0.0.1:8000/docs`.

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

## Cambios realizados (BACK-01)

- El código de `index.py` se separó en `core` (configuración), `routers` (rutas) y `services` (lógica).
- La ruta fija `/home/yane/imagenes` se reemplazó por la variable `IMAGES_DIR`; la carpeta se crea automáticamente.
- Los orígenes de CORS ahora son configurables con `CORS_ORIGINS`.
- El nombre del archivo subido se limpia para impedir escribir fuera de la carpeta de imágenes (`../../archivo`).
- Se eliminó la relectura/reescritura redundante con OpenCV (no modificaba la imagen); OpenCV sigue en las dependencias para las siguientes tareas.
- `print` se sustituyó por `logging`.
- Se completó `requirements.txt` (antes vacío) e incluye `python-multipart`, necesario para recibir archivos.
- Se añadió `.gitignore` para no subir `__pycache__`, entornos virtuales, `.env` ni las imágenes generadas, y se quitó el `.pyc` que estaba versionado.
