# Frontend – ApuntIA

## Archivos

| Archivo              | Uso                                                                                   |
|----------------------|---------------------------------------------------------------------------------------|
| `../index.html`      | **Pantalla principal real**, conectada al backend FastAPI.                             |
| `css/index.css`      | Sistema visual compartido: colores, tipografías, botones, pizarrón, tarjetas.         |
| `css/principal.css`  | Componentes propios de la pantalla principal: encabezado, zona de resultados, estados. |
| `js/config.js`       | Configuración: URL de la API, tiempo máximo y límites de los archivos.                |
| `js/api.js`          | Cliente de la API (FRONT-05): peticiones, cabeceras y errores, según `docs/api.md`.   |
| `js/mensajes.js`     | Catálogo de mensajes de error y validación para el usuario (FRONT-08).               |
| `js/validacion.js`   | Validación en el navegador (FRONT-02): firma binaria, tamaño y archivo vacío.       |
| `js/camara.js`       | Cámara en vivo con `getUserMedia` y alternativas (FRONT-03).                          |
| `js/api-mock.js`     | Respuestas simuladas para trabajar sin backend (`?mock=...`).                         |
| `js/app.js`          | Controlador de la pantalla principal: estados, vista previa y resultado.             |
| `maqueta.html` + `js/index.js` | Prototipo de UX con IA simulada, usado como referencia de diseño.            |

## Pantalla principal (FRONT-01)

Distribución, de arriba abajo:

1. **Encabezado** fijo con la marca y la navegación (Inicio · Cómo funciona · Resultados). La sección visible se marca con `aria-current`.
2. **Pizarrón** con las dos acciones principales: **Cargar imagen** y **Tomar foto**. Son `<label>` de inputs de archivo, así que funcionan con teclado y lector de pantalla. «Tomar foto» abre la cámara en el móvil con `capture="environment"`.
3. **Cómo funciona**: los 4 pasos del flujo.
4. **Zona de resultados**: el botón «Procesar imagen» y los paneles *Original* y *Procesada*.

Estados de la zona de resultados (atributo `data-estado` de `#estado`, que se anuncia con `role="status"`):

| Estado     | Cuándo                                     |
|------------|--------------------------------------------|
| `vacio`    | Al abrir la página; el botón está deshabilitado. |
| `listo`    | Ya hay una imagen elegida y se ve la vista previa. |
| `cargando` | Mientras se espera al servidor; la sección tiene `aria-busy="true"`. |
| `hecho`    | Se muestra la imagen procesada.            |
| `error`    | El servidor no respondió o devolvió un error. |

Accesibilidad básica: enlace «Saltar al contenido», contraste del sistema visual, foco visible, áreas táctiles de al menos 44 px, tema oscuro según el sistema y animaciones reducidas con `prefers-reduced-motion`.

En móvil (≤ 760 px), las acciones y los paneles se apilan en una sola columna y la navegación ocupa todo el ancho.

Los issues siguientes amplían esta base: cámara en vivo (FRONT-03), indicadores de carga (FRONT-07), mensajes de error (FRONT-08) y diseño adaptable fino (FRONT-09).

## Carga de imágenes desde el dispositivo (FRONT-02)

- **Control accesible:** «Cargar imagen» es un `<label>` del `<input type="file">`, con `aria-describedby` apuntando al texto de formatos admitidos. También se puede **arrastrar y soltar** una imagen sobre el pizarrón.
- **Tipos limitados sin confiar solo en ello:** `accept="image/jpeg,image/png,image/webp"` filtra el selector, pero `validacion.js` comprueba además la **firma binaria** de los primeros bytes. Así se rechaza, por ejemplo, un PDF o un HEIC renombrado como `.jpg`, igual que hace el backend.
- **Errores útiles:** archivo vacío, de más de 10 MB o de formato no admitido muestran un mensaje y **conservan la imagen anterior**, si había una.
- **Cancelación:** el evento `cancel` del selector, o un `change` sin archivo en navegadores antiguos, informa «No elegiste otra imagen. Se mantiene «x»» o, si no había ninguna, cómo empezar.
- **Estado:** `estado.archivo` guarda el `File` listo para `api.procesarImagen`, junto con su origen (`archivo`, `camara` o `arrastre`).
- **Sin envíos duplicados:** mientras se procesa, `estado.enviando` bloquea el botón y se ignoran nuevas selecciones; tres clics seguidos producen una sola petición.

## Captura con la cámara (FRONT-03)

«Tomar foto» elige el mejor método disponible:

