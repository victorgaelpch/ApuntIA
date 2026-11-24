# [BACK-11] Ampliar entrada de documentos para pizarrón, hojas de cuaderno y múltiples páginas

- Numero de Issue: #55
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/55
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch, I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:28:42 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:23 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:23 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:28:42Z
- Cierre UTC: 2026-11-10T17:05:23Z

- Fecha de captura: 2026-11-24 12:06:46 -0600 (CDMX)
- [Captura original](%5BBACK-11%5D%20Ampliar%20entrada%20de%20documentos%20para%20pizarr%C3%B3n%2C%20hojas%20de%20cuaderno%20y%20m%C3%BAltiples%20p%C3%A1ginas-original.png)
- [Captura con metadatos](%5BBACK-11%5D%20Ampliar%20entrada%20de%20documentos%20para%20pizarr%C3%B3n%2C%20hojas%20de%20cuaderno%20y%20m%C3%BAltiples%20p%C3%A1ginas.png)

## Descripcion original

## Objetivo
Aceptar fotografías de pizarrones y cuadernos —incluidas varias hojas ordenadas— como fuentes educativas, sin limitar el sistema a superficies de pizarrón. Preservar las imágenes originales y metadatos mínimos necesarios para su procesamiento posterior.

## Contexto técnico y alcance
El servicio actual `POST /analisis` valida JPEG/PNG/WEBP (máximo configurable) y entrega PNG; mantener esta ruta. Incorporar nueva entrada para trabajos/documentos sin cambiar el significado del endpoint heredado. Elegir ampliaciones de formatos solo después de validar bibliotecas y riesgos.

## Actividades detalladas
- [ ] Inspeccionar validación actual de firmas de imagen, megapíxeles, orientación EXIF, tamaño y errores; reutilizarla.
- [ ] Diseñar entrada multipágina para fotos ordenadas, sin asumir perspectiva de pizarrón en cuadernos.
- [ ] Aceptar JPEG/PNG/WEBP inicialmente; estudiar PDF de entrada opcional en issue posterior o añadirlo con pruebas de seguridad si se aprueba.
- [ ] Detectar orientación, recorte razonable, desenfoque/iluminación y corregir perspectiva por página según tipo de documento.
- [ ] Separar metadatos fuente (`tipo`, `numero_pagina`, `orden`, `dimensiones`, `hash`, `usuario`) de resultados OCR.
- [ ] Definir límites totales: número de páginas, MB por archivo/documento y píxeles; mantener límites existentes de `/analisis`.
- [ ] Manejar archivos repetidos, corruptos, vacíos, nombres maliciosos y descompresión excesiva sin bloquear el servidor.
- [ ] Persistir archivos solo según política de usuario e historial; temporales aislados y borrado seguro.
- [ ] Crear mensajes de error específicos para páginas fallidas conservando resultados parciales válidos.
- [ ] Actualizar OpenAPI y ejemplos de imágenes de cuaderno/pizarrón.

## Criterios de aceptación
- [ ] Se pueden subir varias fotos y mantener su orden original y tipo de fuente.
- [ ] Una foto de cuaderno NO se procesa obligatoriamente como un pizarrón.
- [ ] Las validaciones de seguridad existentes siguen vigentes y los errores son consistentes.
- [ ] El `POST /analisis` actual sigue retornando PNG sin cambios incompatibles.
- [ ] Un archivo inválido no destruye los demás ni filtra rutas internas.

## Pruebas y verificación obligatoria
- Pruebas con 1, 2 y 5 páginas, EXIF rotado, cuaderno cuadriculado/rayado y pizarrón.
- Casos límite de tamaño, contenido falso, PNG corrupto, nombres peligrosos, repetidos y carga concurrente.
- Regresión de pruebas anteriores de FastAPI.

## Archivos y entregables esperados
- Modelos y validadores de entrada multipágina, endpoints versionados.
- Fixtures seguras y tests Pytest.
- OpenAPI y guía de límites actualizados.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-15.
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

![Captura del Issue #55](%5BBACK-11%5D%20Ampliar%20entrada%20de%20documentos%20para%20pizarr%C3%B3n%2C%20hojas%20de%20cuaderno%20y%20m%C3%BAltiples%20p%C3%A1ginas.png)
