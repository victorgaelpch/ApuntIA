# Interfaz v2: páginas con cuenta (FRONT-11 … FRONT-22)

## Cómo se sirve

Las páginas con cuenta usan la cookie de sesión HttpOnly de la API v2, que el navegador
solo envía a su propio origen. Por eso el backend sirve la interfaz (`app/routers/frontend.py`):

| URL | Contenido |
|-----|-----------|
| `/inicio` | `index.html`: mejorar una foto (PNG, sin cuenta) y presentación |
| `/front/ayuda.html` | Ayuda, privacidad y **estado real** de las funciones (según `GET /salud`) |
| `/front/cuenta.html` | Registro, inicio de sesión y recuperación (FRONT-17) |
| `/front/nuevo.html` | Crear un apunte con varias fotos (FRONT-12) |
| `/front/editor.html?id=…` | Revisar y corregir el apunte, investigar y exportar el PDF (FRONT-13 … 16, 22) |
| `/front/apuntes.html` | Mis apuntes (FRONT-18) |
| `/front/perfil.html` | Perfil y preferencias (FRONT-19) |

`GET /` sigue devolviendo `{"message": "Hola Mundo"}` (contrato v1). `index.html` también
funciona abierto con doble clic: entonces sus enlaces de cuenta apuntan al servidor de la API.
Solo se sirven HTML, CSS, JS e imágenes de `front/` (no `tests/` ni el README). Las páginas
llevan una CSP sin scripts ni estilos en línea (`script-src 'self'`).

## Navegación

Inicio · Crear apuntes · Mis apuntes · Perfil · Mejorar una foto · Ayuda. Los enlaces privados
solo aparecen con sesión (se consulta con `GET /api/v2/auth/estado`, que no da 401).

## Piezas comunes

- `front/js/v2/nucleo.js`: cliente `pedir()` (mismo origen, `X-CSRF-Token` solo en memoria),
  `h()` para crear elementos con `textContent` (nunca `innerHTML` con datos), avisos accesibles,
  diálogo de confirmación, espera de trabajos y cabecera según la sesión.
- `front/css/app.css`: tarjetas, formularios, avisos, pestañas, chips de estado y diálogos,
  sobre los tokens de `index.css`.

## Pruebas

`fullstack/tests/integracion/v2-*.test.js` abren las páginas en Chromium contra el backend real
(carpeta de datos temporal, investigación desactivada) — `npm run test:integracion`.

## Cuenta (FRONT-17)

- Pestañas accesibles (flechas ←/→) para iniciar sesión, crear cuenta y pedir el enlace de
  recuperación. Validación junto a cada campo (`aria-invalid`, mensaje enlazado) antes de
  enviar; el backend sigue siendo la autoridad.
- Las contraseñas se borran de los campos tras cada envío y nunca se guardan. La sesión es la
  cookie HttpOnly del servidor; el token CSRF solo vive en memoria.
- «Email ya usado» no confirma de quién es la cuenta: ofrece iniciar sesión o recuperarla.
- `?volver=` solo acepta rutas propias (`/front/…` o `/inicio`): sin redirecciones abiertas.
- El enlace de recuperación lleva el token en el fragmento (`#recuperar=…`), que no viaja al
  servidor ni en el Referer; la página lo quita de la barra al leerlo. Con `URL_PUBLICA`
  configurada, el enlace no depende de la cabecera `Host` de la petición.
- `?motivo=expirada` y `?motivo=salida` explican por qué se volvió a esta página.
- Decisión: la mejora de una foto (`/inicio`) **sigue sin cuenta**; solo los apuntes guardados
  la necesitan.

## Crear apuntes (FRONT-12)

- Añadir fotos desde el dispositivo (varias a la vez), arrastrándolas o con la cámara (el mismo
  visor que la página de inicio; sin cámara en vivo se usa la app de cámara del móvil).
- Cada foto muestra miniatura, número, nombre y tamaño, su tipo (Automático, Pizarrón o
  Cuaderno; «Automático» sugiere pizarrón para fotos oscuras y cuaderno para claras) y botones
  ↑ ↓ y Quitar; también se reordena arrastrando.
