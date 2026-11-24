# [BACK-28] Implementar reconocimiento adaptativo y recuperación asistida de texto manuscrito y fórmulas difíciles

- Numero de Issue: #84
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/84
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-10 11:04:04 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 12:14:32 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 12:14:32 -0600 (CDMX)
- Creacion UTC: 2026-11-10T17:04:04Z
- Cierre UTC: 2026-11-10T18:14:32Z

- Fecha de captura: 2026-11-24 12:09:02 -0600 (CDMX)
- [Captura original](%5BBACK-28%5D%20Implementar%20reconocimiento%20adaptativo%20y%20recuperaci%C3%B3n%20asistida%20de%20texto%20manuscrito%20y%20f%C3%B3rmulas%20dif%C3%ADciles-original.png)
- [Captura con metadatos](%5BBACK-28%5D%20Implementar%20reconocimiento%20adaptativo%20y%20recuperaci%C3%B3n%20asistida%20de%20texto%20manuscrito%20y%20f%C3%B3rmulas%20dif%C3%ADciles.png)

## Descripcion original

**Área:** Backend / Inteligencia Artificial / Visión por Computadora  
**Prioridad:** Alta  
**Etiquetas sugeridas:** `backend`, `ocr`, `ia`, `mejora`, `pruebas`  
**Estado inicial:** Todo  
**Dependencias:** BACK-12 (preprocesamiento), BACK-13 (OCR), BACK-14
(manuscritos), BACK-15 (fórmulas), BACK-16 (estructura), BACK-17 (modelo
de apunte) y FULL-19 (evaluación).  
**Integración con frontend:** FRONT-13 (corrección de texto), FRONT-14
(revisión de fórmulas y estructura) y FRONT-20 (mensajes de error).

## Problema actual

ApuntIA presenta dificultades al extraer información de fotografías con
letra manuscrita irregular, trazos unidos, poca iluminación,
inclinación, sombras, hojas cuadriculadas, símbolos matemáticos
pequeños, fracciones, exponentes, subíndices, raíces, matrices y
fórmulas mezcladas con texto. Un único motor OCR o un filtro global no
resuelve todos esos casos; incluso puede borrar trazos importantes o
confundir símbolos.

Este Issue NO sustituye los módulos básicos de OCR y reconocimiento
matemático ya planificados. Su propósito es mejorar su precisión
mediante un flujo adaptativo, medible y seguro, reutilizando los
servicios existentes y preservando la compatibilidad de ApuntIA.

## Objetivo general

Implementar una estrategia híbrida de reconocimiento que analice la
calidad y el tipo de contenido de cada región, seleccione técnicas de
preprocesamiento y motores especializados, compare resultados y produzca
una transcripción estructurada con indicadores de incertidumbre y
mecanismos de corrección. El sistema debe priorizar la fidelidad al
material original y nunca inventar texto o expresiones matemáticas
cuando no exista evidencia suficiente.

## Resultado funcional esperado

Al recibir una o varias fotografías de pizarrón o cuaderno, ApuntIA
deberá:

1.  Detectar problemas de calidad y decidir si puede procesar la imagen
    o debe solicitar una nueva fotografía.
2.  Localizar y separar regiones de texto, fórmulas, tablas, dibujos y
    otros elementos, manteniendo su orden de lectura.
3.  Aplicar preprocesamiento diferente según la región y conservar
    siempre el recorte original.
4.  Reconocer texto impreso y manuscrito en español, incluyendo acentos
    y signos, mediante el motor más adecuado para cada caso.
5.  Reconocer fórmulas matemáticas como expresiones estructuradas (por
    ejemplo, LaTeX), preservando su significado visual.
6.  Identificar fragmentos dudosos, mostrar alternativas cuando existan
    y permitir su revisión antes de generar el apunte y el PDF.
7.  Conservar la procedencia de cada fragmento: imagen, página,
    coordenadas, motor utilizado y versión del reconocimiento.
8.  Producir resultados comparables con un conjunto de pruebas y no
    empeorar los casos sencillos.

## Alcance y reglas para Claude

- Antes de modificar código, inspeccionar la rama de trabajo, la
  estructura REAL del repositorio, dependencias, endpoints, contratos,
  pruebas, scripts de ejecución, Docker y documentación. No asumir que
  existen carpetas, clases, modelos o endpoints específicos.
