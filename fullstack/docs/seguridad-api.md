# Seguridad de la API v2 (BACK-24)

Guía de las protecciones de la API y de cómo comprobarlas. Las pruebas están en
`back/motori_magenes/tests/test_seguridad_api.py`; si una protección cambia, su prueba
debe cambiar en el mismo commit.

## 1. Autorización por propietario

- **Identidad:** la dependencia `sesion_actual` (o `usuario_actual`) de `app/core/seguridad.py`
  resuelve el usuario a partir de la cookie `apuntia_sesion` (HttpOnly, SameSite=Lax y
  `Secure` con `COOKIE_SEGURA=true`). En la base de datos solo se guarda el SHA-256 del token.
- **Regla:** toda consulta de un recurso privado (apunte, versión, archivo, trabajo,
  estructura y, más adelante, exportación o fuente) filtra en SQL por
  `usuario_id = <usuario de la sesión>`. Un identificador ajeno responde
  **`404 NO_ENCONTRADO`**, igual que uno inexistente, para no revelar qué ids existen.
- **Cobertura automática:** `test_todas_las_rutas_con_id_estan_cubiertas` compara las rutas
  `/api/v2/...{id}` de la especificación OpenAPI con la lista `RUTAS_CON_RECURSO`. Una
  ruta nueva sin su prueba de acceso cruzado hace fallar la suite.
- **Archivos:** solo se sirven desde `GET /api/v2/apuntes/{id}/archivos/{archivo_id}`. Se
  comprueba que el apunte es del usuario, que el archivo pertenece a ese apunte y que su
  ruta real queda dentro de `DATA_DIR/archivos/<usuario>/`. `DATA_DIR` nunca se monta como
  carpeta estática y no hay listado de directorios. Los nombres de archivo que envía el
  usuario solo se guardan como dato (saneados): las rutas en disco usan ids aleatorios.

## 2. CSRF, origen, CORS y cookies

| Protección | Dónde |
|------------|-------|
| `X-CSRF-Token` obligatorio en POST, PUT, PATCH y DELETE con sesión | `sesion_actual` → `403 CSRF_INVALIDO` |
| `Origin` de otro sitio rechazado (también en el registro y el inicio de sesión) | `comprobar_origen` → `403 ORIGEN_NO_PERMITIDO` |
| CORS **sin** `allow_credentials`: otro origen nunca recibe la cookie | `app/main.py` |
| Cookie HttpOnly, SameSite=Lax y Path=/; `Secure` y HSTS con `COOKIE_SEGURA=true` | `poner_cookie`, `CabecerasSeguridad` |

La interfaz con sesión se sirve **desde el mismo origen** que la API, así que no necesita CORS.

## 3. Cabeceras de seguridad (`app/core/endurecimiento.py`)

En todas las respuestas: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: no-referrer` y `Cross-Origin-Opener-Policy: same-origin`. En `/api/v2/`
se añaden además `Cache-Control: private, no-store` y
`Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; sandbox`: aunque un
texto del apunte contenga HTML, la respuesta es JSON y el navegador no ejecuta nada. La
interfaz debe mostrar ese texto con `textContent`, nunca con `innerHTML`.

## 4. Límites de abuso

| Límite | Valor por defecto | Error |
|--------|-------------------|-------|
| Cuerpo JSON | `MAX_JSON_KB` = 4096 KB | `413 CARGA_DEMASIADO_GRANDE` |
| Cuerpo multipart (fotos) | `MAX_UPLOAD_MB × MAX_PAGINAS` (+256 KB) | `413 CARGA_DEMASIADO_GRANDE` |
| Cada foto | `MAX_UPLOAD_MB` (10 MB) y `MAX_MEGAPIXELES` (50 MP); el tipo se decide por el contenido, no por la extensión | `400`/`413` de la validación v1 |
| Páginas por apunte | `MAX_PAGINAS` (20) | `400 DEMASIADAS_PAGINAS` |
| Espacio por usuario | `CUOTA_MB_USUARIO` (500 MB) | `413 CUOTA_EXCEDIDA` |
| Inicios de sesión fallidos | 5 por email y 20 por IP en 15 min | `429 DEMASIADOS_INTENTOS` |
| Registros | 10 por IP y hora (`MAX_REGISTROS_HORA`) | `429 DEMASIADAS_PETICIONES` |
| Recuperación de contraseña | 10 por IP y 3 por email cada hora | `429 DEMASIADAS_PETICIONES` |
| Apuntes nuevos | 30 por usuario y hora | `429 DEMASIADAS_PETICIONES` |
| Vistas previas de fórmulas | 120 por usuario y minuto | `429 DEMASIADAS_PETICIONES` |
| Trabajos activos | 3 por usuario; `MAX_TRABAJOS_SIMULTANEOS` (2) en el servidor | `429 DEMASIADOS_TRABAJOS` |

El límite del cuerpo se comprueba por `Content-Length` **antes** de leerlo y, si el cliente
envía el cuerpo por trozos, contando los bytes recibidos. Los contadores de frecuencia se
guardan en SQLite (tabla `intentos_login`, claves `lim:<acción>:<clave>`), así que valen con
varios hilos y sobreviven a un reinicio. Los emails se cuentan por su SHA-256.

## 5. Contenido no confiable

- **Fotos:** se decodifican con OpenCV/Pillow tras comprobar la firma del archivo; HTML,
  PDF o ejecutables con extensión `.png` se rechazan sin guardar nada.
- **LaTeX:** lista blanca de comandos y longitud máxima (`formulas.comprobar_seguridad`);
  se dibuja con mathtext de matplotlib, **sin** ejecutar TeX, así que `\input`, `\write18`
  o `\def` no se ejecutan: se rechazan con `400 LATEX_NO_PERMITIDO`.
- **Fórmulas en texto:** analizador propio de descenso recursivo, sin `eval`.
- **SSRF:** el servidor no descarga URLs que envíe el usuario. La investigación (BACK-18)
  solo consulta proveedores fijos y las fuentes guardadas deben ser `https://`.

## 6. Errores y registros sin fugas

- Los 5xx devuelven un mensaje genérico y `X-ApuntIA-Error-Id`; la traza solo va al log.
- Los logs identifican al usuario por su id, nunca por email, contraseña, token de sesión,
  token CSRF ni token de recuperación (`test_logs_sin_contrasenas_ni_tokens`).
- Los PDF y archivos privados se sirven con `Cache-Control: private, no-store`.

## 7. Borrado y temporales

- `DELETE /api/v2/apuntes/{id}` cancela sus trabajos y borra versiones, archivos y exportaciones.
- `DELETE /api/v2/perfil` (con contraseña) borra la cuenta, todas sus sesiones y la carpeta
  `DATA_DIR/archivos/<usuario>/`.
- Al cancelar un análisis se borran sus imágenes intermedias; al arrancar se limpian los
  temporales de escrituras interrumpidas (`Almacen.limpiar_temporales`).

## 8. Endpoint v1

`POST /analisis` no tiene sesión ni guarda nada en el servidor: procesa la imagen en
memoria y la devuelve (`test_v1_no_guarda_nada_en_el_servidor`). Conserva su contrato de
tamaño (`413 ARCHIVO_DEMASIADO_GRANDE`) y no da acceso a los datos de la v2.
