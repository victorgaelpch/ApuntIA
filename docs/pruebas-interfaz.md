# Pruebas de la interfaz (FRONT-21)

Cómo se prueba la interfaz, qué cubre cada suite y en qué condiciones se ha comprobado.
Todas usan datos sintéticos (fotos generadas en el navegador, cuentas `@example.com`), una
carpeta de datos temporal por backend que se borra al terminar y ninguna cuenta ni clave real.

## 1. Suites

| Suite | Comando | Backend | Qué cubre |
|-------|---------|---------|-----------|
| `front/tests/interfaz.test.js` | `npm run test:front` | **Simulado** (`api-mock.js`, reproducible) | Página de inicio v1: carga, cámara simulada, validación, comparación, PNG, errores, responsive (20 casos) |
| `front/tests/catalogo.test.js` | `npm run test:front` | Ninguno (Node) | Catálogo de mensajes completo y reglas de seguridad del código de la interfaz (9 casos) |
| `fullstack/tests/integracion/flujo.test.js`, `compatibilidad.test.js` | `npm run test:integracion` | **Real** (uvicorn) | Contrato v1 de extremo a extremo |
| `fullstack/tests/integracion/v2-*.test.js` | `npm run test:v2` | **Real**, con OCR Tesseract | Páginas con cuenta (abajo) |
| `v2-accesibilidad.test.js` | `npm run test:a11y` | Real | Accesibilidad y responsive de todas las pantallas |

Las suites con backend real se ejecutan **una a una** (`--test-concurrency=1`): varios backends
con OCR en paralelo saturan la CPU. La investigación usa una Wikipedia simulada
(`app_wikipedia_simulada.py`) y la maquetación lenta del PDF, `app_pdf_lento.py`: en ambos el
backend y el proveedor son los reales y solo se sustituye la red o se añade una espera.
Nunca se llama a servicios externos ni a OCR en la nube.

### Inventario v2 (backend real)

| Archivo | Casos | Recorrido |
|---------|------:|-----------|
| `v2-recorrido` | 1 | Registro → 2 fotos → análisis → corrección → fórmula y tabla → complemento citado → PDF descargado y leído con `pdftotext` → Mis apuntes → salir |
| `v2-navegacion` | 5 | Navegación con y sin sesión, ayuda con el estado real, PNG desde `/inicio`, cabeceras, teclado y anchos |
| `v2-cuenta` | 7 | Registro, inicio y cierre de sesión, recuperación con el buzón, sesión caducada, almacenamiento sin secretos |
| `v2-nuevo` | 6 | Varias fotos: añadir, sugerir tipo, reordenar, quitar, duplicados, inválidas, red cortada, cancelar, cámara simulada |
| `v2-editor` | 10 | Regiones y bloques, correcciones, XSS, dividir/unir, conflicto entre pestañas, sesión caducada, manuscrito |
| `v2-contenido` | 5 | Fórmulas, tabla 3×4 hasta el PDF, texto a tabla, esquema como imagen |
| `v2-versiones` | 5 | Guardado automático, sin conexión, historial, comparar, restaurar, conflicto |
| `v2-investigacion` | 5 | Consentimiento, fuentes, contradicciones, fuente caída o lenta, sin resultados, sin proveedor |
| `v2-pdf` | 6 | Generar, descargar, reutilizar, desactualizado, versión vacía, cancelar, recargar a mitad |
| `v2-apuntes` | 8 | Dos cuentas (A/B), paginación, búsqueda, filtros, estados, descarga, borrado |
| `v2-perfil` | 7 | Preferencias, privacidad aplicada por el servidor, contraseña, sesiones, borrado de cuenta |
| `v2-errores` | 8 | Red cortada, 401, 413, 429, 500, código desconocido, contenido malicioso, cambio de cuenta |
| `v2-accesibilidad` | 12 | 10 pantallas a 320/768/1280 px, teclado y diálogos |

## 2. Accesibilidad (automática)

Para cada pantalla (inicio, ayuda, cuenta, crear, Mis apuntes, editor y sus pestañas, perfil):
`lang="es"`, un solo `h1`, `<main>`, todos los controles con etiqueta, botones y enlaces con nombre
accesible, `alt` en las imágenes, ids únicos, referencias `aria-*` existentes y **contraste AA**
(4,5:1; 3:1 en texto grande) calculado con los colores reales. Además: con `Tab` se llega a la
acción principal y el foco siempre se ve; los diálogos reciben el foco y `Escape` los cancela.

Hallazgos corregidos al introducirla: el editor no tenía `h1` (ahora uno oculto con el título del
apunte). Se comprobó que el auditor detecta texto gris claro, controles sin etiqueta y chips con
poco contraste inyectados a propósito.

No sustituye una revisión con lector de pantalla real (NVDA, VoiceOver, TalkBack), que queda como
comprobación manual recomendada.

## 3. Capturas y fallos

- `CAPTURAS=docs/evidencias npm run test:a11y` guarda una captura de cada pantalla a 320, 768 y
  1280 px; `v2-recorrido` guarda los pasos del recorrido y una captura del momento del fallo.
- `node --test --test-reporter=junit --test-reporter-destination=informe.xml …` produce un informe
  JUnit para CI (FULL-17). Las capturas usan datos sintéticos: no contienen datos de personas reales.

## 4. Matriz probada

| Navegador | Versión | Modo | Anchos | Cámara |
|-----------|---------|------|--------|--------|
| Chromium (Playwright) | 1.63 (build 1243) | Headless, Linux | 320, 360, 768, 1280 px | Dispositivo simulado (`--use-fake-device-for-media-stream`) |

**Limitaciones:** el entorno solo tiene Chromium; Firefox, Safari/WebKit y navegadores móviles
reales no se han probado (Playwright puede ejecutar Firefox y WebKit si se instalan:
`npx playwright install firefox webkit`). La cámara es la simulada de Chromium, no una cámara física.
La vista previa del PDF en `iframe` depende del visor del navegador; en modo headless no se
dibuja, pero sí se comprueba el archivo descargado.