- Reutilizar y ampliar las implementaciones de BACK-12, BACK-13, BACK-14
  y BACK-15; evitar motores duplicados, lógica paralela innecesaria o
  cambios incompatibles.
- Mantener el comportamiento de los endpoints existentes, especialmente
  `POST /analisis` y `GET /salud` si continúan vigentes. Las nuevas
  capacidades deben exponerse mediante el contrato versionado acordado
  en BACK-21, sin cambiar silenciosamente respuestas anteriores.
- No introducir Spring Boot, servicios externos, bases de datos o nuevas
  herramientas solo por suposición: confirmar primero la arquitectura
  vigente.
- No hacer llamadas a servicios de OCR o IA en la nube sin configuración
  explícita y consentimiento del usuario para enviar sus imágenes.
- No utilizar un modelo generativo para rellenar palabras, números o
  símbolos ilegibles como si hubieran sido reconocidos. La investigación
  educativa y el enriquecimiento pertenecen a otra etapa y deben quedar
  claramente separados de la transcripción.
- No borrar ni sobrescribir las imágenes originales. No guardar
  fotografías o contenido privado en logs.
- Mantener funcionamiento en CPU cuando sea técnicamente viable; si se
  ofrece aceleración GPU, debe ser opcional y estar documentada.
- Antes de declarar terminado el Issue, ejecutar pruebas existentes y
  nuevas; documentar cualquier limitación, fallo o incompatibilidad
  real.

## Actividades técnicas

### 1. Auditoría y línea base del reconocimiento

- [ ] Revisar el flujo actual desde la carga de imágenes hasta la
  extracción de texto, fórmulas y exportación.
- [ ] Identificar motores OCR instalados, versiones, modelos, rutas de
  Tesseract y requisitos de ejecución en Windows y Linux.
- [ ] Localizar errores reproducibles: texto omitido, letras
  confundidas, fórmulas incompletas, lectura desordenada y resultados
  vacíos.
- [ ] Registrar ejemplos de entrada, salida actual, salida esperada y
  causa probable del fallo.
- [ ] Medir una línea base de calidad y tiempo antes de modificar los
  algoritmos.
- [ ] Documentar las decisiones de arquitectura para evitar duplicar lo
  ya implementado.

### 2. Crear un conjunto de evaluación de apuntes difíciles

- [ ] Reunir ejemplos autorizados y anonimizados de cuadernos,
  pizarrones y documentos con diferentes niveles de dificultad.
- [ ] Incluir letra cursiva, letra pequeña, palabras encimadas, tinta
  tenue, fotografías inclinadas, sombras y fondos cuadriculados.
- [ ] Incluir expresiones con fracciones, potencias, subíndices, raíces,
  letras griegas, sumatorias, integrales, ecuaciones y matrices.
- [ ] Incluir páginas con texto mezclado con fórmulas, tablas y
  diagramas.
- [ ] Crear transcripciones de referencia verificadas manualmente para
  texto y expresiones matemáticas.
- [ ] Separar casos de desarrollo y casos de evaluación final para
  evitar ajustar el sistema únicamente a los ejemplos conocidos.
- [ ] Guardar únicamente imágenes con permiso de uso; evitar subir datos
  personales reales al repositorio.
- [ ] Documentar cómo reproducir la evaluación y dónde se almacenan los
  ejemplos.

### 3. Diagnóstico automático de calidad de imagen

- [ ] Estimar desenfoque, contraste, resolución, iluminación desigual,
  rotación y perspectiva.
- [ ] Detectar cuándo la imagen está demasiado deteriorada para ofrecer
  una transcripción confiable.
- [ ] Devolver advertencias concretas, por ejemplo: “La fotografía está
  desenfocada” o “La fórmula es demasiado pequeña”.
- [ ] Permitir continuar bajo advertencia cuando sea razonable, sin
  afirmar que el reconocimiento será correcto.
- [ ] Registrar métricas de calidad sin almacenar contenido sensible en
  los logs.

### 4. Preprocesamiento adaptativo por región

- [ ] Conservar la imagen original y generar variantes controladas para
  OCR, sin alterar permanentemente la fuente.
