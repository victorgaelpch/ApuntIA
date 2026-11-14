# Evaluación multimodal del reconocimiento (BACK-36)

Antes de cambiar el pipeline de reconocimiento hay que **medir** con fotos reales. Este
documento define el corpus, las métricas y cómo se ejecuta la medición. Las cifras actuales con el
corpus sintético están en [servidor-ia.md §8.2](servidor-ia.md#82-comparación-de-modelos-con-el-pipeline-11-13112026).

> Estado (14/11/2026): banco de medición **implementado y probado** (`python -m ia_servidor.medir
> --corpus …`, con cobertura, fidelidad a los errores del original y comparación página/regiones;
> 16 pruebas). **Medido con 1 foto real** de pizarrón (§5.1): segmentar por regiones mejora la
> fidelidad. Faltan más fotos (cuaderno manuscrito, circuito) y la segmentación automática.

## 1. Corpus privado (fuera de Git)

Carpeta `fullstack/evaluacion/privado/` (ignorada por Git: nunca se sube). Contiene las fotos y un
`verdad.json` revisado a mano:

```json
{
  "calculo3_vectores": {
    "archivo": "calculo3_vectores.jpg",
    "tipo_fuente": "cuaderno",
    "escritura": "formula",
    "lineas": ["∇f = (∂f/∂x, ∂f/∂y)"],
    "latex": ["\\nabla f = \\left(\\frac{\\partial f}{\\partial x}, \\frac{\\partial f}{\\partial y}\\right)"],
    "permiso": "autor de los apuntes, autorizado por escrito el 2026-11-14"
  }
}
```

- `escritura`: `impreso`, `manuscrito`, `formula`, `tabla`, `diagrama` o `pagina`.
- `permiso` es **obligatorio**: el medidor rechaza una foto sin él.
- Antes de guardarlas: recortar o tapar nombres, rostros, matrículas y cualquier dato personal.
- `lineas` es la transcripción LITERAL en orden de lectura (no la versión corregida); en
  fórmulas, `latex` es la versión revisada. Si algo es ilegible para una persona, no se incluye.

### Fotos necesarias (mínimo)

| # | Caso (del documento de Issues) | Qué mide |
|---|--------------------------------|----------|
| 1 | Agrupamiento / Nmap con tabla | Texto manuscrito + estructura de tabla |
| 2 | Cálculo III: vectores y derivadas | Fórmulas 2D (fracciones, parciales, vectores) |
| 3 | Circuitos con mallas | Diagrama: componentes, valores y conexiones |
| 4+ | Difíciles: poca luz, sombra, tachones, cuadrícula, letra pequeña, pizarrón inclinado | Robustez |

## 2. Métricas

| Métrica | Para | Cálculo |
|---------|------|---------|
| CER / WER | impreso, manuscrito, tabla | Distancia de edición normalizada (`herramientas/metricas.py`) |
| CER LaTeX literal | fórmulas | Sin espacios ni `$`, `x^{2}` = `x^2` |
| CER notación equivalente | fórmulas | Además `\frac{a}{b}` = `a/b`, `\sqrt{x}` = `sqrt(x)` (no es una prueba matemática) |
| Latencia (fría y en caliente) | todas | Segundos por imagen; la 1.ª incluye la carga del modelo |
| VRAM pico | todas | `nvidia-smi` cada 0,25 s + `/api/ps` |
| Errores por código | todas | `RESPUESTA_INVALIDA`, `SIN_MEMORIA`, `TIEMPO_AGOTADO`… |
| Dudas marcadas | todas | Fragmentos `[?]` del modelo frente a errores reales (¿marca lo que falla?) |
| Cobertura | todas | Fracción de elementos de la verdad presentes en la salida (CER ≤ 25 % por elemento, sin depender del orden) |
| **Fidelidad** | trampas | Errores reales del original: fiel (se conserva), **corregida** (el modelo lo «arregló»: alucinación) o no leída |

Pendientes de implementar cuando haya corpus: celdas de tabla correctas y relaciones de
diagramas (nodos y aristas), y equivalencia con SymPy en fórmulas aplicables.

## 3. Ejecutar

En la PC del servidor, con el servidor IA en marcha:

```bat
ia_servidor\.venv\Scripts\python -m ia_servidor.medir --corpus fullstack\evaluacion\privado
```

El informe queda en `fullstack/evaluacion/resultados/servidor-ia-medicion-<modelo>-privado.json`
(también ignorado por Git: contiene texto transcrito). Para comparar modelos, repetir con
`IA_MODELO=qwen3-vl:4b-instruct` y anotar aquí SOLO cifras medidas.

## 4. Decisiones que dependen del corpus

| Decisión | Opciones | Criterio |
|----------|----------|----------|
| Segmentación por regiones | (a) página completa al VLM (hoy); (b) regiones con OpenCV (morfología/contornos) y una petición por región; (c) *grounding* de Qwen3-VL (cajas que propone el modelo); (d) PaddleOCR-VL / PP-Structure | Menor CER y menos bloques omitidos en fotos reales, dentro de 12 GB y tiempo razonable |
| Segundo motor para tablas y fórmulas | PaddleOCR-VL 1.6 (0,9 B, Apache-2.0; instalación orientada a Linux/Docker, probablemente WSL2), pix2tex (solo fórmulas impresas) | Solo si mejora de forma medible al VLM |
| Modelo principal | 8b-instruct frente a 4b-instruct | Si el 4B iguala la calidad en fotos reales, ahorra 2,3 GB de VRAM y la mitad del tiempo |

## 5. Resultados con fotos reales

### 5.1 Pizarrón de trigonometría (14/11/2026)

Corpus: **una** foto real de pizarrón (2000×1500, tres colores de marcador; aportada por el dueño del
proyecto para evaluación privada, sin datos personales) y **12 regiones recortadas a mano** de ella
(fórmulas 2D, tabla grados/radianes, identidades, valores, recordatorios manuscritos). Verdad
transcrita literalmente, con **6 trampas**: errores reales del pizarrón que deben conservarse
(`(cos(h)-1)/1`, `cos(θ/2)` con `1 - cos θ`, un denominador `cos²` equivocado, `sin(π)=-1`,
`sin(π/2)=0`, `sin(3π/2)=0`) y 3 faltas de ortografía en títulos. Equipo: RTX 3060, Ollama 0.40.16,
pipeline 1.1. Recortes manuales = segmentación ideal: es la **cota superior** de cualquier
segmentación automática.

| | 8b-instruct, página completa | 8b-instruct, por regiones | 4b-instruct, página completa | 4b-instruct, por regiones |
|---|---|---|---|---|
| Elementos de las regiones encontrados (38) | 97 % | 97 % | **13 %** | 97 % |
| Títulos y textos fuera de regiones (16) | 100 % | — | 0 % | — |
| Trampas: fieles / **corregidas** / no leídas (6) | 5 / **1** / 0 | 5 / 0 / 1 | 0 / **5** / 1 | **6 / 0 / 0** |
| Ortografía del original (3) | **3 corregidas** | — | **3 corregidas** | — |
| Latencia | 21,3 s la página | 2,2–4,5 s por región (≈40 s las 12) | 18,1 s | 1,3–3,2 s (≈22 s las 12) |
| Pico de VRAM de la GPU* | 10,8 GB | 10,8 GB | 8,2 GB | 8,2 GB |

\* Incluye ~2,9 GB del escritorio. La 1.ª petición de cada tanda incluye la carga del modelo (9–14 s).

Observaciones literales:
- Con la página completa, el 8B **corrigió** `(cos(h)-1)/1` a `/h` y la ortografía de los títulos:
  justo lo que el Issue prohíbe («no corregir la ecuación escrita»).
- El 4B con la página completa la envolvió en `\begin{center}`, unió fórmulas con `\quad` e
  **inventó** encabezados («Special Values», «Graphs»): inutilizable como transcripción.
- Por regiones, el 8B desordenó las fracciones 2D de las identidades (une numeradores y
  denominadores); el 4B las transcribió exactas. El 4B omitió la cabecera «Degree | Radians» de la tabla.
- Ningún modelo marcó dudas (`[?]`) en esta foto.

**Conclusión provisional** (una sola foto: no generalizable):
1. **Segmentar por regiones mejora la fidelidad** con ambos modelos y es imprescindible con el 4B.
   La página completa solo sirve, si acaso, para el orden de lectura y los títulos, nunca como
   transcripción de fórmulas.
2. Por regiones, el **4b-instruct fue igual o mejor** que el 8B (6/6 trampas, identidades exactas),
   en la mitad del tiempo y con 2,6 GB menos de VRAM.
3. Siguiente paso: **segmentación automática** de regiones (OpenCV o *grounding*) medida contra estos
   recortes manuales, y más fotos (cuaderno manuscrito, circuito) antes de cambiar el modelo por defecto.

Reproducir: `python -m ia_servidor.medir --corpus fullstack\evaluacion\privado` con cada modelo;
`--reevaluar INFORME --corpus …` recalcula cobertura y fidelidad sin usar la GPU.

### 5.2 Segmentación automática (tarea `documento`, 14/11/2026)

Misma foto. `regiones_opencv` (sin GPU, 83 ms) propone las regiones y cada una se lee con un prompt
genérico de región; se compara sobre los mismos 38 elementos y 6 trampas. `IA_SEG_HUECO_LINEAS`
controla cuánto se unen las líneas de un mismo párrafo (0 = regiones por línea).

| Modelo · hueco | Regiones | Elementos encontrados | Trampas fieles / corregidas / no leídas | Tiempo |
|----------------|----------|-----------------------|------------------------------------------|--------|
| 4b-instruct · 0 | 33 | 79 % | 5 / 1 / 0 | 65,9 s |
| 4b-instruct · 0,2 | 17 | 82 % | 3 / 2 / 1 | 35,4 s |
| 4b-instruct · 0,6 | — | falló (502: una región sin respuesta válida tumbaba el documento; **corregido**, ahora queda «no reconocida») | — | 29,2 s |
| 8b-instruct · 0 | 33 | 79 % | 1 / 1 / 4 | 86,1 s |
| **8b-instruct · 0,2** | **17** | **95 %** | **6 / 0 / 0** | 52,8 s |
| 8b-instruct · 0,6 | 13 | 100 % | 5 / 1 / 0 | 43,5 s |
| *Referencia:* 8b, página completa | — | 97 % | 5 / 1 / 0 | 21,3 s |

- Regiones demasiado pequeñas (hueco 0) pierden contexto: cada línea suelta se lee peor.
- Con regiones automáticas, el 8B supera al 4B (al revés que con los recortes manuales): el 4B es
  más sensible a recortes imperfectos.
- **Configuración por defecto provisional**: `qwen3-vl:8b-instruct` y `IA_SEG_HUECO_LINEAS=0.2`
  (la única combinación sin ninguna trampa corregida). Es una sola foto: revisar con más fotos.
- Pendiente: *grounding* (cajas propuestas por el VLM) y tablas, que la segmentación aún parte en trozos.
