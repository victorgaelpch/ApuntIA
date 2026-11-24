# [FULLSTACK][IA][OCR][P0] Implementar motor multimodal avanzado de reconocimiento, interpretación y reconstrucción inteligente de apuntes académicos

- Numero de Issue: #91
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/91
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-10 13:02:32 -0600 (CDMX)
- Cierre GitHub: 2026-11-12 19:45:39 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-12 19:45:39 -0600 (CDMX)
- Creacion UTC: 2026-11-10T19:02:32Z
- Cierre UTC: 2026-11-13T01:45:39Z

- Fecha de captura: 2026-11-24 12:09:25 -0600 (CDMX)
- [Captura original](%5BFULLSTACK%5D%5BIA%5D%5BOCR%5D%5BP0%5D%20Implementar%20motor%20multimodal%20avanzado%20de%20reconocimiento%2C%20interpretaci%C3%B3n%20y%20reconstrucci%C3%B3n%20inteligente%20de%20apuntes%20acad%C3%A9micos-original.png)
- [Captura con metadatos](%5BFULLSTACK%5D%5BIA%5D%5BOCR%5D%5BP0%5D%20Implementar%20motor%20multimodal%20avanzado%20de%20reconocimiento%2C%20interpretaci%C3%B3n%20y%20reconstrucci%C3%B3n%20inteligente%20de%20apuntes%20acad%C3%A9micos.png)

## Descripcion original

## 1. CONTEXTO GENERAL

ApuntIA busca convertir fotografías de pizarrones, cuadernos y documentos académicos en apuntes digitales editables y exportables.

El sistema actual emplea técnicas de visión por computadora y OCR. Sin embargo, el reconocimiento puede fallar ante:
- Escritura manuscrita compleja o inclinada.
- Apuntes con varios colores y tamaños de letra.
- Cuadernos cuadriculados o rayados.
- Derivadas, integrales, matrices, vectores, fracciones y ecuaciones.
- Circuitos eléctricos, diagramas de flujo y mapas conceptuales.
- Gráficas, flechas, llaves y relaciones espaciales.
- Tablas, comparaciones y documentos de varias columnas.
- Mezclas de texto impreso, manuscrito y elementos visuales.

La meta es evolucionar ApuntIA hacia una arquitectura multimodal que combine OCR tradicional, reconocimiento manuscrito (HTR), modelos de visión-lenguaje (VLM), OCR matemático y análisis de distribución espacial.

El resultado debe conservar la información original, la estructura, las fórmulas y los diagramas. Si una región es ilegible, se debe preservar el recorte original y marcarla para revisión, nunca inventarla.

## 2. INSTRUCCIONES OBLIGATORIAS PARA CLAUDE / AGENTE DE DESARROLLO

ANTES de editar, inspeccionar el estado real del repositorio: README principal, back/motori_magenes/, front/, fullstack/, docs/, requirements, iniciar.bat, iniciar.sh, Docker/Compose, endpoints OCR, modelos de datos, editor, generador de PDF y pruebas.

Reglas obligatorias:
- No rehacer el proyecto desde cero ni eliminar capacidades actuales.
- No inventar rutas, tecnologías, carpetas o dependencias existentes: verificar primero.
- No asumir que Spring Boot participa en la versión actual; comprobarlo.
- Mantener los contratos de API existentes o versionarlos con migración compatible.
- No introducir un único servicio monolítico para todas las tareas de IA.
- Mantener compatibilidad con apuntes, usuarios, permisos, exportación y Docker.
- No instalar modelos pesados como dependencia obligatoria del modo básico.
- No descargar pesos en CI ni subirlos a Git.
- No usar APIs de pago obligatorias.
- Verificar licencia, condiciones de distribución y uso de cada modelo y dependencia.
- Conservar originales y permitir revisión humana de ambigüedades.
- Dividir la implementación en PR pequeños, con pruebas y entregables verificables.
- No declarar terminadas funciones cuya integración o evaluación real no se haya realizado.

## 3. PROBLEMAS A RESOLVER

