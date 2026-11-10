# Arquitectura de IA multimodal (FULL-30)

Issue: [#91](https://github.com/victorgaelpch/ApuntIA/issues/91). Este documento recoge la
**auditoría del repositorio real** (fase 1), el **diseño** adaptado a lo que ya existe, la
**selección de modelos** con lo verificado hasta ahora y el **plan de PR**. Instalación y
operación del VLM local: [`ia-local.md`](ia-local.md).

## 1. Auditoría: qué existe ya (comprobado en el código, 2026-11-10)

| Pieza de la arquitectura objetivo (issue §4) | Estado real en ApuntIA | Dónde |
|---|---|---|
| Backend / API | FastAPI, API v1 y v2 con sesiones, permisos y límites. **No hay Spring Boot** (ni `pom.xml` ni código Java) | `back/motori_magenes/app` |
| Document Manager | Documento tipado `apuntia.documento/1` (Pydantic) con páginas, bloques, `bbox` en coordenadas de la foto, orden, recorte, texto original frente a editado, alternativas, procedencia y motivo de revisión (BACK-17, BACK-28) | `services/documento.py` |
| Job Manager | Cola persistente en SQLite con etapas, progreso, reintentos limitados, cancelación, límite de trabajos simultáneos y recuperación tras reinicio (BACK-27) | `services/trabajos.py` |
| Validación de imagen | MIME real, tamaño, píxeles máximos (anti-descompresión), páginas por apunte (BACK-11, FULL-22) | `services/entrada.py`, `validacion.py` |
| Preprocesado OpenCV | Perspectiva, enderezado del texto, iluminación, renglones y cuadrícula, perfiles pizarrón/cuaderno, sin morfologías que borren trazos (BACK-12, BACK-28) | `preprocesado_ocr.py`, `perspectiva.py` |
| Diagnóstico de calidad | Desenfoque, resolución, contraste, letra pequeña, inclinación; nivel «insuficiente» (BACK-28) | `calidad.py` |
| Layout | Bloques de Tesseract en orden de lectura; títulos, listas y tablas por heurística; zonas sin texto (diagramas) conservadas como imagen (BACK-13, 14, 16) | `ocr.py`, `estructura.py`, `manuscrito.py` |
| Reconocimiento | Tesseract con variantes por región, consenso y alternativas (BACK-28) | `reconocimiento.py`, `adaptativo.py` |
| OCR matemático | Texto lineal → LaTeX validado y renderizado de forma segura; fórmulas 2D: recorte (BACK-15) | `formulas.py` |
| Validación antialucinaciones | Lo dudoso no se da por seguro; lo ilegible queda vacío con su recorte; nada se inventa (BACK-14, 28) | `adaptativo.py` |
| Editor | Vista dividida foto / bloques, regiones resaltadas, edición de texto y LaTeX, alternativas con un clic, historial de versiones (FRONT-12 a 21) | `front/js/v2/` |
| PDF | Generado desde el documento estructurado (no texto concatenado), con fórmulas renderizadas, recortes y avisos (BACK-20) | `services/pdf.py` |
| Despliegue | Scripts Windows/Linux y Docker Compose (FULL-11, 13) | `fullstack/` |
| Evaluación | Banco FULL-19 (11 muestras) y corpus difícil BACK-28 (22 fotos, 2 particiones), **todo sintético** | `fullstack/evaluacion`, `herramientas/` |

**Conclusión:** buena parte del esqueleto que pide el issue ya existe. Lo que falta es lo
**multimodal**: motores distintos de Tesseract, enrutamiento por tipo de región, un VLM local y
una evaluación con fotos reales.

## 2. Brechas (lo que falta de verdad)

1. **Interfaz común de motores y registro** → este PR.
2. **VLM local opcional** (Ollama) con diagnóstico de hardware y perfiles → este PR (adaptador;
   todavía sin usarlo en el análisis).
3. **Clasificación de regiones** más rica (fórmula / diagrama / tabla / manuscrito / impreso) con
   bounding boxes propias, no solo los bloques de Tesseract.
4. **Motores especializados evaluados**: OCR documental, HTR en español, OCR matemático 2D.
5. **Reprocesar una región** desde el editor (hoy se reanaliza la página entera).
6. **Corpus real** con fotos autorizadas de los casos A, B y C del issue y su transcripción
   verificada por personas.
7. **Exportaciones** HTML y TXT y variantes de PDF (fiel / académico).

## 3. Diseño (adaptado a las convenciones del repositorio)

```
app/services/ia/                  (nuevo; nombres en español como el resto del backend)
  motores.py     interfaz MotorReconocimiento + ResultadoMotor + adaptador de Tesseract
  ollama.py      VLM local por Ollama (opcional, local, sin descargas)
  registro.py    registro de motores, perfiles, enrutamiento por tarea y diagnóstico del equipo
app/routers/v2_reconocimiento.py  GET /api/v2/reconocimiento/motores y /perfiles
fullstack/scripts/diagnostico_ia.py
```

Interfaz común (issue §9), en español:

| Issue | ApuntIA |
|---|---|
| `is_available()` | `disponible()` (rápido; sin cargar modelos; caché de 30 s en el VLM) |
| `get_capabilities()` | `capacidades()` → `texto_impreso`, `texto_manuscrito`, `formula`, `diagrama`, `tabla`, `layout` |
| `get_model_info()` | `info_modelo()` → nombre, modelo, versión, licencia, local, motivo si no está |
| `recognize(image, options)` | `reconocer(imagen, OpcionesReconocimiento)` → `ResultadoMotor` o `ErrorMotor` con código |

**Rutas:** el issue propone `/api/v2/recognition/jobs…`, pero los trabajos ya existen
(`/api/v2/apuntes` crea el análisis y `/api/v2/trabajos/{id}` lo sigue, lo cancela y lo
reintenta). Para no duplicarlos solo se añaden `motores` y `perfiles`. Reprocesar una región
será `POST /api/v2/apuntes/{id}/bloques/{bloque}/reconocer` en la fase 6.

**Estados:** el contrato ya tiene equivalentes; no se cambian para no romper apuntes guardados.

| Issue §14 | ApuntIA |
|---|---|
| RECOGNIZED | `reconocido` |
| NEEDS_REVIEW | `incierto` (+ `revision`: `lecturas_distintas`, `sin_confirmar`…) |
| PARTIALLY_RECOGNIZED | `incierto` con `palabras_dudosas` |
| UNREADABLE | `no_reconocido` (texto vacío + recorte) |
| PRESERVED_AS_IMAGE | `conservar_imagen: true` (tipo `imagen` o `manuscrito` sin texto) |
| USER_CORRECTED | `editado: true` (con `texto_original` intacto) |

**Perfiles:** `rapido` (Tesseract, flujo clásico), `equilibrado` (Tesseract adaptativo de
BACK-28; aquí entrarán los motores especializados), `avanzado` (+ VLM local) y `automatico` (el
más completo que el equipo puede ejecutar). **En este PR el análisis todavía no usa los perfiles**
(la API lo indica con `aplicado_en_analisis: false`).

**Principio del VLM:** apoyo interpretativo, nunca la única fuente. Sus salidas no tienen
confianza calibrada, así que siempre quedan como propuesta para revisar. El contenido
reinterpretado (descripciones de diagramas, reorganización) irá en campos separados de la
transcripción, nunca sustituyéndola.

## 4. Selección de modelos (verificado / pendiente)

| Motor | Uso previsto | Licencia | Estado |
|---|---|---|---|
| Tesseract 5.3.4 | Texto impreso; respaldo | Apache-2.0 | **Integrado y medido** (FULL-19, BACK-28) |
| Qwen3-VL 2B / 4B / 8B por Ollama | Apoyo visual: diagramas, layout, manuscrito dudoso | Apache-2.0 (ficha en ollama.com) | **Adaptador listo; sin medir**. Etiquetas verificadas en ollama.com: `qwen3-vl:2b` (1,9 GB), `:4b` (3,3 GB), `:8b` (6,1 GB); exige Ollama ≥ 0.12.7 |
| Modelos `*-cloud` de Ollama | — | — | **Bloqueados**: procesan la imagen fuera del equipo |
| pix2tex 0.1.4 | Fórmulas 2D | MIT | **Medido y descartado** (BACK-28, `evaluacion.md` §7): inventa símbolos y cambia números sin avisar; ~6 GB |
| TrOCR | HTR | MIT | **No apto aún**: el modelo manuscrito oficial (`trocr-base-handwritten`) es inglés (IAM); los modelos en español (`qantev/trocr-*-spanish`) son **solo para texto impreso**, según su propia ficha |
| PaddleOCR (PP-OCRv5) | OCR documental, tablas | Apache-2.0 | Por evaluar (fase 3). Sus pesos se descargan de servidores externos: probarlo requiere un equipo con acceso |
| Pix2Text | OCR matemático | MIT según su repositorio (verificar al integrarlo) | Por evaluar (fase 4), comparándolo con lo medido para pix2tex |
| SymPy | Comprobaciones, sin «corregir» transcripciones | BSD | Por evaluar (fase 4) |

## 5. Evaluación prevista (y lo que NO se ha medido)

- **Nada del VLM se ha medido todavía.** En el entorno donde se escribió este PR no había GPU,
  había 7,8 GB de RAM y no se podían descargar modelos (ollama.com y Hugging Face bloqueados).
  Las pruebas usan un Ollama **simulado**: comprueban el contrato, los errores y la seguridad,
  no la calidad. La memoria por modelo de `registro.MEMORIA_ESTIMADA_GB` es una **estimación**
  (tamaño del archivo + margen), no una medida.
- Primer paso real para quien tenga el hardware: `python fullstack/scripts/diagnostico_ia.py --probar`.
- Comparación obligatoria (issue §24) con los mismos datos: 1) Tesseract actual, 2) OCR documental,
  3) VLM local, 4) híbrido. Por categoría (texto impreso, manuscrito, fórmulas, diagramas, tablas,
  layout) y dificultad, no solo promedios. Métricas: CER, WER, omisiones, duplicados, **contenido
  inventado**, exactitud de LaTeX y renderizado, regiones conservadas, orden, tiempo, RAM/VRAM.
