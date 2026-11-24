# [BACK-12] Adaptar OpenCV y preprocesamiento para mejorar OCR de cuadernos y pizarrones

- Numero de Issue: #56
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/56
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch, I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:29:09 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:25 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:25 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:29:09Z
- Cierre UTC: 2026-11-10T17:05:25Z

- Fecha de captura: 2026-11-24 12:06:51 -0600 (CDMX)
- [Captura original](%5BBACK-12%5D%20Adaptar%20OpenCV%20y%20preprocesamiento%20para%20mejorar%20OCR%20de%20cuadernos%20y%20pizarrones-original.png)
- [Captura con metadatos](%5BBACK-12%5D%20Adaptar%20OpenCV%20y%20preprocesamiento%20para%20mejorar%20OCR%20de%20cuadernos%20y%20pizarrones.png)

## Descripcion original

## Objetivo
Modificar el pipeline de visión para producir imágenes aptas para OCR en documentos impresos y manuscritos, sin destruir trazos finos, subíndices, signos matemáticos o líneas de tablas.

## Contexto técnico y alcance
Actualmente existen etapas de perspectiva, reducción de ruido y mejora del contraste. Deben reutilizarse pero con perfiles seleccionables: no aplicar el mismo filtrado a tinta fina de cuaderno que a marcadores de un pizarrón.

## Actividades detalladas
- [ ] Analizar implementaciones en `back/motori_magenes/app/services/`, medidas existentes y pruebas.
- [ ] Separar modo `pizarron`, `cuaderno`, `impreso` o `auto` con parámetros explícitos y fallback cuando falle la detección.
- [ ] Corregir orientación, perspectiva, sombras, balance de iluminación, brillo, ruido y contraste con algoritmos configurables.
- [ ] Evitar borrar signos `-`, `=`, `√`, exponentes, subíndices o separadores de tabla mediante morfología agresiva.
- [ ] Generar representación OCR optimizada y conservar original y vista procesada para auditoría y edición.
- [ ] Definir detección de calidad: resolución insuficiente, desenfoque, reflejo, corte de página, tinta pálida; reportar advertencias.
- [ ] Incorporar preprocesamiento por regiones cuando páginas combinan texto, fórmulas, dibujos y tablas.
- [ ] Medir efecto real en CER/WER y exactitud de fórmula; no asumir que visualmente más nítido implica mejor OCR.
- [ ] Controlar memoria/tiempo y evitar transformaciones destructivas acumulativas.
- [ ] Mantener el modo original `/analisis` y su interfaz de comparación.

## Criterios de aceptación
- [ ] Pizarrón y cuaderno pasan por pipelines adaptados sin deformaciones importantes.
- [ ] El preprocesamiento no elimina sistemáticamente trazos matemáticos ni líneas estructurales.
- [ ] Se preservan originales y hay advertencias de calidad cuando no puede garantizarse lectura.
- [ ] Se demuestra mejora o ausencia de regresión frente a línea base documentada.

## Pruebas y verificación obligatoria
- Casos con lápiz fino, borradores, cuadrícula, marcadores brillantes y luz lateral.
- Comparar resultados de OCR antes/después por tipo de muestra.
- Suite unitaria de servicios OpenCV y regresión de `/analisis`.

## Archivos y entregables esperados
- Pipeline configurable con tests y mediciones.
- Documentación de perfiles y limitaciones.
- Imágenes de demostración autorizadas y resultados comparativos.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-11.
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

![Captura del Issue #56](%5BBACK-12%5D%20Adaptar%20OpenCV%20y%20preprocesamiento%20para%20mejorar%20OCR%20de%20cuadernos%20y%20pizarrones.png)
