# Cuentas, historial y permisos (FULL-18)

Cómo se conectan identidad, almacenamiento e historial para que cada persona vea **solo lo suyo**
en todas las pantallas, ediciones y descargas. Detalle de la API en `fullstack/docs/api-v2.md` §4 y de las
protecciones en `fullstack/docs/seguridad-api.md`.

## 1. Matriz de permisos

| Acción | Sin sesión | Propietario | Otra cuenta |
|--------|-----------|-------------|-------------|
| `POST /analisis` (mejorar una foto, v1) | ✔ (no guarda nada) | ✔ | ✔ |
| Ver la ayuda y el estado de funciones | ✔ | ✔ | ✔ |
| Crear un apunte | 401 → iniciar sesión | ✔ | — |
| Listar y buscar apuntes | 401 | ✔ solo los suyos | ✔ solo los suyos (nunca los de otros) |
| Ver un apunte, su foto o sus recortes | 401 | ✔ | **404** |
| Editar, restaurar una versión | 401 | ✔ con `If-Match` + CSRF | **404** |
| Investigar, aceptar/descartar complementos | 401 | ✔ con permiso del perfil + consentimiento | **404** |
| Exportar y descargar el PDF | 401 | ✔ | **404** |
| Ver, cancelar o reintentar un trabajo | 401 | ✔ | **404** |
| Borrar un apunte | 401 | ✔ con confirmación | **404** |
| Perfil, contraseña, sesiones, borrar la cuenta | 401 | ✔ (lo propio) | — |

- **404 y no 403** para recursos ajenos: no se revela que un identificador existe.
- La autorización la decide **siempre el servidor** (filtro `usuario_id` en cada consulta); la
  interfaz solo oculta lo que no tiene sentido mostrar. No hay URL públicas: los archivos y PDF solo
  salen por rutas autenticadas, con `Cache-Control: private, no-store`.
- Las páginas privadas sin sesión llevan a `cuenta.html?volver=…` y, tras entrar, vuelven a la misma
  página. Si la sesión caduca en el editor con cambios sin guardar, la página no se abandona.

## 2. Sesiones

- Cookie `apuntia_sesion` HttpOnly, SameSite=Lax y Path=/ (Secure con `COOKIE_SEGURA=true`, es
  decir, detrás de HTTPS, p. ej. con el proxy de Docker). En la base de datos solo está su SHA-256.
- Caduca tras 12 h sin uso o 7 días en total. «Salir» la borra **en el servidor**: reutilizar la
  cookie antigua da 401. Cambiar la contraseña o restablecerla cierra las demás sesiones; también
  hay «Cerrar la sesión en los demás navegadores».
- CSRF: cabecera `X-CSRF-Token` (solo en memoria en la página) y comprobación de `Origin` en todo
  lo que modifica datos. La interfaz se sirve desde el mismo origen que la API, así que no hace
  falta CORS con credenciales.

## 3. Modos de ejecución

| Modo | Origen de la interfaz | Cookie | Notas |
|------|----------------------|--------|-------|
| Scripts locales (FULL-11) | `http://localhost:8000/inicio` | sin `Secure` (HTTP local) | `COOKIE_SEGURA=false` |
| Docker (FULL-13) | el del proxy | `Secure` si el proxy sirve HTTPS | `COOKIE_SEGURA=true` con HTTPS |
| `index.html` con doble clic | `file://` | — | Solo «Mejorar una foto»; los enlaces de cuenta llevan al servidor |

Los datos (SQLite + archivos) viven en `DATA_DIR`; persisten entre reinicios y entre modos si se
usa la misma carpeta.

## 4. Migración de datos existentes

La versión 1 no guardaba nada (cada foto se procesaba y se devolvía), así que **no hay apuntes sin
dueño** que migrar. Las migraciones de la base de datos (`app/datos/migraciones/`) crean las tablas
desde cero y conservan los datos en los cambios posteriores (p. ej. 0004 recrea `exportaciones`
asignando cada fila al dueño de su apunte, nunca a otra cuenta). Ver `fullstack/docs/datos.md`.

## 5. Evidencia

- `back/motori_magenes/tests/test_seguridad_api.py`: prueba IDOR de **cada** ruta con identificador
  (y una prueba que falla si se añade una ruta nueva sin cubrir), 401 sin sesión.
- `fullstack/tests/integracion/v2-permisos.test.js` (navegador + backend real): B recibe 404 al ver,
  editar, restaurar, exportar, descargar, consultar o cancelar trabajos y borrar lo de A, también
  desde su navegador; sin sesión, todas las páginas privadas piden entrar; tras **reiniciar el
  servidor** con los mismos datos, A conserva sus apuntes, su sesión y su PDF y B sigue sin verlos;
  la cookie de una sesión cerrada ya no sirve.
- `v2-apuntes.test.js`, `v2-cuenta.test.js`, `v2-perfil.test.js` y `v2-errores.test.js`: historial,
  sesiones caducadas, contraseñas y cambio de cuenta sin restos de la anterior.
