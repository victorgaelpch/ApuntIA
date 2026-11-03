# Flujo completo de ApuntIA (FULL-01)

Este documento traduce el objetivo de ApuntIA, convertir la foto de un pizarrón en una imagen
digital legible, en un recorrido técnico entre la **interfaz**, la **API** y el **procesamiento**.
Es la base para el contrato de la API ([`api.md`](api.md)) y para el resto de issues.

## Actores

| Actor | Rol |
|-------|-----|
| **Estudiante** (usuario) | Fotografía o elige la imagen del pizarrón, la revisa y obtiene el resultado. |
| **Interfaz web** (`index.html` + `front/js`) | Valida la selección, muestra la vista previa, envía la imagen y presenta el resultado o los errores. |
| **API FastAPI** (`back/motori_magenes`) | Valida la petición, ejecuta el procesamiento y responde con la imagen o con un error estructurado. |
| **Motor de procesamiento** (OpenCV) | Decodifica, corrige perspectiva, elimina ruido, mejora contraste y nitidez, y codifica el resultado. |

## Recorrido normal

```mermaid
sequenceDiagram
    actor U as Estudiante
    participant F as Interfaz web
    participant A as API FastAPI
    participant P as Motor OpenCV
    U->>F: 1. «Cargar imagen» o «Tomar foto»
    F->>F: 2. Valida tipo y tamaño, muestra vista previa
    U->>F: 3. «Procesar imagen»
    F->>A: 4. POST /analisis (multipart, campo "file")
    A->>A: 5. Valida presencia, tamaño, formato y decodificación
    A->>P: 6. Pipeline: redimensionar → perspectiva → ruido → mejora
    P-->>A: 7. Imagen procesada (PNG en memoria)
    A-->>F: 8. 200 image/png + cabeceras de metadatos
    F-->>U: 9. Muestra original y procesada, permite comparar y descargar
```

| Paso | Entrada | Salida | Restricciones |
|------|---------|--------|---------------|
| 1. Elegir imagen | Archivo del dispositivo o foto de la cámara | `File` en memoria del navegador | Cámara solo en contexto seguro (`https` o `localhost`) y con permiso del usuario |
| 2. Validar en el cliente | `File` | Vista previa o mensaje de error | JPEG, PNG o WEBP; máximo 10 MB. Es una ayuda: el backend vuelve a validar todo |
| 3. Confirmar | Clic | Petición en curso | Un envío a la vez: los botones se bloquean |
| 4. Enviar | `multipart/form-data`, campo `file` | Petición HTTP | URL base configurable, sin rutas fijas de una computadora |
| 5. Validar en el servidor | Bytes del archivo | Imagen decodificada o error 4xx | Rechaza archivo ausente, vacío, demasiado grande, de tipo no permitido o corrupto |
| 6. Procesar | Matriz OpenCV | Matriz procesada | El original no se modifica. Si no se detecta el pizarrón, se continúa sin corregir la perspectiva |
| 7–8. Responder | Matriz procesada | `image/png` y cabeceras `X-ApuntIA-*` | Nada se guarda en disco |
| 9. Mostrar | `Blob` | Comparación original/procesada y descarga | Se liberan las URLs temporales |

## Casos de error

| Caso | Dónde se detecta | Respuesta esperada |
|------|------------------|--------------------|
| No se elige archivo o se cancela el selector | Interfaz | Se conserva la selección anterior; sin selección, «Procesar» queda deshabilitado |
| Tipo no admitido (PDF, HEIC, etc.) | Interfaz y API (`415`) | Mensaje con los formatos aceptados y opción de elegir otra imagen |
| Archivo demasiado grande | Interfaz y API (`413`) | Mensaje con el límite y opción de elegir otra imagen |
| Archivo vacío o corrupto | API (`400`) | Mensaje «la imagen no se pudo leer» y opción de elegir otra |
| Permiso de cámara denegado o sin cámara | Interfaz | Explicación y alternativa «Cargar imagen» |
| Servidor apagado o sin red | Interfaz (fallo de `fetch`) | Mensaje de conexión y botón «Reintentar» |
| Tiempo de espera agotado | Interfaz (60 s) | Mensaje y botón «Reintentar» |
| Pizarrón no detectado | Motor | No es un error: se devuelve la imagen mejorada sin corregir la perspectiva y la interfaz lo indica |
| Fallo inesperado del procesamiento | API (`500`) | Mensaje genérico sin trazas técnicas; el detalle queda en el log del servidor |

## Alcance de la primera versión

**Incluye:**
- Carga desde el dispositivo y captura con cámara (en vivo con `getUserMedia`, con `capture` como alternativa).
- Vista previa, procesamiento con OpenCV (perspectiva, ruido, contraste y nitidez) y comparación antes/después con descarga.
- Validación y mensajes de error en las dos capas.
- Diseño para móvil y escritorio.
- Pruebas automáticas de backend, interfaz e integración, y documentación.

**Queda fuera** (posibles versiones futuras): reconocimiento de texto (OCR), cuentas de usuario, historial guardado en el servidor, procesamiento por lotes y formatos HEIC/PDF.

La maqueta `front/maqueta.html` (biblioteca de apuntes, IA simulada) es una referencia de diseño y no forma parte de esta versión.

## Actividades relacionadas y dependencias

```mermaid
flowchart LR
    F1[FULL-01 Flujo] --> F3[FULL-03 Contrato API]
    F3 --> B2[BACK-02 Validación] --> B7[BACK-07 Errores]
    B2 --> B3[BACK-03 Pipeline OpenCV]
    B3 --> B4[BACK-04 Perspectiva] & B5[BACK-05 Nitidez] & B6[BACK-06 Ruido]
    B4 & B5 & B6 --> B9[BACK-09 Optimización]
    B7 & B9 --> B8[BACK-08 Pruebas] --> B10[BACK-10 Docs backend]
    F3 --> R5[FRONT-05 Cliente API]
    R1[FRONT-01 Interfaz] --> R2[FRONT-02 Carga] --> R4[FRONT-04 Vista previa]
    R1 --> R3[FRONT-03 Cámara]
    R5 --> R6[FRONT-06 Resultado] & R7[FRONT-07 Carga] & R8[FRONT-08 Errores]
    R1 --> R9[FRONT-09 Responsivo]
    R6 & R7 & R8 & R9 --> R10[FRONT-10 Pruebas UI]
    R5 & B2 --> F4[FULL-04 Integración] --> F5[FULL-05 Flujo completo]
    F3 --> F6[FULL-06 Compatibilidad]
    F4 --> F7[FULL-07 Pruebas integración] --> F8[FULL-08 Errores multicapa] --> F9[FULL-09 Validación UX]
    F1 --> F2[FULL-02 Coordinación]
    F9 --> F10[FULL-10 Arquitectura]
```

## Criterios de entrega

- El usuario completa el recorrido «elegir o tomar foto → procesar → ver resultado» sin pasos manuales externos.
- Cada error de la tabla anterior produce un mensaje visible, entendible y con una acción para resolverlo.
- Las pruebas automáticas de backend (`pytest`), interfaz e integración pasan.
- La documentación permite levantar las dos partes desde cero.

> **Pendiente del equipo:** este flujo es una propuesta. Debe revisarse y acordarse en el issue (FULL-01 pide un «flujo acordado por el equipo»).