- [ ] Evaluar corrección de perspectiva, rotación, iluminación,
  contraste local, ampliación y reducción moderada de ruido.
- [ ] Probar técnicas como CLAHE, umbralización adaptativa y corrección
  de sombras solo donde aporten mejoras verificables.
- [ ] Evitar operaciones morfológicas agresivas que destruyan puntos,
  acentos, signos menos, barras de fracción, exponentes y subíndices.
- [ ] Separar estrategias para texto impreso, manuscrito, tinta fina y
  contenido matemático.
- [ ] Comparar el resultado del reconocimiento sobre la imagen original
  y las variantes procesadas.
- [ ] Elegir la mejor variante por evidencia y no aplicar siempre el
  mismo filtro a toda la página.

### 5. Detección de regiones y orden de lectura

- [ ] Identificar bloques de texto, renglones, fórmulas aisladas o
  incrustadas, tablas y figuras.
- [ ] Conservar coordenadas y número de página para vincular cada
  resultado con su recorte original.
- [ ] Respetar columnas, encabezados, listas y orden de lectura.
- [ ] Evitar que las líneas de cuaderno, cuadrículas y bordes de tablas
  se interpreten como caracteres o símbolos matemáticos.
- [ ] Mantener los dibujos o esquemas como recortes cuando no sea
  posible interpretarlos de forma confiable.

### 6. Reconocimiento híbrido de texto manuscrito

- [ ] Evaluar el OCR actual frente a motores alternativos aptos para
  manuscritos (por ejemplo, TrOCR o modelos compatibles con español),
  sin asumir que un modelo entrenado para inglés reconocerá
  correctamente textos en español.
- [ ] Mantener Tesseract u otro motor adecuado para texto impreso si
  demuestra mejor rendimiento en ese tipo de región.
- [ ] Seleccionar motores por configuración y tipo de región, con una
  interfaz común para intercambiarlos sin modificar toda la aplicación.
- [ ] Implementar un segundo intento acotado cuando el primer resultado
  sea dudoso, sin bucles indefinidos ni costos descontrolados.
- [ ] Normalizar espacios y codificación Unicode sin alterar nombres,
  cifras, unidades o símbolos reconocidos.
- [ ] Conservar alternativas y fragmentos no reconocidos; no
  sustituirlos automáticamente por palabras supuestas.
- [ ] Verificar licencias, tamaños de modelos, versiones de bibliotecas
  y compatibilidad con los scripts y Docker existentes.

### 7. Reconocimiento especializado de fórmulas matemáticas

- [ ] Detectar fórmulas como regiones matemáticas, no procesarlas
  únicamente como párrafos de texto.
- [ ] Evaluar un motor de reconocimiento matemático imagen-a-LaTeX, como
  pix2tex u otra alternativa técnicamente compatible.
- [ ] Soportar, según el alcance evaluado, fracciones, exponentes,
  subíndices, raíces, ecuaciones, sumatorias, integrales, matrices y
  letras griegas.
- [ ] Distinguir caracteres visualmente similares: `1/l`, `0/O`, `x/×`,
  `-/=`, `ν/v`, signos y subíndices.
- [ ] Validar la sintaxis del LaTeX generado y comprobar que pueda
  renderizarse sin errores.
- [ ] Conservar la imagen original de la fórmula y ofrecer revisión
  cuando el resultado sea ambiguo.
- [ ] No modificar automáticamente valores numéricos ni “resolver” la
  fórmula como sustituto del reconocimiento.
- [ ] Comprobar que las fórmulas revisadas se mantengan correctas en el
  documento estructurado y en el PDF final.

### 8. Evaluación de confianza y revisión asistida

- [ ] Definir estados por región: `reconocido`, `requiere_revision` y
  `no_reconocido` (o equivalentes acordados con el contrato existente).
- [ ] Utilizar puntuaciones y reglas de calidad documentadas; no
  comparar directamente confianzas de motores diferentes sin
  calibración.
- [ ] Señalar la ubicación exacta del contenido dudoso y conservar su
  recorte para revisión.
- [ ] Ofrecer hasta varias alternativas de reconocimiento únicamente
  cuando los motores realmente las produzcan.
