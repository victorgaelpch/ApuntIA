# [BACK-14] Reconocer escritura manuscrita de cuadernos y pizarrones con fallback seguro

- Numero de Issue: #58
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/58
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch, I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:29:48 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:18 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:18 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:29:48Z
- Cierre UTC: 2026-11-10T17:02:18Z

- Fecha de captura: 2026-11-24 12:07:00 -0600 (CDMX)
- [Captura original](%5BBACK-14%5D%20Reconocer%20escritura%20manuscrita%20de%20cuadernos%20y%20pizarrones%20con%20fallback%20seguro-original.png)
- [Captura con metadatos](%5BBACK-14%5D%20Reconocer%20escritura%20manuscrita%20de%20cuadernos%20y%20pizarrones%20con%20fallback%20seguro.png)

## Descripcion original

## Objetivo
Ampliar OCR a escritura a mano para apuntes de cuaderno y pizarrón. Usar un motor que admita manuscritos o una estrategia híbrida, sin prometer precisión total ni transcribir por imaginación.

## Contexto técnico y alcance
La escritura manuscrita varía enormemente; el objetivo operativo es identificar contenido legible, producir puntuación/advertencias y permitir revisión por usuario. Evaluar TrOCR/PaddleOCR u otros modelos según idiomas, recursos y licencias; no atar funcionalidad a servicios de pago sin alternativa.

## Actividades detalladas
- [ ] Reunir casos de manuscrito con permiso y referencias correctas: cursiva, imprenta, tinta oscura, lápiz, cuadrícula, renglones.
- [ ] Comparar motores/módulos HTR y su rendimiento en hardware razonable de una computadora académica.
- [ ] Integrar un adaptador específico para manuscrito reutilizando entrada y estructura JSON del OCR impreso.
- [ ] Identificar líneas y orden de lectura; soportar español, símbolos frecuentes y líneas partidas.
- [ ] Aplicar confianza calibrada cuando exista y un estado `revisar`/`no_reconocido` en vez de texto fabricado.
- [ ] Implementar estrategia fallback: conservar recorte visual original cuando el texto no sea suficientemente confiable.
- [ ] Evitar el reconocimiento de fórmulas como texto lineal si son regiones matemáticas: enviar a BACK-15.
- [ ] Registrar modelo, versión y parámetros usados en cada análisis para reproducibilidad.
- [ ] Documentar descarga/almacenamiento inicial de modelos y ejecución offline cuando sea viable.
- [ ] Agregar ejemplos de cuadernos con OCR corregible desde la interfaz.

## Criterios de aceptación
- [ ] El sistema intenta transcribir manuscritos y distingue claramente lo no legible.
- [ ] Puede conservar segmentos manuscritos como imagen, con localización para corrección manual.
- [ ] No destruye fórmulas ni modifica bloques seguros por un fallback mal aplicado.
- [ ] Hay evaluación reproducible por tipo de escritura y limitaciones declaradas.

## Pruebas y verificación obligatoria
- Muestras de varias caligrafías; medir CER/WER y errores frecuentes.
- Fallas de modelo, ausencia de internet inicial y memoria insuficiente manejadas sin caída global.
- Regresión OCR impreso y compatibilidad de salida v2.

## Archivos y entregables esperados
- Adaptador manuscrito con fallback y configuración.
- Muestras legales, tests y métricas.
- Guía de precisión esperable y corrección manual.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-12, BACK-13, FULL-19.
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

![Captura del Issue #58](%5BBACK-14%5D%20Reconocer%20escritura%20manuscrita%20de%20cuadernos%20y%20pizarrones%20con%20fallback%20seguro.png)