A. Texto: sólo se recuperan fragmentos, hay omisiones y mezclas entre columnas.
B. Fórmulas: se pierden subíndices, exponentes, vectores, fracciones y símbolos.
C. Diagramas: el OCR puede destruir circuitos, gráficas y flechas.
D. Estructura: no se respeta siempre el orden de lectura ni la relación entre elementos.
E. Exportación: el PDF puede quedar incompleto porque la extracción falla.
F. Operación: modelos de IA locales deben funcionar con recursos y configuraciones variables.
G. Verificación: faltan métricas reproducibles y un conjunto de documentos de prueba representativo.

## 4. ARQUITECTURA OBJETIVO

Frontend existente
    |
    v
Backend / API actual
    |
    v
Document Manager + Job Manager
    |
    +--> Validación de imagen y metadatos
    |
    +--> OpenCV: limpieza adaptativa, orientación, perspectiva
    |
    +--> Layout Analyzer: regiones, columnas, tablas, orden de lectura
    |
    +--> Recognition Manager
    |       |-- OCR tradicional (Tesseract: fallback)
    |       |-- OCR documental (PaddleOCR / PaddleOCR-VL)
    |       |-- HTR para manuscritos (TrOCR u otra alternativa adecuada)
    |       |-- OCR matemático (Pix2Text u otra alternativa)
    |       `-- VLM local (Qwen3-VL mediante Ollama u otro runtime compatible)
    |
    +--> Result Aggregator + Evidence Store
    |
    +--> Validación, comparación de alternativas, control de alucinaciones
    |
    +--> Document Reconstruction Engine
    |
    v
Editor de apuntes existente
    |
    v
PDF / HTML / TXT + originales y recortes de apoyo

Todos los componentes de IA deberán tener adaptadores independientes, esquemas de entrada y salida estables, manejo de fallos y registro de versiones.

## 5. INVESTIGACIÓN Y SELECCIÓN DE MODELOS

Evaluar, no instalar indiscriminadamente:

- Qwen3-VL (variantes ligeras y cuantizadas, por ejemplo 2B/4B/8B si están disponibles para el runtime elegido): análisis contextual y visual, estructura general, diagramas y apoyo al reconocimiento manuscrito.
- PaddleOCR / PaddleOCR-VL: OCR y análisis documental, tablas y estructuras compatibles.
- TrOCR u otra arquitectura HTR: manuscritos, previa verificación con español y cuadernos reales.
- Pix2Text o modelo matemático especializado: conversión de expresiones a LaTeX.
- Tesseract: soporte legado y fallback para texto impreso.
- OpenCV: preprocesamiento, transformación y extracción de regiones.
- SymPy: verificaciones matemáticas cuando aplique (sin alterar la transcripción por “corrección” automática).
- Ollama / Transformers / PyTorch: ejecución local según modelo, licencia y compatibilidad.
- Renderizador LaTeX seguro y generador PDF existente: presentación y exportación.

Criterios comparativos:
- Precisión en español y manuscritos reales.
- Calidad de reconocimiento de fórmulas.
- Capacidad de detección y clasificación de regiones.
- Calidad estructural y respeto del orden de lectura.
- CPU/GPU/RAM/VRAM necesarios y tiempos.
- Compatibilidad Windows/Linux/Docker.
- Licencia y posibilidad de distribución.
- Estabilidad, actualización y disponibilidad de modelos.

Documentar las versiones elegidas y fijarlas en las dependencias/configuración. No asumir que cualquier VLM puede realizar todas estas tareas correctamente.

## 6. MOTOR DE PREPROCESAMIENTO ADAPTATIVO

Ampliar OpenCV para:
- Corrección de perspectiva, orientación y rotación.
- Detección de desenfoque y baja resolución.
- Corrección de iluminación, sombras y contraste.
- Detección de bordes y regiones.
- Reducción de ruido sin borrar trazos finos.
- Tratamiento de papel cuadriculado/rayado.
- Conservación de colores de tinta y anotaciones.
- Generación selectiva de variantes: original, contraste, OCR, fórmulas.

No aplicar todos los filtros a todas las imágenes. Binarizaciones y morfologías agresivas pueden destruir tildes, puntos, signos menos, exponentes y circuitos. Conservar siempre la imagen original y la transformación geométrica usada.

## 7. ANÁLISIS DE LAYOUT Y REGIONES

Detectar, clasificar y ubicar:
- title, subtitle, paragraph, handwritten_text, printed_text
- formula, table, list, diagram, graph
- annotation, arrow, image, unknown

Cada región debe contener:
- ID estable, página y tipo.
- Bounding box o polígono en coordenadas del original.
- Orden de lectura y relaciones espaciales.
- Texto/LaTeX/descripción si fue posible obtenerlos.
- Referencia al recorte original.
- Motor, modelo y versión utilizados.
- Estado de validación y evidencias.
- Incertidumbre/confianza sólo cuando sea interpretable y esté calibrada.

Detectar columnas, secciones, tablas, bloques, conexiones entre flechas y texto, y elementos superpuestos. Mantener matrices de transformación para mapear recortes procesados al original.

## 8. RECONOCIMIENTO MULTIESCALA

Nivel 1 — Documento completo: identificar distribución, títulos, columnas y regiones; sugerir materia sólo como hipótesis.
Nivel 2 — Regiones: aplicar el motor más apropiado a cada recorte.
Nivel 3 — Recortes difíciles: ampliar, variar contraste, usar otro motor y conservar alternativas.
Nivel 4 — Contexto: VLM reorganiza contenido y relaciones, sin completar texto no verificable visualmente.

Ejemplos obligatorios de salida: texto con acentos; fórmulas LaTeX correctas; diagramas conservados; tablas estructuradas cuando sea seguro, o preservadas como imagen.

## 9. MULTIENGINE, ENRUTAMIENTO Y CONSENSO

Crear una interfaz común de motores, por ejemplo:

class RecognitionEngine:
    def is_available(self) -> bool: ...
    def get_capabilities(self) -> dict: ...
    def get_model_info(self) -> dict: ...
    def recognize(self, image, options): ...

Implementar RecognitionManager y ModelRegistry:
- Descubrimiento de motores instalados.
- Selección por tipo de región y perfil.
- Timeouts y reintentos limitados.
- Fallback ante modelo no instalado, timeout u OOM.
- Guardado de candidatos alternativos.
- Evaluación de contradicciones.
- Comparación con evidencia visual.

No tratar la votación mayoritaria como verdad. Dos motores pueden cometer el mismo error.

Perfiles:
- Rápido: procesamiento tradicional y conservador.
- Equilibrado: OCR documental + matemático según regiones.
- Avanzado: OCR + VLM local + validación multietapa.
- Automático: selecciona según complejidad y hardware.

## 10. RECONOCIMIENTO MANUSCRITO (HTR)

Requisitos:
- Soporte real y evaluado para español.
- Acentos, puntuación, números y símbolos frecuentes.
- Escritura inclinada, irregular y de varios tamaños.
- Regiones pequeñas, notas marginales y variación de iluminación.
- Separación adecuada de líneas y párrafos.
- Marcado de palabras ilegibles y alternativas.

No basar la validación sólo en tipografías que simulan manuscritos: se requieren fotos reales.

## 11. OCR MATEMÁTICO

Reconocer y, cuando sea viable, producir LaTeX de:
- Derivadas, integrales, límites, sumatorias.
- Fracciones, radicales, potencias y subíndices.
- Vectores y notación con i, j, k.
- Matrices y sistemas de ecuaciones.
- Funciones trigonométricas.
- Fórmulas eléctricas.

Ejemplo objetivo:
\vec{v}(t)=\frac{d\vec{r}(t)}{dt}

Preservar recorte original, validar que LaTeX renderice y permitir editarlo. No cambiar el sentido de una expresión sólo porque parezca matemáticamente incorrecta. Marcar signos dudosos sin alucinarlos.

## 12. DIAGRAMAS, GRÁFICAS Y TABLAS

Prioridad:
1) Preservar el diagrama completo y legible.
2) Extraer etiquetas y leyendas sin destruirlo.
3) Identificar relaciones y describirlas con cautela.
4) Reconstruir vectorialmente sólo cuando exista evidencia y validación.

Tipos: circuitos, fuentes, resistencias, flechas, polaridades, nodos, ejes, curvas, vectores, tablas, mapas conceptuales, diagramas de flujo y redes.

Si la reconstrucción estructurada es dudosa, incrustar el recorte original y señalar la limitación. No inventar conexiones eléctricas ni etiquetas.

## 13. DOCUMENTO ESTRUCTURADO Y RECONSTRUCCIÓN

Crear DocumentReconstructionEngine con esquema tipado Pydantic. El contenido original debe ser distinto del contenido reinterpretado o generado.

Ejemplo conceptual de formato JSON:

{
  "document_id": "doc_001",
  "title": "Derivada de vectores",
  "pages": [
    {
      "page_number": 1,
      "regions": [
        {
          "id": "r1",
          "type": "title",
          "text": "Derivada de vectores",
          "bbox": [100, 80, 700, 140],
          "reading_order": 1,
          "status": "recognized",
          "engine": "multimodal"
        },
        {
          "id": "r2",
          "type": "formula",
          "latex": "\\vec{r}(t)=x(t)\\hat{i}+y(t)\\hat{j}+z(t)\\hat{k}",
          "reading_order": 2,
          "status": "needs_review",
          "source_crop": "regions/r2.png"
        },
        {
          "id": "r3",
          "type": "diagram",
          "description": "Representación gráfica de un vector en el espacio.",
          "reading_order": 3,
          "status": "preserved_as_image",
          "source_crop": "regions/r3.png"
        }
      ]
    }
  ]
}

El contrato definitivo debe respetar la estructura existente del proyecto e incorporar migración cuando corresponda.

Campos recomendados: esquema/versionado, ID, páginas, idioma, dimensiones, regiones, texto original, candidatos, source_crop, transformaciones, relaciones, autor de corrección, procedencia, estado y motor/versión.

## 14. VALIDACIÓN Y CONTROL DE ALUCINACIONES

Crear RecognitionValidationEngine:
- Detectar regiones sin reconocer, duplicadas o contradictorias.
- Comprobar asociación de texto a regiones reales.
- Verificar sintaxis y renderizado de LaTeX.
- Comparar candidatos contra imagen/recorte original.
- Rechazar resultados que no tengan suficiente evidencia.
- Conservar alternativas y permitir revisión manual.

Estados:
RECOGNIZED, NEEDS_REVIEW, PARTIALLY_RECOGNIZED, UNREADABLE, PRESERVED_AS_IMAGE, USER_CORRECTED.

Nunca completar información ilegible simplemente por contexto. La corrección ortográfica y el razonamiento académico deben estar fuera de la transcripción fiel.

## 15. MODOS DE CONTENIDO

Modo transcripción fiel:
- Preservar lo escrito, incluso posibles errores del alumno.
- No resolver ejercicios ni editar conceptos.
- Conservar diagramas y marcar ambigüedades.

Modo apunte organizado:
- Ordenar títulos, listas, fórmulas, tablas y diagramas.
- Permitir comparar con el original.
- Mantener historial y trazabilidad de cambios.

Modo explicación asistida (opcional/futura fase):
- Explicar contenido usando modelo local.
- Marcar claramente contenido generado por IA.
- Nunca sustituir silenciosamente el original.

## 16. FRONTEND: EDICIÓN Y REVISIÓN VISUAL

Ampliar el editor existente con vista dividida:
- Izquierda: fotografía y regiones resaltadas.
- Derecha: apunte digital editable.

Funciones:
- Elegir modo rápido, equilibrado, avanzado o automático.
- Mostrar disponibilidad de motores y modelos.
- Mostrar progreso/errores del trabajo.
- Seleccionar bloque y resaltar región correspondiente.
- Editar texto, LaTeX y orden de lectura.
- Previsualizar fórmulas matemáticas.
- Confirmar/rechazar candidatos.
- Reprocesar sólo una región sin rehacer todo el documento.
- Recuperar recorte original.
- Guardar correcciones con historial.
- Funcionar de forma razonable en móvil.

## 17. PDF Y EXPORTACIÓN

Mantener el generador actual, mejorándolo para usar el documento estructurado en vez de concatenar texto OCR.

Exportaciones:
- PDF fiel al original (conservación prioritaria).
- PDF académico (presentación limpia).
- PDF con imágenes originales de apoyo.
- HTML y TXT cuando corresponda.

Requisitos:
- Fórmulas renderizadas o preservadas como imagen.
- Tablas legibles y diagramas nítidos.
- Márgenes, saltos de página y fuentes con acentos.
- Sin duplicaciones o pérdida de bloques confirmados.
- Multipágina.
- Trazabilidad de imágenes originales.
- Vista previa y descarga.

## 18. EJECUCIÓN GRATUITA Y PERFILES DE HARDWARE

Modo básico CPU:
- OpenCV + Tesseract/alternativas ligeras.
- La app debe seguir funcionando sin VLM.

Modo equilibrado:
- OCR documental y matemático cuando el hardware lo permita.

Modo avanzado:
- VLM multimodal local, OCR especializado y validación por regiones.
- Posible GPU, RAM/VRAM considerable y tiempos de inferencia superiores.

Implementar diagnóstico de RAM, GPU, modelos y runtime disponibles. No cargar un modelo enorme sin validar recursos. Documentar claramente que el software/modelos gratuitos no equivalen a cómputo gratuito.

## 19. OLLAMA / INFERENCIA LOCAL

Agregar proveedor opcional de inferencia por Ollama (o runtime alternativo justificado).

Requisitos:
- Detectar instalación, versión y servicio.
- Listar modelos instalados y validar soporte visual.
- Configurar URL/modelo/timeouts.
- Manejar fallos, reintentos y límites de concurrencia.
- Limitar entrada y tamaño de imágenes.
- Validar salidas JSON y recuperar respuestas incompletas.
- No descargar nada sin consentimiento del administrador.

Variables propuestas (adaptar a convenciones existentes):

APUNTIA_AI_ENABLED=true
APUNTIA_AI_PROVIDER=ollama
APUNTIA_OLLAMA_HOST=http://127.0.0.1:11434
APUNTIA_VLM_MODEL=qwen3-vl:4b
APUNTIA_RECOGNITION_MODE=auto
APUNTIA_OCR_FALLBACK=tesseract
APUNTIA_MATH_ENGINE=auto
APUNTIA_MAX_CONCURRENT_INFERENCES=1
APUNTIA_AI_TIMEOUT_SECONDS=180
APUNTIA_PRESERVE_ORIGINAL=true
APUNTIA_ALLOW_EXTERNAL_AI=false

Ejemplo opcional para verificar instalación del modelo, previa confirmación de etiqueta compatible con Ollama:
ollama pull qwen3-vl:4b

No asumir que una etiqueta de modelo existe sin verificarla al implementar.

## 20. COLA Y PROCESAMIENTO DE TRABAJOS

Las inferencias pesadas no deben bloquear el event loop de FastAPI. Diseñar un Job Manager con cola/control de procesos o workers adecuados, persistencia si se requiere y cancelación cuando sea posible.

Estados:
PENDING, PREPROCESSING, DETECTING_REGIONS, RECOGNIZING_TEXT, RECOGNIZING_FORMULAS, ANALYZING_DIAGRAMS, MULTIMODAL_PROCESSING, VALIDATING, RECONSTRUCTING, COMPLETED, FAILED, CANCELLED.

Requisitos:
- ID de trabajo y seguimiento.
- Progreso e historial.
- Reintentos limitados e idempotencia.
- Gestión de timeouts y OOM.
- Cancelación y liberación de recursos.
- Límites de concurrencia.
- Conservación del original ante fallo.

## 21. API (PROPUESTA, SUJETA A REVISIÓN)

GET  /api/v2/recognition/engines
GET  /api/v2/recognition/profiles
POST /api/v2/recognition/jobs
GET  /api/v2/recognition/jobs/{job_id}
GET  /api/v2/recognition/jobs/{job_id}/result
POST /api/v2/recognition/jobs/{job_id}/regions/{region_id}/retry
POST /api/v2/recognition/jobs/{job_id}/cancel

Usar contratos Pydantic y autenticación/autorización existentes. Reutilizar rutas equivalentes si ya existen; no duplicarlas. Documentar entradas, errores y respuestas.

## 22. ESTRUCTURA PROPUESTA (ADAPTAR AL REPOSITORIO)

back/motori_magenes/app/services/recognition/
  __init__.py
  manager.py
  engine_base.py
  model_registry.py
  image_analyzer.py
  layout_analyzer.py
  region_detector.py
  text_recognizer.py
  handwriting_recognizer.py
  math_recognizer.py
  diagram_analyzer.py
  multimodal_reasoner.py
  result_aggregator.py
  validation_engine.py
  document_reconstructor.py
  schemas.py
  engines/
    tesseract_engine.py
    paddle_engine.py
    paddle_vl_engine.py
    trocr_engine.py
    pix2text_engine.py
    ollama_vlm_engine.py

fullstack/config/.env.example
fullstack/scripts/verificar_modelos.py
fullstack/scripts/diagnostico_ia.py
fullstack/evaluacion/multimodal/manifest.json
fullstack/evaluacion/multimodal/evaluar.py

docs/reconocimiento-multimodal.md
docs/modelos-ia.md
docs/instalacion-ia-local.md
docs/arquitectura-ia.md
docs/evaluacion-multimodal.md
docs/limitaciones-ia.md

Esta estructura es orientativa. Agrupar o reutilizar módulos según las convenciones reales. Evitar archivos vacíos o redundantes sólo para cumplir una lista.

## 23. EVALUACIÓN CON TRES CASOS REALES

Caso A — Algoritmos de agrupamiento:
- Manuscritos de diferente tamaño.
- Direcciones IP/MAC, distancia euclidiana, K1/K2/K3.
- Tabla de datos cuantitativos y cualitativos.
- Diagrama de red, flechas y notas.

Caso B — Cálculo III:
- Derivadas de vectores.
- Posición, velocidad y aceleración.
- Funciones trigonométricas y LaTeX.
- Gráficas y ejes.

Caso C — Circuitos eléctricos:
- Resistencias, fuentes, nodos, mallas, voltajes y corrientes.
- Fórmulas y polaridades.
- Diagramas y anotaciones relacionadas.

Crear datos de referencia transcritos y verificados por humanos. Las fotografías que el usuario compartió por chat no están automáticamente dentro del repositorio: incorporarlas únicamente como archivos de prueba con autorización y revisar privacidad/licencias.

## 24. MÉTRICAS Y BENCHMARKS

Texto:
- CER (Character Error Rate).
- WER (Word Error Rate).
- Cobertura, omisiones, duplicaciones y contenido inventado.

Fórmulas:
- Exactitud LaTeX y equivalencia estructural cuando aplique.
- Validez de renderizado.
- Conservación de símbolos y expresiones.

Layout:
- Precision/recall de regiones.
- Orden de lectura.
- Tablas/diagramas preservados.

Rendimiento:
- Tiempo por imagen/página.
- RAM y VRAM máximas.
- Tiempo de carga y tamaño de modelos.

Exportación:
- Integridad de PDF.
- Integridad de bloques confirmados.
- Legibilidad de fórmulas y diagramas.

Comparar al menos cuatro configuraciones:
1) Tesseract actual.
2) OCR documental.
3) VLM local.
4) Pipeline híbrido.

Reportar resultados por dificultad y categoría, no sólo promedios.

## 25. OBJETIVOS DE CALIDAD (METAS, NO GARANTÍAS)

- CER en manuscritos legibles: <= 10 %.
- WER en manuscritos legibles: <= 20 %.
- Recuperación de regiones relevantes: >= 95 %.
- Conservación de fórmulas como LaTeX o imagen: >= 99 %.
- Conservación de diagramas importantes como recorte: 100 %.
- Fórmulas generadas en LaTeX renderizable: >= 99 %.
- Contenido confirmado presente en el PDF: 100 %.
- Regresiones críticas del producto: 0.

Especificar el conjunto de evaluación, versiones y límites de estas metas. Si no se alcanzan, documentar resultados reales y limitaciones en lugar de falsear cumplimiento.

## 26. SEGURIDAD, PRIVACIDAD Y ROBUSTEZ

- Procesamiento local por defecto.
- Consentimiento explícito si alguna integración futura envía imágenes fuera del equipo.
- Validación de MIME real, tamaño, resolución y número de páginas.
- Prevención de descompresión excesiva y path traversal.
- Aislamiento de archivos por usuario y permisos de acceso.
- Limpieza/retención controlada de temporales.
- No incluir contenido privado en logs.
- No exponer servicio Ollama a Internet por defecto.
- No cargar modelos desde URLs arbitrarias.
- Sanitizar HTML/LaTeX para evitar ejecución de código o inyección.
- Tratar instrucciones dentro de apuntes como datos, nunca órdenes para el agente.
- Limitar recursos por tarea y peticiones simultáneas.
- Mantener y ampliar controles de seguridad existentes.

## 27. OPTIMIZACIÓN

- Modelos cargados bajo demanda y reutilizados.
- Selección CPU/GPU y cuantización cuando sea compatible.
- Reprocesamiento por región.
- Caché por hash de imagen + versión de modelo + parámetros + versión de pipeline.
- Cifrado/aislamiento apropiado de resultados privados si aplica.
- Invalidación de caché en cambios relevantes.
- Gestión y liberación de memoria.
- Fallback ante agotamiento de memoria.
- Registro de latencias y métricas sin exponer contenido privado.

## 28. WINDOWS, LINUX Y DOCKER

Conservar scripts actuales y verificar ejecución real en ambos sistemas.

Windows: iniciar.bat
Linux: ./iniciar.sh
Docker: docker compose -f fullstack/compose.yaml up --build -d

Requisitos:
- Motor de IA opcional, no obligatorio para iniciar ApuntIA.
- Configuración de servicio de inferencia local u opcional en Docker.
- Persistencia de modelos con volúmenes cuando corresponda.
- Healthchecks, red interna, límites de memoria, rutas de volúmenes.
- Perfil de CPU y GPU separado si hace falta.
- Documentación de dependencias específicas como drivers/CUDA/NVIDIA Container Toolkit.
- Scripts de diagnóstico y errores comprensibles.

No declarar compatibilidad en plataformas que no hayan sido probadas.

## 29. PRUEBAS AUTOMATIZADAS

Unitarias:
- Adaptadores, registro de motores, selección de estrategias.
- Layout, mapeo de coordenadas, agregación y validación.
- Serialización y reconstrucción documental.
- LaTeX y fallback.
- Estados de tareas y errores.

Integración:
- API + OCR.
- API + VLM simulado.
- OCR matemático + reconstrucción.
- Editor + resultados.
- Documento estructurado + PDF.

E2E:
Subir imagen → procesar → revisar → corregir → guardar → descargar PDF.

CI:
- Tests normales sin descargar modelos pesados.
- Mocks/fixtures para contratos.
- Suite separada de benchmarks reales con modelos instalados.
- No reportar benchmarks de mocks como resultados de IA.

## 30. DOCUMENTACIÓN OBLIGATORIA

Actualizar README, requerimientos y guías:
- Arquitectura y flujo.
- Modelos soportados, licencias y versiones.
- Instalación de Python y dependencias externas.
- Instalación/configuración de Ollama y modelos seleccionados.
- Requisitos CPU/RAM/GPU/VRAM por perfil.
- Docker / Windows / Linux.
- Variables .env.
- Diagnóstico, troubleshooting y desinstalación.
- API y esquemas de respuesta.
- Métodos de evaluación y datos de referencia.
- Limitaciones conocidas y resultados reales.

Objetivo: cualquier desarrollador debe poder ejecutar el modo básico y, con hardware adecuado, habilitar el modo avanzado siguiendo documentación reproducible.

## 31. PLAN DE IMPLEMENTACIÓN Y PRS

Fase 1 — Auditoría y diseño
- [ ] Inspeccionar repositorio y contratos reales.
- [ ] Documentar arquitectura actual y propuesta.
- [ ] Definir benchmark y criterios de evaluación.

Fase 2 — Infraestructura y modelos
- [ ] Interfaz de motores y ModelRegistry.
- [ ] Integración Ollama y VLM local.
- [ ] Perfiles y detección de disponibilidad.
- [ ] Timeout, fallback y pruebas.

Fase 3 — OCR/HTR y layout
- [ ] Evaluar PaddleOCR/PaddleOCR-VL y HTR.
- [ ] Detección/segmentación por regiones.
- [ ] Enrutamiento por tipo de región.
- [ ] Benchmark frente a Tesseract.

Fase 4 — Matemáticas y diagramas
- [ ] Integrar OCR matemático y render de LaTeX.
- [ ] Preservar diagramas y extraer etiquetas.
- [ ] Probar con cálculo y circuitos reales.

Fase 5 — Reconstrucción y validación
- [ ] Documento estructurado.
- [ ] Agregador y verificador.
- [ ] Antialucinaciones y revisión humana.

Fase 6 — Frontend
- [ ] Vista original/editor.
- [ ] Resaltar regiones y editar fórmulas.
- [ ] Reintentar reconocimiento selectivo.
- [ ] Progreso y estados.

Fase 7 — PDF y exportación
- [ ] Integrar documento estructurado.
- [ ] PDF fiel y PDF académico.
- [ ] Probar diagramas, fórmulas y multipágina.

Fase 8 — Optimización, despliegue y calidad
- [ ] Caché, recursos y cola de trabajo.
- [ ] Docker, scripts y compatibilidad.
- [ ] Pruebas, benchmarks, documentación.

Cada fase debe tener PR(s), pruebas, capturas/evidencias y resumen técnico.

## 32. CRITERIOS DE ACEPTACIÓN

Reconocimiento:
- [ ] Mejora medible en manuscritos respecto a Tesseract actual.
- [ ] Modelo visual local configurable y funcionando en hardware compatible.
- [ ] Detección de regiones y conservación de orden de lectura.
- [ ] Fórmulas renderizables o preservadas en imágenes.
- [ ] Diagramas relevantes conservados en el resultado.
- [ ] Regiones ambiguas claramente marcadas, sin contenido inventado.

Producto:
- [ ] Procesa pizarrones y cuadernos.
- [ ] Soporta imágenes multipágina o series de fotografías.
- [ ] Permite revisar/corregir el resultado.
- [ ] Permite reprocesar regiones.
- [ ] Genera PDF legible y completo respecto a contenido confirmado.
- [ ] Conserva funcionalidades anteriores.
- [ ] No requiere API comercial.

Ingeniería:
- [ ] Arquitectura modular y configuración por perfiles.
- [ ] Manejo de errores/OOM, timeouts y fallback.
- [ ] Pruebas unitarias, integración y E2E.
- [ ] Benchmark real por categoría, con comparación anterior.
- [ ] Docker/scripts y documentación actualizados.
- [ ] Privacidad y seguridad revisadas.

## 33. DEFINICIÓN DE TERMINADO Y RESULTADO ESPERADO

NO cerrar sólo porque:
- Ollama quedó instalado.
- Un modelo reconoció una imagen sencilla.
- Se agregó un endpoint.
- Un mock pasó CI.
- Se generó un PDF con texto parcial.

Para cerrar se requiere:
1) Código integrado y revisado.
2) Arquitectura y modelos documentados.
3) Instrucciones reproducibles.
4) Suite automatizada pasando.
5) Evaluación real con apuntes manuscritos y fórmulas.
6) Resultados comparativos honestos (Tesseract vs alternativas vs híbrido).
7) Ejemplos de salida y PDF generado.
8) Evidencia de no regresión.
9) Limitaciones y tareas pendientes documentadas.

Flujo final:
Tomar foto → validar imagen → preprocesar → detectar regiones → OCR/HTR/matemáticas/VLM → comparar y validar → reconstruir documento → revisar y corregir → guardar → exportar PDF/HTML/TXT.

PRINCIPIO FUNDAMENTAL:
Precisión → Fidelidad → Conservación de información → Validación → Experiencia de usuario → Rendimiento.


## Evidencia visual

![Captura del Issue #91](%5BFULLSTACK%5D%5BIA%5D%5BOCR%5D%5BP0%5D%20Implementar%20motor%20multimodal%20avanzado%20de%20reconocimiento%2C%20interpretaci%C3%B3n%20y%20reconstrucci%C3%B3n%20inteligente%20de%20apuntes%20acad%C3%A9micos.png)
