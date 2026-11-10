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