| Situación | Comportamiento |
|-----------|----------------|
| `getUserMedia` disponible en contexto seguro (`https` o `localhost`) | Se abre un **visor en vivo** con la cámara trasera (`facingMode: environment`) y guías de encuadre. El botón de captura guarda un JPEG (`foto-AAAAMMDD-HHMMSS.jpg`) que pasa por la misma validación y vista previa que un archivo. |
| Contexto no seguro (`http://192.168.x.x` desde el celular) o navegador sin `getUserMedia` | Se usa `<input capture="environment">`, que abre la **app de cámara** del móvil (en un ordenador, el selector de archivos). |
| Permiso denegado | Explica cómo permitirlo en el navegador y ofrece «Usar la app de cámara» o «Cargar imagen». |
| Sin cámara, o cámara ocupada por otra app | Mensaje específico y las mismas alternativas. |

- La cámara **se apaga** (se detienen las pistas) al capturar, al cerrar con ✕ o al pulsar Esc.
- El visor muestra el video con `object-fit: contain`: lo que se ve es exactamente lo que se captura.
- Dentro del visor, «Elegir archivo» permite cambiar a la carga desde el dispositivo.

## Vista previa (FRONT-04)

- Se muestra en el panel *Original* con `object-fit: contain` y una altura máxima del 60 % de la pantalla, así **no se deforma ni desborda**, sea vertical u horizontal.
- Debajo aparecen el **archivo elegido**, su peso, sus dimensiones y su orientación (p. ej. `vert.jpg · 114 KB · 1500×4000 px (vertical)`).
- **Cambiar** abre de nuevo el selector y **Quitar** elimina la selección: se vacía la vista previa, se deshabilita «Procesar» y el foco vuelve a «Cargar imagen». Ambos botones se bloquean mientras se procesa.
- Usa `URL.createObjectURL` en lugar de leer la imagen como base64, que es más rápido y consume menos memoria, y **libera la URL temporal** (`revokeObjectURL`) al reemplazar o quitar la imagen.

## Resultado del procesamiento (FRONT-06)

- El panel *Procesada* recibe el **blob PNG** de la API (según el contrato) y lo muestra junto al *Original*, así se distinguen claramente.
- **Ver original:** mientras se mantiene pulsado (ratón, dedo, o Espacio/Enter con teclado), el panel del resultado muestra la imagen original en el mismo lugar, con la etiqueta «Original». No se usa un comparador superpuesto porque la corrección de perspectiva cambia el encuadre y las dimensiones, y las dos imágenes no coincidirían.
- **Datos:** si el pizarrón se enderezó o no (`X-ApuntIA-Perspectiva`), dimensiones, peso y tiempo de procesamiento. Los datos que falten se omiten.
- **Tamaño real** abre el PNG en una pestaña nueva para leer los detalles; **Descargar** usa el nombre de `Content-Disposition` (`<nombre>_apuntia.png`).
- **Resultado vacío o fallido:** una respuesta vacía, que no es imagen o que el navegador no puede decodificar se trata como un error (`RESPUESTA_INVALIDA`) y no deja acciones a medias. No hay resultados que caduquen, porque la API devuelve la imagen directamente (ver `docs/api.md`). La URL temporal del resultado se libera al elegir otra imagen o al volver a procesar.

## Indicadores de carga (FRONT-07)

| Momento | Qué ve el usuario |
|---------|-------------------|
| 0–2 s | Spinner y «Enviando la imagen al servidor…» |
| 2–8 s | «Procesando la imagen…» y un reloj con los segundos transcurridos |
| > 8 s | «Sigue procesando… Las fotos grandes pueden tardar un poco más.» |
| Al llegar | «Recibiendo el resultado…» y, a continuación, el resultado |

- **Sin porcentajes:** el backend no informa del progreso, así que no se inventan.
- **Accesible:** el mensaje está en una región `role="status"`. El spinner y el reloj son `aria-hidden`, así el lector de pantalla anuncia solo los cambios de fase y no cada segundo. La sección tiene `aria-busy="true"` mientras dura la espera.
- **Controles bloqueados durante la espera:** «Procesar» (que muestra «Procesando…»), «Cargar imagen», «Tomar foto», «Cambiar», «Quitar» y arrastrar y soltar.
- **Cancelar:** aborta la petición con un `AbortController`.
- **Restauración garantizada:** al terminar, fallar o cancelar, un bloque `finally` vuelve a habilitar todos los controles.

## Mensajes de error y validación (FRONT-08)