- Se valida con las reglas del backend y los límites de `GET /salud` (formato real, MB,
  megapíxeles y número de fotos). Las fotos repetidas (mismo contenido, SHA-256) no se añaden.
  Una foto inválida queda marcada y bloquea el envío hasta quitarla; los errores del servidor
  por página (`PAGINAS_INVALIDAS`) se muestran en su foto.
- Avisos locales de resolución baja o foto muy oscura (el análisis añade después los del servidor).
- Las fotos solo viven en memoria (las miniaturas son URL `blob:` que se liberan); al salir con
  fotos sin enviar el navegador pide confirmación.
- Envío con barra de progreso real, botón «Cancelar envío» y «Reintentar»; la cabecera
  `Idempotency-Key` hace que un reintento tras un corte no cree dos apuntes.
- Al aceptarse, se abre el editor del apunte, que muestra el avance del análisis.

## Editor: transcripción (FRONT-13)

- Mientras el análisis está en curso se muestra su etapa y progreso reales (`GET /api/v2/trabajos/{id}`),
  con «Cancelar análisis»; si falla o se cancela, el motivo y «Reintentar el análisis».
- Vista lado a lado: la foto procesada de cada página con las **regiones** de los bloques
  (posicionadas en % de `bbox`, así escalan con el ancho; amarillo = reconocido, naranja
  discontinuo = incierto, rojo punteado = sin leer) y la lista de bloques en orden de lectura.
  Pulsar una región enfoca su bloque y viceversa. «Ver la foto original» oculta las regiones,
  que están en coordenadas de la procesada.
- Cada bloque muestra estado y confianza, palabras dudosas, el recorte de la foto cuando es dudoso
  o manuscrito, y permite corregir el texto, cambiar el tipo, dividir (donde está el cursor),
  unir con el siguiente, subir/bajar, volver al texto reconocido, borrar (con «Deshacer») y
  conservar la imagen original en el PDF. Se pueden añadir textos y títulos a mano.
- Guardado explícito (botón o Ctrl+S) con `If-Match`: «Cambios sin guardar» → «Guardando…» →
  «Guardado · versión n · hh:mm» solo tras la respuesta del servidor. Un 409 no pisa nada:
  se ofrece ver la versión guardada, copiar los cambios o guardar encima.
- Si la sesión caduca, la página no se abandona: los cambios siguen en la pestaña y se pide
  iniciar sesión en otra. Al cerrar con cambios sin guardar, el navegador pide confirmación.
- Todo el texto se muestra con `value`/`textContent`: un `<script>` del OCR o del usuario es texto.

## Editor: fórmulas, tablas y esquemas (FRONT-14)

- **Fórmulas:** recorte de la foto junto al LaTeX reconocido, editable, con vista previa que dibuja
  el servidor (`POST /api/v2/formulas/validar`) con el mismo motor que el PDF. Se eligió frente a
  KaTeX/MathJax porque lo que se ve es lo que saldrá en el PDF, no hay que cargar scripts de un CDN
  (la CSP solo admite los propios) y el navegador nunca interpreta macros ni HTML: recibe un PNG.
  Errores de sintaxis y comandos no permitidos (`\input`, `\def`…) se explican junto al campo
  (`aria-invalid`); también se puede escribir en texto normal (`sqrt(x+1) + x^2`) y convertir.
  Si la fórmula no se puede dibujar, el PDF usa la imagen original; hay casilla para forzarlo.
- **Tablas:** edición de encabezados y celdas, añadir y quitar filas y columnas (hasta 500 × 30),
  con etiquetas accesibles por celda; «Convertir en tabla» pasa un texto con `|` o tabuladores a
  tabla. Las tablas anchas se desplazan dentro de su caja en el móvil.
- **Esquemas y dibujos:** se muestran y se exportan como la imagen original, con descripción
  opcional. ApuntIA no los redibuja para no inventar relaciones.
- Se pueden añadir fórmulas y tablas a mano. Todo se guarda con el mismo control de versiones.
