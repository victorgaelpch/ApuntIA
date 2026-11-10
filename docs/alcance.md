# Cumplimiento del alcance (rúbrica, punto 1: *Scope Definition*)

Objetivo: comprobar que el código entregado cubre el **100 % de los requerimientos del backlog** (los issues de
`victorgaelpch/ApuntIA`) y que **lo que no se pidió no está en el repositorio**, para evitar el *scope creep*.

## 1. Matriz de trazabilidad: requerimiento → código → prueba

Leyenda: ✅ cumplido y verificado · ⏳ depende de una persona o de un dispositivo real (no lo puede cerrar el código).

### Backend

| Issue | Requerimiento | Implementación | Prueba o evidencia | Estado |
|-------|---------------|----------------|--------------------|--------|
| BACK-01 #2 | Estructura del backend en módulos | `app/core`, `app/routers`, `app/services`, `main.py` | `tests/test_api.py` (todas las rutas responden) | ✅ |
| BACK-02 #3 | Carga y validación: archivo, tamaño, formato, decodificación | `app/services/validacion.py` | `test_sin_archivo`, `test_archivo_vacio`, `test_tipo_no_permitido_*`, `test_imagen_corrupta`, `test_archivo_demasiado_grande`, `test_demasiados_megapixeles` | ✅ |
| BACK-03 #4 | Pipeline de OpenCV reutilizable | `app/services/procesamiento.py` | `test_el_original_no_se_modifica`, `test_distintas_dimensiones_y_canales` | ✅ |
| BACK-04 #5 | Corrección de perspectiva | `app/services/perspectiva.py` | `test_precision_de_esquinas`, `test_detecta_pizarron_en_muestras`, `test_sin_cuadrilatero_fiable_no_detecta` · `docs/evidencias/back-04-perspectiva.jpg` | ✅ |
| BACK-05 #6 | Calidad y nitidez | `app/services/mejora.py` | `test_mejora_aumenta_contraste_en_foto_oscura` · `herramientas/evaluar_mejora.py` | ✅ |
| BACK-06 #7 | Eliminación de ruido configurable | `app/services/ruido.py` | `test_ruido_mejora_psnr_sin_borrar_texto`, `test_todos_los_filtros_de_ruido` | ✅ |
| BACK-07 #8 | Manejo de errores coherente | `app/core/errores.py` | `test_ruta_inexistente`, `test_metodo_no_permitido`, `test_parametro_invalido`, `test_error_*_sin_trazas`, `test_errores_500_llevan_cabeceras_cors` | ✅ |
| BACK-08 #9 | Pruebas de los endpoints | `tests/` | `python -m pytest` → 74 passed | ✅ |
| BACK-09 #10 | Optimizar el tiempo | `redimensionar()`, fondo a ¼ de resolución | `herramientas/benchmark.py`: 862 → 149 ms en 12 MP | ✅ |
| BACK-10 #11 | Documentar la instalación | `back/motori_magenes/README.md` | Instalación desde cero en un venv limpio → 70 passed (en ese momento) | ✅ |

### Frontend

| Issue | Requerimiento | Implementación | Prueba o evidencia | Estado |
|-------|---------------|----------------|--------------------|--------|
| FRONT-01 #12 | Interfaz principal | `index.html`, `front/css/principal.css` | C01, C14 · `docs/evidencias/front-10-inicio.jpg` | ✅ |
| FRONT-02 #13 | Carga desde el dispositivo | `front/js/validacion.js`, `app.js` | C02, C04, C05, C07 | ✅ |
| FRONT-03 #14 | Captura con la cámara | `front/js/camara.js` | C12, C13 | ✅ (⏳ en celular real) |
| FRONT-04 #15 | Vista previa | `app.js` (`mostrarPreview`) | C02, C03 | ✅ |
| FRONT-05 #16 | Cliente de la API | `front/js/api.js`, `config.js`, `api-mock.js` | C06–C11 (mock) · `compatibilidad.test.js` (real) | ✅ |
| FRONT-06 #17 | Mostrar el resultado | `app.js` (`mostrarResultado`) | C08 | ✅ |
| FRONT-07 #18 | Indicadores de carga | `app.js` (`enviarImagen`) | C06, C11 · I09 | ✅ |
| FRONT-08 #19 | Mensajes de error y validación | `front/js/mensajes.js` | C09 ×6, C10, C12 | ✅ |
| FRONT-09 #20 | Diseño adaptable | `front/css/principal.css` | C14, C15 · auditoría de 8 tamaños | ✅ |
| FRONT-10 #21 | Pruebas de la interfaz | `front/tests/interfaz.test.js` | `npm run test:front` → 20 passed | ✅ (⏳ Firefox/Safari) |