`front/js/mensajes.js` traduce cada código, sea del contrato de la API, de la validación, de la cámara o de la red, a un **mensaje público con una acción para resolverlo**:

| Situación | Código | Acciones ofrecidas |
|-----------|--------|--------------------|
| Tipo no admitido (incluido HEIC) | `TIPO_NO_PERMITIDO` | Elegir otra imagen |
| Tamaño excedido | `ARCHIVO_DEMASIADO_GRANDE` / `IMAGEN_DEMASIADO_GRANDE` | Elegir otra imagen |
| Archivo vacío o dañado | `ARCHIVO_VACIO` / `IMAGEN_CORRUPTA` | Elegir otra imagen |
| Sin archivo | `ARCHIVO_AUSENTE` | Cargar imagen · Tomar foto |
| Permiso de cámara denegado | `CAMARA_PERMISO_DENEGADO` | Usar la app de cámara · Cargar imagen |
| Sin cámara / cámara ocupada | `CAMARA_NO_DISPONIBLE` / `CAMARA_OCUPADA` | App de cámara o Tomar foto · Cargar imagen |
| Sin red / servidor apagado | `SIN_CONEXION` (con texto distinto si `navigator.onLine` es falso) | Reintentar |
| Tiempo agotado | `TIEMPO_AGOTADO` | Reintentar · Elegir otra imagen |
| Error del servidor | `ERROR_INTERNO` / `ERROR_PROCESAMIENTO` / cualquier 5xx | Reintentar (+ Elegir otra) |
| Resultado no mostrable | `RESPUESTA_INVALIDA` | Reintentar |
| Fallo de configuración o de la app | `PARAMETRO_INVALIDO`, `RUTA_NO_ENCONTRADA`… | Recargar / Reintentar |

**Mensajes públicos frente a técnicos:**
- El texto visible siempre sale del catálogo; el mensaje del servidor y la causa técnica no se muestran.
- El detalle técnico (`console.error`) solo va a la consola.
- Si hubo respuesta HTTP, se ofrece un desplegable «Detalles técnicos» con el código, el estado HTTP y la referencia `X-ApuntIA-Error-Id`, útil para buscar el fallo en el log del servidor. **Nunca** se muestran trazas.

## Cliente de la API (FRONT-05)

`front/js/api.js` expone `window.ApuntIA.api`:

| Función | Descripción |
|---------|-------------|
| `procesarImagen(archivo, opciones?, {signal?, timeoutMs?})` | `POST /analisis` en multipart con el campo `file`. `opciones` admite `perspectiva`, `ruido`, `mejorar` y `grises`. Devuelve `{blob, perspectiva, dimensiones, tiempoMs, archivoRecibido, nombreDescarga}`. |
| `obtenerSalud()` | `GET /salud`: estado y límites del servidor. |
| `urlBase()` | URL de la API en uso. |
| `ApiError` | Error tipado que lanzan todas las funciones. |

`ApiError` tiene `tipo` (`red`, `tiempo`, `cancelado`, `http` o `respuesta`), `codigo` (el del contrato, o `SIN_CONEXION`, `TIEMPO_AGOTADO`, `CANCELADO` o `RESPUESTA_INVALIDA`), `mensaje` (el del servidor), `status` y `errorId`.

**URL de la API**, sin rutas fijas de una computadora concreta. Por orden de prioridad:
1. El parámetro de la página `?api=http://192.168.1.20:8000`.
2. `apiUrl` en `config.js`.
3. El mismo host que la página, en el puerto 8000. Así funciona al abrir el archivo con doble clic (`localhost`) y desde el celular en la red local (`http://<ip-del-pc>:8000`).

**Sin backend:** añade `?mock=<escenario>` a la URL, por ejemplo `index.html?mock=ok`. Escenarios: `ok`, `ok-sin-perspectiva`, `lento`, `colgado`, `tipo` (415), `grande` (413), `corrupta` (400), `servidor` (500), `red` y `vacia`. El mock sustituye `fetch` solo para la API, así que se ejecuta el cliente real.

Son scripts clásicos (sin módulos ES) a propósito: los módulos no cargan desde `file://`, y el equipo abre `index.html` con doble clic.

## Cómo probarlo

Primero levanta el backend (ver `back/motori_magenes/README.md`):

```bash
cd back/motori_magenes && uvicorn main:app --reload
```

Después, en otra terminal y desde la raíz del repo:

```bash
python -m http.server 5500
```

Abre `http://localhost:5500/index.html`, elige una imagen y pulsa «Procesar imagen». La versión en escala de grises aparece en el panel *Procesada*.
