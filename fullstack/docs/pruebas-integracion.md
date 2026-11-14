# Pruebas de integración frontend ↔ backend (FULL-07)

Interfaz real en Chromium contra FastAPI real (uvicorn), manejada como lo haría el usuario: elegir una imagen,
pulsar «Procesar» y leer lo que muestra la pantalla.

```bash
npm install
```

```bash
npx playwright install chromium
```

```bash
npm run test:integracion
```

- Las pruebas levantan **ellas mismas** los dos servicios en puertos libres ([`fullstack/tests/integracion/entorno.js`](../tests/integracion/entorno.js)). Si el backend está en un entorno virtual, indica su Python: `PYTHON=back/motori_magenes/.venv/bin/python npm run test:integracion` (en Windows, `.venv\Scripts\python.exe`).
- Los errores del servidor se provocan con [`fullstack/tests/integracion/app_con_fallos.py`](../tests/integracion/app_con_fallos.py): la misma app con un fallo inyectado mediante `APUNTIA_FALLO`, sin tocar el código de producción.
- Para guardar evidencias: `CAPTURAS=fullstack/docs/evidencias npm run test:integracion`.

## Escenarios y resultados

| ID | Escenario | Respuesta HTTP | Lo que ve el usuario | Tiempo | Resultado |
|----|-----------|----------------|----------------------|--------|-----------|
| I01 | Imagen válida (foto real 516×387) | 200 | «Listo: resultado de «image.png»…» y la imagen procesada | 1.2 s | ✅ |
| I02 | Pizarrón inclinado de 12 MP (4032×3024) | 200 | «✓ Pizarrón detectado y enderezado», lado ≤ 2000 px | 1.4 s | ✅ |
| I03 | Archivo inválido (PDF disfrazado), con la validación del navegador **desactivada** | 415 | «Ese archivo no es una imagen admitida…» · *Elegir otra imagen* · detalle `TIPO_NO_PERMITIDO · HTTP 415` | 0.9 s | ✅ |
| I04 | Archivo inválido con la validación normal | — (no se envía) | El mismo mensaje; «Procesar» deshabilitado | — | ✅ |
| I05 | Archivo de 11 MB (validación del navegador desactivada) | 413 | «La imagen pesa más de 10 MB…» | 0.5 s | ✅ |
| I06 | Backend apagado | sin respuesta | «No se pudo conectar con el servidor…» · *Reintentar*, sin resultado viejo | 0.9 s | ✅ |
| I06b | «Reintentar» con el backend activo | 200 | Resultado visible | — | ✅ |
| I07 | Error de procesamiento (`cv2.error` en el pipeline) | 500 | «No se pudo procesar esta imagen…» · *Reintentar* · *Elegir otra* · referencia del error; la traza solo en el log | 1.0 s | ✅ |
| I08 | Excepción no prevista en el servidor (`RuntimeError`) | 500 | «Ocurrió un problema en el servidor…» · *Reintentar* · referencia. Antes de FULL-08: ❌ «No se pudo conectar…» (defecto D1) | 1.0 s | ✅ (tras corregir D1) |
| I09 | Servidor lento (+3 s) | 200 | Spinner → «Procesando la imagen…» → resultado | 4.2 s | ✅ |

Además, la batería de compatibilidad ([`compatibilidad.md`](compatibilidad.md)) añade 10 pruebas. **Total: 19 de 19 correctas.** Antes de FULL-08 eran 18 correctas y 1 defecto registrado (D1).

Evidencias: [válida](evidencias/full-07-valida.jpg) · [sin red](evidencias/full-07-red.jpg) · [error de procesamiento](evidencias/full-07-error-procesamiento.jpg)

## Defectos registrados

### D1: un 500 por excepción no prevista llega al navegador como «sin conexión»

- **Severidad:** media. El usuario cree que el servidor está apagado y no hay forma de ver la referencia del error.
- **Capas:** backend (CORS) → navegador → frontend (mensaje).
- **Pasos para reproducirlo:**
  1. Desde `back/motori_magenes`, levanta un backend con un fallo inesperado:

     ```bash
     APUNTIA_FALLO=inesperado python -m uvicorn app_con_fallos:app --app-dir ../../fullstack/tests/integracion --port 8123
     ```

  2. Abre `index.html?api=http://localhost:8123`, elige cualquier imagen y pulsa «Procesar».
  3. **Esperado:** «Ocurrió un problema en el servidor…» con la referencia del error. **Obtenido:** «No se pudo conectar con el servidor de ApuntIA…».
  4. Comprobación sin navegador: `curl -D - -H "Origin: http://localhost:5500" -F "file=@../bd/img/image.png" http://localhost:8123/analisis` devuelve `500` y `x-apuntia-error-id`, pero **sin** `access-control-allow-origin`. Con `APUNTIA_FALLO=procesamiento`, el 500 sí lleva las cabeceras CORS.
- **Causa probable:** en Starlette, el manejador de `Exception` se ejecuta en `ServerErrorMiddleware`, que está **fuera** de `CORSMiddleware`; los manejadores de excepciones concretas (`ApiError`, `ProcesamientoError`) se ejecutan dentro.
- **Estado:** ✅ **cerrado en FULL-08**. Causa, solución y evidencia en [`incidencias.md`](incidencias.md#d1-un-500-por-excepción-no-prevista-llega-como-sin-conexión).
