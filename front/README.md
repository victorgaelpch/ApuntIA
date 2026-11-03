# Frontend – ApuntIA

## Archivos

| Archivo              | Uso                                                                                   |
|----------------------|---------------------------------------------------------------------------------------|
| `../index.html`      | **Pantalla principal real**, conectada al backend FastAPI.                             |
| `css/index.css`      | Sistema visual compartido: colores, tipografías, botones, pizarrón, tarjetas.         |
| `css/principal.css`  | Componentes propios de la pantalla principal: encabezado, zona de resultados, estados. |
| `js/fastapi.js`      | Lógica de la pantalla principal: selección de imagen, vista previa y envío a la API.  |
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
