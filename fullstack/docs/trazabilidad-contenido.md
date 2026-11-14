# Trazabilidad del contenido: de la foto al PDF (BACK-38)

Cada cosa que aparece en un apunte y en su PDF sabe **de dónde sale**. Esta guía resume las
procedencias, cómo se guardan y cómo se muestran. Contrato completo de la API: [api-v2.md](api-v2.md).

## 1. Procedencias

| Procedencia | Dónde se guarda | Cómo se ve en el editor | Cómo se ve en el PDF |
|-------------|-----------------|-------------------------|----------------------|
| **Transcripción del OCR local** | bloque con `origen: "ocr"`, `procedencia.motor = "tesseract"…`, `texto_original` intacto | «Reconocido 92 %», «Incierto…» | texto; «reconocimiento incierto: revisar» si lo es |
| **Propuesta del servidor IA** | bloque con `procedencia.motor = "ia_remota"`, `version` = modelo, `revision = "sin_confirmar"`, `confianza = null` | «Propuesta de IA · sin revisar» + recorte siempre visible | «propuesta del servidor IA: sin revisar» + recorte de la foto (ver §3) |
| **Revisada por la persona** | el mismo bloque con `revisado: true` (la procedencia NO cambia) | «Propuesta de IA · revisada» | «propuesta del servidor IA: revisada», sin recorte |
| **Corregida por la persona** | `editado: true`; `texto_original`/`latex_original` conservan lo reconocido | «corregido» | «corregido por ti» |
| **Sin leer** | `estado: "no_reconocido"`, `conservar_imagen: true` | «IA: sin leer» / recorte | el recorte como imagen, con su pie |
| **Investigación externa** | `ampliaciones[]` con `fuente` (título, URL fija, proveedor, autor, licencia, fecha de consulta) y `estado` propuesta/aceptada/rechazada | pestaña «Información complementaria» | sección aparte «Información complementaria» + «Fuentes»; solo las **aceptadas** |

`procedencia`, `revision`, `texto_original`, `latex_original`, `bbox` y `recorte` son inmutables para
el cliente (`INMUTABLES_OCR` en `app/services/documento.py`): el usuario no puede «convertir» una
propuesta de IA en transcripción confirmada cambiando la procedencia; solo puede revisarla o corregirla.

## 2. Qué se envía al servidor IA y qué no

Se envía la foto de la página (la necesita para leerla) y nada más: ni el correo, ni el nombre, ni el
título, ni el texto de otros apuntes. El resultado se guarda en `ia_resultados` con una clave
idempotente (usuario, apunte, página, archivo, pipeline) para no repetir la GPU; detalles en
[trabajos-remotos.md](trabajos-remotos.md).

## 3. Regiones divididas (BACK-38)

El servidor IA lee **regiones** (segmentación OpenCV). Con la foto real del pizarrón se vio que una
región puede devolver varias fórmulas y un título juntos, o un texto con líneas `$…$`. El editor y el
PDF admiten una fórmula por bloque, así que `dividir_lineas` (`app/services/analisis_remoto.py`):

- separa cada línea matemática en su propio bloque «fórmula» (sin `$`);
- deja juntas las líneas de texto seguidas en un bloque «texto»;
- reparte las dudas: las de una línea concreta («llaves desbalanceadas en la línea 2») a esa parte; las
  generales (`[?]`) a las partes que lo contienen, o a todas si no se sabe;
- mantiene el **mismo `bbox` y el mismo recorte** en todas las partes (ids `p…bN_1`, `p…bN_2`…).

No se reescribe nada: si el modelo corrigió la ortografía («Isosceles» donde el pizarrón dice «Isoscilos»),
eso queda como propuesta y el recorte permite verlo.

## 4. Qué se deriva y de dónde

El resumen extractivo, el glosario, los ejemplos, la lista de fórmulas y los **conceptos sugeridos para
investigar** solo salen de bloques **confirmados**: OCR local, propuestas de IA revisadas o corregidas.
Una propuesta de IA sin revisar aparece en la transcripción (marcada y con su recorte) y en ningún
otro sitio, para que un error del modelo no se propague a otras secciones ni a búsquedas externas.

## 5. Pruebas

- `tests/test_analisis_remoto.py`: división multilínea (unitaria y de extremo a extremo con el servidor
  IA en proceso), procedencia y `revisado` que el cliente no puede falsear.
- `tests/test_pdf.py`: etiquetas IA, recorte una sola vez por región, opción `incluir_recortes_ia`,
  derivados sin propuestas sin revisar.
- `tests/test_investigacion.py`: conceptos sugeridos solo de lo confirmado.
