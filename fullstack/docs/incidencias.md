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

**Reproducción:** prueba I08 de `fullstack/tests/integracion/flujo.test.js` y pasos manuales en [`pruebas-integracion.md`](pruebas-integracion.md#d1-un-500-por-excepción-no-prevista-llega-al-navegador-como-sin-conexión).

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

No hay fallos abiertos de varias capas en la versión 1 (los de la versión 2, abajo). Siguen abiertas las validaciones que requieren personas o dispositivos (Firefox, Safari y celulares reales: ver FULL-09).

## Versión 2: defectos encontrados al preparar la entrega

Encontrados con la instalación desde un clon limpio (FULL-22), los escenarios de aceptación y la
inspección manual (FULL-24). Prioridad: **P1** impide usar o entregar · **P2** resultado incorrecto
con salida · **P3** detalle de presentación.

| Id | Defecto | Prioridad | Estado |
|----|---------|-----------|--------|
| D2 | El paquete `app/datos` no estaba en el repositorio | P1 | ✅ Corregido (`500acb7`) |
| D3 | Dos análisis simultáneos ~100 veces más lentos | P1 | ✅ Corregido (`d48cefe`) |
| D4 | Una tabla en la hoja se tomaba por el borde de la hoja; sus celdas no se leían | P2 | ✅ Corregido (`e695e38`) |
| D5 | Lo no transcrito del PDF se rotulaba siempre como «manuscrito» | P3 | ✅ Corregido (`bded4b4`) |
| D6 | «x²» se lee como «x?» y se marca como reconocido | P2 | ⏳ Abierto |
| D7 | En el móvil, la última pestaña del editor se ve cortada | P3 | ⏳ Abierto |

**D2. Un clon limpio no arranca.** Reproducir: `git clone` → `./iniciar.sh` → «ModuleNotFoundError:
No module named 'app.datos'». Causa: la regla `datos/` del `.gitignore` también ignoraba el paquete de
código. En el equipo de desarrollo el paquete existía, así que todas las pruebas pasaban.

**D3. Análisis simultáneos lentísimos.** Reproducir: con `iniciar.sh`, crear dos apuntes de 3 fotos a la
vez → 209 s (uno solo: 2 s). Causa: los hilos OpenMP de dos procesos de Tesseract compiten por los
núcleos. Arreglo: `OMP_THREAD_LIMIT=1` por defecto → 1,9 s.

**D4. Tablas fotografiadas.** Reproducir: `herramientas.corpus.tabla_cuaderno()` como apunte de
cuaderno → se perdía el título de encima de la tabla y se leían 0 de 8 celdas. Causa: la detección
de perspectiva tomaba la cuadrícula por el borde de la hoja, y la cuadrícula confundía a Tesseract.
Ahora: título y 7/8 celdas.

**D5. Rótulo falso en el PDF.** Reproducir: apunte con `formulas_pizarron()` → PDF → «E = m c^2» aparece
como «Fragmento manuscrito no transcrito». Ahora el rótulo depende del tipo de bloque.

**D6. Un superíndice mal leído pasa por seguro.** Reproducir: apunte con `impreso_cuaderno()` → el
bloque «Si f(x) = x?, entonces…» queda «reconocido» al 92 %. Es el único «reconocido con errores» del
banco de evaluación ([evaluacion.md](evaluacion.md)), donde se vigila para que no aumente. Arreglo
posible: marcar como incierta la palabra que contenga «?» pegado a una letra cuando Tesseract dé
alternativas, o reconocer superíndices con el detector de fórmulas. Mientras tanto: la foto está al
lado en el editor para corregirlo.

**D7. Pestañas del editor en el móvil.** Reproducir: abrir el editor a 412 px de ancho → «Versiones»
se ve cortada. La barra se desplaza y se llega con el teclado (no se pierde la función), pero no hay
indicio visual. Arreglo posible: sombra en el borde o pestañas en dos líneas.