- [ ] Permitir que FRONT-13 y FRONT-14 muestren texto/fórmula, imagen
  original y campo de corrección.
- [ ] Preservar por separado la transcripción original, la corrección
  del usuario y el contenido educativo agregado posteriormente.
- [ ] Garantizar que la generación del PDF utilice la versión revisada o
  indique claramente los fragmentos pendientes.

### 9. Contrato de datos e integración

- [ ] Reutilizar el esquema de documento definido en BACK-17;
  versionarlo si es necesario.
- [ ] Para cada región, conservar: identificador, página, tipo,
  coordenadas, recorte, resultado, representación matemática si aplica,
  estado de revisión y procedencia.
- [ ] Registrar motor y versión, variante de preprocesamiento y
  advertencias cuando sea útil para diagnóstico.
- [ ] Coordinar el contrato con BACK-21 y el frontend antes de modificar
  las respuestas HTTP.
- [ ] Integrar con el flujo multipágina y con la generación de PDF de
  BACK-19/BACK-20.
- [ ] Evitar que un fallo en una sola región descarte todo el apunte;
  devolver resultados parciales y errores localizados.
- [ ] Mantener la protección de recursos y permisos de usuario definida
  en BACK-24.

### 10. Rendimiento, estabilidad y seguridad

- [ ] Establecer límites configurables de tamaño, resolución, número de
  páginas, tiempo de ejecución y reintentos.
- [ ] Evitar descargar modelos en cada solicitud; documentar la
  preparación inicial y el almacenamiento en caché.
- [ ] Evitar que los modelos pesados bloqueen indefinidamente la API;
  integrarse con el mecanismo de trabajos de BACK-27 si existe.
- [ ] Protegerse contra imágenes malformadas, consumo excesivo de
  memoria y archivos temporales abandonados.
- [ ] Validar y escapar de forma segura el LaTeX y los datos que se
  renderizan en HTML/PDF.
- [ ] Mantener un modo local sin servicios externos y documentar los
  requisitos de memoria y espacio.
- [ ] Evitar exponer rutas locales, trazas internas, tokens, datos
  personales o imágenes privadas en respuestas y registros.

### 11. Pruebas automatizadas y evaluación objetiva

- [ ] Añadir pruebas unitarias para selección de motores, selección de
  variantes, normalización, clasificación de regiones y estados de
  revisión.
- [ ] Añadir pruebas de integración con imágenes de texto manuscrito y
  fórmulas de diferente dificultad.
- [ ] Probar entradas vacías, imágenes corruptas, fórmulas ilegibles,
  texto mixto y ausencia de un motor opcional.
- [ ] Medir CER (tasa de error de caracteres) y WER (tasa de error de
  palabras) para texto con transcripción de referencia.
- [ ] Medir calidad de fórmulas mediante comparación de LaTeX
  normalizado y revisión visual de expresiones renderizadas; no depender
  únicamente de coincidencia literal.
- [ ] Comparar la versión anterior y la nueva en el mismo conjunto de
  evaluación y publicar resultados reproducibles.
- [ ] Medir tiempo y consumo de memoria en un equipo de referencia;
  registrar p50/p95 si el volumen de pruebas lo permite.
- [ ] Verificar que el reconocimiento de apuntes fáciles no sufra
  regresiones importantes.
- [ ] Ejecutar las pruebas existentes de OpenCV, FastAPI, frontend e
  integración; no eliminarlas para conseguir un resultado verde.
- [ ] Probar que el PDF generado conserve texto, símbolos, fórmulas y
  correcciones de usuario.

### 12. Documentación, entrega y Pull Request

- [ ] Documentar en README o documentación técnica la arquitectura de
  reconocimiento adaptativo y sus limitaciones.
- [ ] Explicar instalación local de los motores elegidos, versiones
  compatibles, modelos requeridos y cómo se obtienen.
- [ ] Integrar las nuevas dependencias en la instalación por scripts y
  en Docker, sin pasos manuales ocultos.
- [ ] Documentar parámetros configurables, comportamiento sin GPU,
  tiempos estimados medidos y requisitos mínimos comprobados.
- [ ] Agregar ejemplos antes/después, capturas de regiones dudosas y
  evidencia del PDF final.