### Full stack

| Issue | Requerimiento | Implementación | Prueba o evidencia | Estado |
|-------|---------------|----------------|--------------------|--------|
| FULL-01 #22 | Flujo completo y alcance | `docs/flujo.md` | — | ✅ (⏳ acuerdo del equipo) |
| FULL-02 #23 | Coordinación de la integración | `docs/integracion.md` | — | ✅ (⏳ bitácoras) |
| FULL-03 #24 | Contrato de la API | `docs/api.md` | `compatibilidad.test.js` comprueba el contrato | ✅ (⏳ aprobación) |
| FULL-04 #25 | Integrar el frontend con FastAPI | CORS en `app/main.py`, `docs/ejecutar.md` | `test_cors_*` · I01–I09 | ✅ |
| FULL-05 #26 | Flujo de extremo a extremo | `app.js` (reintentos, correspondencia) | I01, I02, I06 | ✅ |
| FULL-06 #27 | Compatibilidad de datos | sincronización con `/salud` | `compatibilidad.test.js` → 10 passed | ✅ |
| FULL-07 #28 | Pruebas de integración | `fullstack/tests/integracion/flujo.test.js` | `npm run test:integracion` → 19 passed | ✅ |
| FULL-08 #29 | Errores entre capas | `CapturarErroresInesperados` | `docs/incidencias.md` · I08 | ✅ |
| FULL-09 #30 | Validación de la experiencia | `docs/validacion-ux.md` | Dispositivos emulados | ✅ (⏳ celulares reales) |
| FULL-10 #31 | Documentación de arquitectura | `docs/arquitectura.md`, `README.md` | 74 enlaces verificados | ✅ |

**Cobertura:** 30 de 30 issues implementados. Los ⏳ son tareas que el código no puede cerrar (aprobaciones, bitácoras, pruebas manuales en dispositivos) y están registradas en [`integracion.md`](integracion.md#4-bloqueos-y-riesgos).

## 2. Auditoría de lo que NO está en el backlog

Se revisó todo el repositorio buscando funcionalidades que ningún issue pide:

| Elemento | ¿Lo pide algún issue? | Decisión |
|----------|-----------------------|----------|
| `POST /imagen-memoria` (imagen de ejemplo) | No. Es código heredado anterior al backlog | **Conservado y marcado como obsoleto** (`deprecated` en `/docs`): BACK-01 exige que «las rutas existentes continúen respondiendo». Retirarlo requiere aprobación del equipo. |
| `front/maqueta.html` + `front/js/index.js` (biblioteca, favoritos, OCR e «IA» simulados) | No. Es un prototipo de diseño creado por el equipo antes del backlog | **No se borró:** es trabajo de otro integrante (regla de `integracion.md`: no modificar trabajo ajeno sin coordinarlo). No está enlazado desde la aplicación. **Pendiente de decisión del equipo:** retirarlo o moverlo a una carpeta de prototipos. |
| Parámetro `?grises=` | Sí, indirectamente: BACK-03 pide «convertir espacios de color cuando corresponda» | Conservado |
| Arrastrar y soltar una imagen | No explícitamente (FRONT-02 pide «control de archivo accesible») | Conservado como parte del mismo control (unas 25 líneas); se puede retirar sin afectar a nada más |
| `herramientas/` (muestras, benchmark, evaluaciones) | Sí: BACK-04/05/06 piden comparar y BACK-09 medir | Conservado |
| OCR, cuentas, historial, HEIC/PDF | Fuera de alcance según `flujo.md` | **No implementados** ✅ |

**Inconsistencia detectada:** la descripción del repositorio en GitHub dice «…mediante visión por computadora, **OCR e inteligencia artificial**. Reconoce texto, fórmulas y diagramas…», pero el OCR está explícitamente fuera del alcance v1. Hay que actualizarla desde *Settings → General → Description* (la interfaz ya se corrigió en FULL-09).
