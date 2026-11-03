# Compatibilidad de datos frontend ↔ backend (FULL-06)

Comparación de las **peticiones reales del navegador** y las **respuestas reales de FastAPI** con el contrato
([`api.md`](api.md)). Automatizada en [`tests/integracion/compatibilidad.test.js`](../tests/integracion/compatibilidad.test.js):

```bash
npm run test:integracion
```

La batería levanta uvicorn y el servidor estático por su cuenta; usa `PYTHON=ruta/al/python` si el backend está en un `.venv`.

## Lista de verificación

| Aspecto | Contrato | Comprobado en la petición o respuesta real | ✔ |
|---------|----------|---------------------------------------------|---|
| Método y ruta | `POST /analisis` | Capturado por un servidor de eco: `POST /analisis?ruido=mediana` | ✅ |
| Content-Type | `multipart/form-data` | `multipart/form-data; boundary=----WebKitFormBoundary…`, puesto por el navegador | ✅ |
| Nombre del campo | `file`, un solo campo | Una sola parte, `name="file"` | ✅ |
| Tipo de la parte | Tipo de la imagen | `Content-Type: image/png` | ✅ |
| Archivo | Bytes íntegros | El cuerpo contiene el archivo completo | ✅ |
| Codificación del nombre | UTF-8 | `pizarrón día 1.png` llega en UTF-8 y vuelve igual en `X-ApuntIA-Archivo` y en `Content-Disposition` | ✅ |
| Credenciales | Ninguna | Sin `Cookie`; respuesta sin `Allow-Credentials` | ✅ |
| Tipo de respuesta | `image/png` | El blob es `image/png` y el navegador lo decodifica | ✅ |
| Cabeceras | Legibles desde el navegador | `X-ApuntIA-*` y `Content-Disposition` legibles por CORS; `X-ApuntIA-Dimensiones` coincide con la imagen real | ✅ |
| CORS | Otro origen permitido | Puerto distinto (:5500 → :8000) y `file://` (origen `null`) | ✅ |
| Tamaño máximo | 10 MB, rechazo si es mayor | **Mismo borde en las dos capas:** 10 485 760 bytes se aceptan; 10 485 761 → cliente y servidor `ARCHIVO_DEMASIADO_GRANDE` (413) | ✅ |
| Formatos | Firma JPEG/PNG/WEBP | Lo que rechaza el cliente (PDF, GIF, vacío) lo rechaza el servidor **con el mismo código** | ✅ |
| Imágenes del navegador | JPEG/PNG/WEBP de `canvas.toBlob` (como la cámara) | Las tres aceptadas, 320×240 | ✅ |
| Transparencia | PNG con alfa | Aceptado (el backend lo pasa a BGR) | ✅ |
| Orientación EXIF | — | Foto de celular guardada a 400×200 con `Orientation=6`: el navegador la muestra a 200×400 y el backend devuelve **200×400**, la misma orientación | ✅ |
| Códigos de error | Tabla del contrato | Cada código del contrato y del backend tiene un mensaje en `front/js/mensajes.js` | ✅ |
| Límites | `GET /salud` es la fuente de verdad | Con `MAX_UPLOAD_MB=1` en el servidor, la interfaz valida y avisa con 1 MB | ✅ (tras la corrección C2) |

## Incompatibilidades encontradas

| # | Incompatibilidad | Capa | Estado | Responsable |
|---|------------------|------|--------|-------------|
| C1 | El navegador no podía leer las cabeceras `X-ApuntIA-*` (faltaba `Access-Control-Expose-Headers`) | Backend | ✅ Corregida en FULL-04 | Full / Back |
| C2 | Los límites (10 MB y formatos) estaban fijos en `front/js/config.js`: si se cambiaba `MAX_UPLOAD_MB` en el servidor, la interfaz validaba con el valor viejo y el texto de ayuda mentía | Frontend | ✅ **Corregida en este issue:** al cargar, `app.js` lee `GET /salud` y actualiza la configuración, el texto de ayuda y los mensajes | Front |
| C3 | El borde del tamaño podía diferir (MB decimales, redondeo) | Ambas | ✅ Verificado: el cliente usa la misma fórmula que el servidor, `floor(MB × 1024 × 1024)` | Front |
| C4 | Un nombre con comillas o saltos de línea (`a"b.png`) lo escapa **el navegador** como `a%22b.png` antes de enviarlo, así que `X-ApuntIA-Archivo` no coincide con el nombre local | Navegador | Registrada, no se corrige: es cosmético y solo se anota en la consola; la correspondencia imagen ↔ resultado se garantiza en el cliente (FULL-05) | — |
| C5 | Fotos HEIC de iPhone | Ambas | Registrada: fuera del alcance v1; las dos capas las rechazan con el mismo código y el mensaje explica cómo exportar a JPEG | Back |