- [ ] Incluir tabla de resultados comparativos, errores conocidos y
  mejoras futuras.
- [ ] Crear commits descriptivos y un Pull Request asociado a este
  Issue; no fusionar sin revisión y pruebas satisfactorias.
- [ ] Actualizar la bitácora con fecha, actividades, problemas,
  soluciones, pruebas y evidencias.

## Criterios de aceptación obligatorios

- [ ] Existe un flujo de reconocimiento adaptativo que procesa por
  separado texto manuscrito, texto impreso y fórmulas cuando
  corresponde.
- [ ] El sistema conserva imágenes originales y recortes de las regiones
  reconocidas.
- [ ] Los casos difíciles del conjunto de evaluación muestran una mejora
  cuantificable respecto a la línea base, documentada con CER/WER y
  ejemplos de fórmulas; el equipo acuerda un umbral realista tras medir
  la versión actual.
- [ ] No hay regresiones críticas en los casos sencillos ni en los
  endpoints existentes.
- [ ] Las fórmulas se almacenan como expresiones editables y
  renderizables cuando se reconocen; si no, quedan marcadas para
  revisión con su recorte original.
- [ ] Los resultados dudosos no se presentan como seguros ni se
  completan mediante invención de contenido.
- [ ] La interfaz puede recibir los estados de revisión y permitir
  correcciones mediante los contratos definidos.
- [ ] Las correcciones se reflejan en el apunte estructurado y en el PDF
  final.
- [ ] La instalación funciona en el modo por scripts y en el modo Docker
  previsto para ApuntIA, con requisitos documentados.
- [ ] Existen pruebas unitarias, de integración y de regresión que se
  ejecutan correctamente.
- [ ] El README y la documentación técnica explican motores, modelos,
  configuración, limitaciones y resultados de evaluación.
- [ ] El Pull Request muestra qué archivos cambian, por qué se cambian,
  cómo se probaron y qué resultados se obtuvieron.

## Entregables

1.  Módulo de diagnóstico de calidad de imagen y preprocesamiento
    adaptativo.
2.  Integración configurable de OCR impreso, OCR manuscrito y
    reconocimiento matemático.
3.  Detección de regiones, metadatos y estados de incertidumbre.
4.  Contratos de respuesta compatibles con la arquitectura vigente.
5.  Integración con edición/revisión y exportación PDF.
6.  Dataset de evaluación autorizado o fixtures reproducibles, con
    transcripciones de referencia.
7.  Pruebas automatizadas y reporte comparativo de precisión,
    rendimiento y regresiones.
8.  README/documentación actualizados para ejecución por scripts y
    Docker.
9.  Evidencias visuales, commits, Pull Request y bitácora.

## Ejemplos mínimos para demostrar la mejora

**Caso A — Cuaderno con letra irregular:** fotografiar una página con
renglones, sombras y palabras unidas. El sistema debe recuperar el texto
legible, respetar el orden y marcar las palabras inciertas.

**Caso B — Fórmulas complejas:** fotografiar ecuaciones con fracciones,
raíces, potencias y subíndices. El sistema debe reconocerlas como
expresiones matemáticas, permitir corregir LaTeX y conservarlas en el
PDF.

**Caso C — Página mixta:** fotografiar apuntes que mezclen explicación,
tabla, diagrama y ecuaciones. El sistema debe conservar la estructura,
asociar recortes y generar un documento coherente sin inventar datos.

**Caso D — Fotografía de baja calidad:** utilizar una imagen borrosa o
con texto demasiado pequeño. El sistema debe advertir que parte del
contenido no puede reconocerse, en lugar de producir una transcripción
falsa.

## Definición de terminado

El Issue solo se cierra cuando existe evidencia reproducible de mejora,
las funcionalidades anteriores siguen funcionando, los resultados
ambiguos pueden revisarse y el flujo completo desde la fotografía hasta
el PDF ha sido probado. Una demostración aislada con una sola imagen no
es suficiente.

## Evidencia visual

![Captura del Issue #84](%5BBACK-28%5D%20Implementar%20reconocimiento%20adaptativo%20y%20recuperaci%C3%B3n%20asistida%20de%20texto%20manuscrito%20y%20f%C3%B3rmulas%20dif%C3%ADciles.png)
