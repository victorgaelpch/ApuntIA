# Evaluación multimodal del reconocimiento (BACK-36)

Antes de cambiar el pipeline de reconocimiento hay que **medir** con fotos reales. Este
documento define el corpus, las métricas y cómo se ejecuta la medición. Las cifras actuales con el
corpus sintético están en [servidor-ia.md §8.2](servidor-ia.md#82-comparación-de-modelos-con-el-pipeline-11-13112026).

> Estado (14/11/2026): banco de medición **implementado y probado** (`python -m ia_servidor.medir
> --corpus …`, 7 pruebas). **Bloqueado**: faltan las fotos reales con permiso. Sin ellas no se elige la
> segmentación por regiones ni se afirma nada sobre pizarrones reales.

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

Ninguno todavía: no hay corpus real. No se reportan cifras hasta medirlas.
