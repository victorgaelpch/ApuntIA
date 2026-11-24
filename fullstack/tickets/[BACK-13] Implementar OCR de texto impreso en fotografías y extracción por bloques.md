# [BACK-13] Implementar OCR de texto impreso en fotografías y extracción por bloques

- Numero de Issue: #57
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/57
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch, I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:29:32 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:26 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:27 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:29:32Z
- Cierre UTC: 2026-11-10T17:05:26Z

- Fecha de captura: 2026-11-24 12:06:56 -0600 (CDMX)
- [Captura original](%5BBACK-13%5D%20Implementar%20OCR%20de%20texto%20impreso%20en%20fotograf%C3%ADas%20y%20extracci%C3%B3n%20por%20bloques-original.png)
- [Captura con metadatos](%5BBACK-13%5D%20Implementar%20OCR%20de%20texto%20impreso%20en%20fotograf%C3%ADas%20y%20extracci%C3%B3n%20por%20bloques.png)

## Descripcion original

## Objetivo
Incorporar reconocimiento óptico de caracteres real para transformar imágenes de apuntes impresos y texto legible de pizarrón en bloques de texto estructurados. No confundir limpieza OpenCV con OCR.

## Contexto técnico y alcance
Elegir un motor adecuado entre opciones libres y evaluables como Tesseract, PaddleOCR, EasyOCR u otro, basándose en pruebas, soporte de español, coste, licencias y requisitos. El motor no se debe hardcodear sin justificación.

## Actividades detalladas
- [ ] Revisar dependencias, estructura de servicios y contrato v2 antes de agregar biblioteca.
- [ ] Construir una interfaz de adaptador OCR (`reconocer(imagen, idioma, regiones)`) desacoplada de FastAPI y del proveedor concreto.
- [ ] Implementar extracción de texto impreso con idioma español y caracteres comunes en inglés, números y signos.
- [ ] Retornar texto por línea/bloque, orden de lectura, coordenadas, confianza si el motor la ofrece y página de origen.
- [ ] Normalizar codificación Unicode y conservar saltos/límites que aporten estructura sin cambiar automáticamente el contenido.
- [ ] Crear advertencia para imágenes sin texto, texto ilegible o confianza baja; no inventar transcripción.
- [ ] Evitar bloquear indefinidamente la API: límites de ejecución y memoria, control de modelo y errores uniformes.
- [ ] Permitir sustitución de motor y pruebas con mocks; no introducir claves externas obligatorias.
- [ ] Agregar endpoint/servicio que entregue JSON v2, nunca reemplazar el PNG devuelto por `/analisis`.
- [ ] Documentar dependencias nativas, primera instalación, licencias y limitaciones lingüísticas.

## Criterios de aceptación
- [ ] Una imagen de texto impreso legible produce bloques de texto con ubicación y orden correctos de forma verificable.
- [ ] La API distingue resultado vacío, fallo técnico y confianza baja.
- [ ] Se conservan tildes, eñes y caracteres Unicode esperados en el PDF posterior.
- [ ] El procesamiento anterior sigue siendo compatible.

## Pruebas y verificación obligatoria
- Benchmark sobre fotos impresas con ground truth en español y mezcla texto/números.
- Tests con texto vacío, Unicode, imágenes rotadas, límites y falla de motor.
- Ejecutar pruebas sin acceso a servicios cloud.

## Archivos y entregables esperados
- Adaptador OCR, servicio y endpoints v2.
- Fixtures y benchmark CER/WER con metodología.
- Manual de instalación y compatibilidad OCR.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-11, BACK-12; FULL-15.
- **Área responsable:** backend.
- **Prioridad:** Crítica.

### Reglas obligatorias de implementación para Claude o cualquier desarrollador
- Antes de escribir código, inspeccionar la rama objetivo y el estado REAL del repositorio (`README.md`, `docs/api.md`, `docs/arquitectura.md`, `back/`, `front/`, `fullstack/` si existe, scripts, tests y PR relacionados). No asumir rutas, tecnologías o funcionalidades que no estén presentes.
- NO crear una segunda implementación si ya existe: extender, refactorizar de manera incremental y reutilizar módulos. Resolver discrepancias del código real y documentarlas en el PR.
- Conservar compatibilidad del sistema previo: `POST /analisis` recibe campo `file` y devuelve PNG; `GET /salud` y el formato `{ "error": { "codigo": "...", "mensaje": "..." } }` siguen disponibles salvo decisión explícita y versionada.
- No eliminar ni debilitar validaciones, seguridad, módulos, pruebas ni documentación existentes; no introducir rutas absolutas, claves en el repositorio ni datos privados de alumnos.
- Antes de cerrar, ejecutar tests afectados (y suites disponibles), corregir fallos, revisar integración con frontend/backend/fullstack, actualizar README/contrato/arquitectura y registrar comandos + resultados reales.
- Adjuntar en el PR evidencia reproducible, capturas o archivos sintéticos cuando correspondan, problemas detectados y decisiones técnicas; NO declarar pruebas como aprobadas sin haberlas ejecutado.

## Evidencia y bitácora
- Fecha, responsable, actividades realizadas y tiempo invertido.
- Archivos editados, endpoints/contratos afectados y motivo de cada cambio.
- Comandos de pruebas realmente ejecutados, resultados y capturas/logs saneados.
- Incidencias, soluciones, limitaciones y enlaces al Pull Request/commits.


## Evidencia visual

![Captura del Issue #57](%5BBACK-13%5D%20Implementar%20OCR%20de%20texto%20impreso%20en%20fotograf%C3%ADas%20y%20extracci%C3%B3n%20por%20bloques.png)