- **Datos:** los tres casos reales del issue (agrupamiento, Cálculo III, circuitos) requieren
  fotos con permiso de su autor y transcripción verificada por personas. Las fotos compartidas
  por chat no están en el repositorio y no se incluyen sin esa autorización.

## 6. Plan de PR

| # | PR | Contenido | Estado |
|---|----|-----------|--------|
| 1 | Auditoría, interfaz de motores, Ollama, perfiles y diagnóstico | Este documento, `services/ia/`, API de motores y perfiles, `diagnostico_ia.py`, `ia-local.md` | **Este PR** |
| 2 | Perfiles en el análisis + VLM en regiones conservadas como imagen | El trabajo de análisis usa el perfil; en «avanzado», el VLM añade una **descripción marcada como IA** a diagramas y regiones sin leer, en un campo nuevo y opcional del contrato, sin tocar la transcripción. Editor y PDF la muestran como «generado por IA» | Siguiente |
| 3 | Corpus real y benchmark multimotor | Fotos autorizadas A/B/C con su verdad; `fullstack/evaluacion/multimodal`; Tesseract frente a VLM (los resultados reales se publican aunque sean malos) | Necesita fotos y un equipo con el modelo |
| 4 | Clasificación de regiones | Detector de regiones (fórmula, diagrama, tabla, manuscrito) con medida de precision/recall | — |
| 5 | Motores especializados | PaddleOCR y OCR matemático, solo si mejoran lo medido en el PR 3 | — |
| 6 | Reprocesar una región desde el editor | Endpoint y botón; selector de perfil en la interfaz | — |
| 7 | Exportaciones | HTML, TXT, PDF fiel / académico | — |
| 8 | Docker con Ollama opcional, caché por hash, recursos | Servicio `ollama` en un perfil de Compose, volumen de modelos, límites | Probar en Docker real antes de declararlo |
