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
    └── services/           # Lógica reutilizable, sin dependencias de rutas
        ├── almacenamiento.py   # Guardado seguro de archivos subidos
        └── procesamiento.py    # Procesamiento con Pillow (escala de grises, ejemplo)
```

## Rutas disponibles

| Método | Ruta              | Descripción                                                     |
|--------|-------------------|-----------------------------------------------------------------|
| GET    | `/`               | Comprobación de estado. Responde `{"message": "Hola Mundo"}`.   |
| POST   | `/analisis`       | Recibe `file` (multipart), lo convierte a grises y lo devuelve. |
| POST   | `/imagen-memoria` | Devuelve una imagen PNG de ejemplo generada en memoria.         |

Las rutas y sus respuestas no cambiaron, por lo que `front/js/fastapi.js`
sigue funcionando contra `http://localhost:8000/analisis`.

## Variables de entorno

| Variable       | Por defecto                    | Uso                                                  |
|----------------|--------------------------------|------------------------------------------------------|
| `IMAGES_DIR`   | `imagenes` (relativo a esta carpeta) | Carpeta donde se guardan las imágenes recibidas. Se crea sola. |
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

## Cambios realizados (BACK-01)

- El código de `index.py` se separó en `core` (configuración), `routers` (rutas) y `services` (lógica).
- La ruta fija `/home/yane/imagenes` se reemplazó por la variable `IMAGES_DIR`; la carpeta se crea automáticamente.
- Los orígenes de CORS ahora son configurables con `CORS_ORIGINS`.
- El nombre del archivo subido se limpia para impedir escribir fuera de la carpeta de imágenes (`../../archivo`).
- Se eliminó la relectura/reescritura redundante con OpenCV (no modificaba la imagen); OpenCV sigue en las dependencias para las siguientes tareas.
- `print` se sustituyó por `logging`.
- Se completó `requirements.txt` (antes vacío) e incluye `python-multipart`, necesario para recibir archivos.
- Se añadió `.gitignore` para no subir `__pycache__`, entornos virtuales, `.env` ni las imágenes generadas, y se quitó el `.pyc` que estaba versionado.
