# Incidencias que involucran varias capas (FULL-08)

Cada incidencia incluye cómo se reprodujo, dónde se aisló la causa, la solución y la evidencia de la nueva prueba.
Los commits usan el prefijo del issue en el que se corrigieron.

| ID | Incidencia | Capas | Estado | Corregida en |
|----|-----------|-------|--------|--------------|
| D1 | Un 500 por excepción no prevista se mostraba como «sin conexión» | Backend → navegador → frontend | ✅ Cerrada | FULL-08 |
| C1 | El navegador no podía leer las cabeceras `X-ApuntIA-*` | Backend → navegador | ✅ Cerrada | FULL-04 |
| C2 | Límites de tamaño y formato desfasados entre la interfaz y el servidor | Frontend ↔ backend | ✅ Cerrada | FULL-06 |
| F1 | Resultado anterior visible durante un reintento o junto a un error | Frontend + flujo | ✅ Cerrada | FULL-05 |

---

## D1: un 500 por excepción no prevista llega como «sin conexión»

**Reproducción:** prueba I08 de `tests/integracion/flujo.test.js` y pasos manuales en [`pruebas-integracion.md`](pruebas-integracion.md#d1-un-500-por-excepción-no-prevista-llega-al-navegador-como-sin-conexión).

**Investigación por capa:**

| Capa | Qué se revisó | Observación |
|------|---------------|-------------|
| Consola del navegador | Mensajes al pulsar «Procesar» | `Access to fetch … has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header` |
| Petición HTTP | `curl -D - -H "Origin: …"` | El servidor **sí** responde `500` con `x-apuntia-error-id`, pero sin `access-control-allow-origin` |
| Log del servidor | Salida de uvicorn | `ERROR apuntia.errores: Error ERROR_INTERNO en POST /analisis (id=…)` con la traza: el manejador se ejecutó |
| Comparación | `APUNTIA_FALLO=procesamiento` | Ese 500 (`ProcesamientoError`) **sí** lleva CORS |

**Causa:** Starlette ejecuta el manejador registrado para `Exception` dentro de `ServerErrorMiddleware`, la capa más externa y **fuera de `CORSMiddleware`**. Los manejadores de excepciones concretas (`ApiError`, `ProcesamientoError`, `HTTPException`) se ejecutan en `ExceptionMiddleware`, dentro de CORS. Por eso solo fallaban las excepciones no previstas. El navegador descartaba la respuesta y `fetch` lo trataba como un fallo de red. La interfaz no tenía forma de distinguirlo.

**Solución:** `CapturarErroresInesperados` (`back/motori_magenes/app/core/errores.py`), un middleware ASGI registrado **antes** que CORS, de modo que queda dentro de él. Convierte cualquier excepción no prevista en el mismo 500 `ERROR_INTERNO`, con su id y el registro en el log. Si la respuesta ya había empezado a enviarse, vuelve a lanzar la excepción.

**Evidencia:**
- Prueba nueva `test_errores_500_llevan_cabeceras_cors` (backend): un `RuntimeError` y un `cv2.error` producen 500 con `access-control-allow-origin` y la cabecera del id expuesta.
- I08 (integración) pasa: el usuario ve «Ocurrió un problema en el servidor. Vuelve a intentarlo en unos momentos.» con *Reintentar* y la referencia.
- Con `curl`, tras la corrección:

  ```http
  HTTP/1.1 500 Internal Server Error
  x-apuntia-error-id: 746652cb84d7
  access-control-allow-origin: *
  access-control-expose-headers: Content-Disposition, X-ApuntIA-Archivo, …, X-ApuntIA-Error-Id
  ```

**Regresiones:** backend 74/74 · interfaz 20/20 · integración 19/19.

---

## C1: cabeceras `X-ApuntIA-*` no legibles desde el navegador

- **Reproducción:** con el cliente real contra uvicorn (FRONT-05), `perspectiva`, `dimensiones` y `archivoRecibido` llegaban como `null`; con `curl` las cabeceras estaban presentes.
- **Causa:** sin `Access-Control-Expose-Headers`, el navegador solo deja leer las cabeceras «simples» de una respuesta de otro origen.
- **Solución:** `expose_headers` en `CORSMiddleware` con la lista del contrato.
- **Evidencia:** `test_cors_expone_cabeceras_del_contrato` y la prueba de compatibilidad «la respuesta cumple el contrato y sus cabeceras son legibles».

## C2: límites desfasados entre la interfaz y el servidor

- **Reproducción:** con `MAX_UPLOAD_MB=1` en el servidor, la interfaz seguía aceptando 1.5 MB y decía «hasta 10 MB»; el servidor respondía 413.
- **Causa:** los límites estaban fijos en `front/js/config.js`.
- **Solución:** `app.js` lee `GET /salud` al cargar y actualiza la configuración, el texto de ayuda y los mensajes.
- **Evidencia:** prueba de compatibilidad «con MAX_UPLOAD_MB=1 en el backend, la interfaz valida y avisa con 1 MB».

## F1: resultado anterior visible durante un reintento o junto a un error

- **Reproducción:** procesar, provocar un error y reintentar: durante la espera, y junto al mensaje de error, seguía visible el resultado del envío anterior.
- **Causa:** el resultado solo se reemplazaba al llegar uno nuevo.
- **Solución:** el resultado se retira al empezar cada envío y la respuesta se descarta si la selección cambió.
- **Evidencia:** prueba I06 (después de un fallo, `resultadoVisible = false`) y la verificación de FULL-05.

---

## Observaciones que no son defectos de la aplicación

- **Apagado de uvicorn con `SIGTERM`:** espera a que se cierren las conexiones keep-alive abiertas por el navegador. Para simular una caída en las pruebas se usa `SIGKILL`.
- **Nombres de archivo con comillas:** el navegador los escapa (`%22`) antes de enviarlos (C4 en [`compatibilidad.md`](compatibilidad.md)).

## Fallos pendientes

No hay fallos abiertos de varias capas. Siguen abiertas las validaciones que requieren personas o dispositivos (Firefox, Safari y celulares reales: ver FULL-09).
