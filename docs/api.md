# Contrato de la API de ApuntIA (FULL-03)

Versión del contrato: **1.0**. URL base por defecto en desarrollo: `http://localhost:8000`.
La documentación interactiva generada por FastAPI está en `/docs` (Swagger) y en `/redoc`.

Este contrato es la referencia común para backend y frontend. Si cambia, hay que actualizar este
archivo **en el mismo PR** que el código.

---

## `POST /analisis`: procesar una foto del pizarrón

### Solicitud

- **Content-Type:** `multipart/form-data`
- **Campo de archivo:** `file` (obligatorio, un solo archivo)
- **Formatos permitidos:** JPEG, PNG y WEBP. Se comprueba **el contenido real** del archivo; la
  extensión y el `Content-Type` que envía el navegador no bastan.
- **Tamaño máximo:** 10 MB (variable `MAX_UPLOAD_MB`) y 50 megapíxeles (variable `MAX_MEGAPIXELES`).

**Parámetros opcionales de consulta (query):**

| Parámetro     | Tipo | Por defecto | Valores | Efecto |
|---------------|------|-------------|---------|--------|
| `perspectiva` | bool | `true` | `true` / `false` | Detecta el pizarrón y endereza la foto. |
| `ruido`       | texto | `combinado` | `ninguno`, `mediana`, `gaussiano`, `bilateral`, `combinado` | Filtro para eliminar ruido. `combinado` = mediana + bilateral (ver BACK-06). |
| `mejorar`     | bool | `true` | `true` / `false` | Ajusta el contraste local (CLAHE) y aplica un enfoque moderado. |
| `grises`      | bool | `false` | `true` / `false` | Devuelve el resultado en escala de grises. |

Ejemplo:

```bash
curl -X POST "http://localhost:8000/analisis?ruido=mediana" -F "file=@pizarron.jpg" -o resultado.png -D -
```

### Respuesta correcta: `200 OK`

- **Cuerpo:** la imagen procesada en binario.
- **Content-Type:** `image/png` (sin pérdida, para conservar los trazos finos).

| Cabecera | Ejemplo | Significado |
|----------|---------|-------------|
| `Content-Disposition` | `inline; filename="pizarron_apuntia.png"` | Nombre sugerido para descargar. |
| `X-ApuntIA-Perspectiva` | `corregida` | `corregida`, `no_detectada` o `desactivada`. |
| `X-ApuntIA-Dimensiones` | `1600x1200` | Ancho×alto del resultado en píxeles. |
| `X-ApuntIA-Tiempo-Ms` | `184` | Tiempo de procesamiento en el servidor. |
| `X-ApuntIA-Archivo` | `pizarr%C3%B3n.jpg` | Nombre del archivo recibido, codificado como URL. Sirve para comprobar que el resultado corresponde a la imagen enviada. |

Estas cabeceras se exponen por CORS (`Access-Control-Expose-Headers`) para que el navegador
pueda leerlas. Que no se detecte el pizarrón **no es un error**: la respuesta es `200` con
`X-ApuntIA-Perspectiva: no_detectada`.

El resultado se devuelve directamente en la respuesta y **no se guarda en el servidor**. No
hay URL de recuperación posterior ni resultados que caduquen: si el cliente lo necesita de
nuevo, vuelve a enviar la imagen.

### Respuestas de error

Todos los errores, incluidos los 404 y 500, tienen **la misma estructura JSON**:

```json
{
  "error": {
    "codigo": "TIPO_NO_PERMITIDO",
    "mensaje": "Formato no admitido. Usa una imagen JPEG, PNG o WEBP."
  }
}
```

- `codigo`: identificador estable en MAYÚSCULAS. El frontend decide qué mostrar según este valor.
- `mensaje`: texto en español apto para el usuario. **Nunca** incluye trazas ni rutas internas.
- En los errores `500`, la cabecera `X-ApuntIA-Error-Id` trae un identificador que también aparece
  en el log del servidor, junto a la traza completa, para poder investigar el fallo.

| HTTP | `codigo` | Cuándo |
|------|----------|--------|
| 400 | `ARCHIVO_AUSENTE` | La petición no incluye el campo `file`. |
| 400 | `ARCHIVO_VACIO` | El archivo tiene 0 bytes. |
| 400 | `IMAGEN_CORRUPTA` | La firma es de una imagen permitida, pero no se puede decodificar. |
| 413 | `ARCHIVO_DEMASIADO_GRANDE` | El archivo supera `MAX_UPLOAD_MB`. |
| 413 | `IMAGEN_DEMASIADO_GRANDE` | La imagen supera `MAX_MEGAPIXELES`. |
| 415 | `TIPO_NO_PERMITIDO` | El contenido no es JPEG, PNG ni WEBP. |
| 422 | `PARAMETRO_INVALIDO` | Un parámetro de consulta tiene un valor no válido (por ejemplo `ruido=xyz`). |
| 404 | `RUTA_NO_ENCONTRADA` | La ruta no existe. |
| 405 | `METODO_NO_PERMITIDO` | El método HTTP no está permitido en la ruta. |
| 500 | `ERROR_PROCESAMIENTO` | Fallo dentro del pipeline de OpenCV. |
| 500 | `ERROR_INTERNO` | Cualquier otro fallo inesperado. |

Ejemplos:

```http
HTTP/1.1 415 Unsupported Media Type
Content-Type: application/json

{"error": {"codigo": "TIPO_NO_PERMITIDO", "mensaje": "Formato no admitido. Usa una imagen JPEG, PNG o WEBP."}}
```

```http
HTTP/1.1 413 Content Too Large
Content-Type: application/json

{"error": {"codigo": "ARCHIVO_DEMASIADO_GRANDE", "mensaje": "La imagen pesa más de 10 MB. Elige una más ligera."}}
```

---

## `GET /salud`: estado y límites del servicio

El frontend lo usa para saber si el servidor está activo y para conocer los límites vigentes.

```json
{
  "estado": "ok",
  "version": "1.0.0",
  "formatos": ["image/jpeg", "image/png", "image/webp"],
  "max_mb": 10,
  "max_megapixeles": 50
}
```

---

## Rutas heredadas

| Ruta | Estado |
|------|--------|
| `GET /` | Se conserva: responde `{"message": "Hola Mundo"}`. |
| `POST /imagen-memoria` | Se conserva como ejemplo: devuelve un PNG de prueba generado en memoria. |

---

## CORS

- Orígenes permitidos: variable `CORS_ORIGINS` (por defecto `*` en desarrollo).
- Métodos: `GET`, `POST`.
- Cabeceras expuestas: `Content-Disposition`, `X-ApuntIA-Archivo`, `X-ApuntIA-Perspectiva`,
  `X-ApuntIA-Dimensiones`, `X-ApuntIA-Tiempo-Ms` y `X-ApuntIA-Error-Id`.
- El cliente no envía credenciales ni cookies.

## Validación en el cliente

El frontend replica los límites (formatos y 10 MB) **solo para avisar antes al usuario**.
El backend es la fuente de verdad: al cargar, el cliente lee `GET /salud` y usa esos límites (FULL-06).
El borde es el mismo en las dos capas: se rechaza si `tamaño > floor(MAX_UPLOAD_MB × 1024 × 1024)`.

> **Pendiente del equipo:** los responsables de backend y frontend deben revisar y aprobar este
> contrato en el issue FULL-03.
