# Frontend – ApuntIA

## Archivos

| Archivo              | Uso                                                                                   |
|----------------------|---------------------------------------------------------------------------------------|
| `../index.html`      | **Pantalla principal real**, conectada al backend FastAPI.                             |
| `css/index.css`      | Sistema visual compartido: colores, tipografías, botones, pizarrón, tarjetas.         |
| `css/principal.css`  | Componentes propios de la pantalla principal: encabezado, zona de resultados, estados. |
| `js/config.js`       | Configuración: URL de la API, tiempo máximo y límites de los archivos.                |
| `js/api.js`          | Cliente de la API (FRONT-05): peticiones, cabeceras y errores, según `docs/api.md`.   |
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
