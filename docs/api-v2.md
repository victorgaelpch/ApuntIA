# Contrato de la API v2: apuntes, OCR, fórmulas, PDF y cuentas (FULL-15)

Versión del contrato: **2.0**. Complementa, sin sustituirlo, al contrato v1 ([`api.md`](api.md)).

## 0. Compatibilidad con v1 (no cambia)

| Ruta v1 | Garantía |
|---------|----------|
| `POST /analisis` | Mismo campo `file`, mismos parámetros, misma respuesta `image/png` y mismos errores. Sigue sin cuenta y sin guardar nada |
| `GET /salud` | Mismos campos. Se **añaden** campos nuevos (`ocr`, `base_datos`), nunca se quitan |
| `GET /`, `POST /imagen-memoria` | Sin cambios (la segunda sigue marcada como obsoleta) |
| Errores | Misma estructura `{"error": {"codigo", "mensaje"}}` en v1 y v2 |

Todas las rutas nuevas viven bajo **`/api/v2/`**. La documentación interactiva (`/docs`) muestra ambas versiones.

## 1. Arquitectura

```mermaid
flowchart LR
    subgraph Navegador
      UI["Frontend (/app/)"]
    end
    subgraph API["FastAPI"]
      V1["v1: /analisis, /salud"]
      AUTH["/api/v2/auth, /perfil"]
      AP["/api/v2/apuntes, /trabajos, /exportaciones"]
      TR["Gestor de trabajos durable (hilos + SQLite)"]
    end
    subgraph Servicios
      PRE["Preprocesado OpenCV por perfil (pizarrón/cuaderno)"]
      OCR["OCR Tesseract (impreso + manuscrito con fallback)"]
      FOR["Fórmulas → LaTeX validado"]
      EST["Estructura del apunte"]
      INV["Investigación opcional (con consentimiento)"]
      PDF["PDF (ReportLab)"]
    end
    DB[("SQLite: usuarios, sesiones, apuntes, versiones, trabajos")]
    FS[("Almacenamiento privado: originales, recortes, PDFs")]
    UI -- "cookie HttpOnly + X-CSRF-Token" --> AUTH & AP
    UI -- "sin cuenta" --> V1
    AP --> TR --> PRE --> OCR --> FOR --> EST --> PDF
    TR -.-> INV
    AUTH & AP & TR --> DB
    AP & TR --> FS
```

**Mismo origen.** Las cuentas usan una cookie `HttpOnly`, así que la interfaz con cuentas se sirve desde el mismo origen que la API: `http://localhost:8000/app/` en modo script, y detrás de un proxy en Docker. El modo v1 anónimo sigue funcionando desde cualquier origen (`file://`, `:5500`).

## 2. Modelo de dominio

| Entidad | Descripción | Pertenece a |
|---------|-------------|-------------|
| `usuario` | Cuenta: email, nombre, hash de contraseña, preferencias | — |
| `sesion` | Sesión activa (solo se guarda el **hash** del token) | usuario |
| `apunte` | Una nota: título, estado, versión actual | usuario |
| `pagina` | Foto original de una hoja o pizarrón, con su orden y tipo de fuente | apunte |
| `version` | Instantánea inmutable del **documento** (el modelo intermedio, sección 3) | apunte |
| `trabajo` | Tarea larga (análisis, investigación, exportación) con estado persistente | apunte, usuario |
| `exportacion` | PDF generado a partir de una versión concreta | apunte, versión |
| `archivo` | Fichero privado en disco (original, procesado, recorte, PDF), referido por id | usuario |

## 3. Documento: el modelo intermedio editable (BACK-17)

Una única representación JSON, validada y versionada. Separa **lo que hay en la foto** (`origen: "ocr"`), **lo que corrigió el usuario** (`editado: true`, conservando `texto_original`) y **lo que viene de fuera** (`ampliaciones`, nunca mezcladas con los bloques).

```json
{
  "esquema": "apuntia.documento/1",
  "titulo": "Derivadas",
  "paginas": [
    {"id": "p1", "orden": 1, "tipo_fuente": "cuaderno", "archivo_original": "a1", "archivo_procesado": "a2",
     "ancho": 1600, "alto": 1200, "advertencias": ["IMAGEN_BORROSA"]}
  ],
  "bloques": [
    {"id": "b1", "pagina": "p1", "orden": 1, "tipo": "titulo", "bbox": [120, 80, 900, 140],
     "origen": "ocr", "estado": "reconocido", "confianza": 0.93,
     "texto": "Derivadas", "texto_original": "Derivadas", "editado": false},
    {"id": "b2", "pagina": "p1", "orden": 2, "tipo": "formula", "bbox": [120, 300, 800, 380],
     "origen": "ocr", "estado": "incierto", "confianza": 0.61,
     "texto": "f'(x) = lim (f(x+h) - f(x)) / h", "latex": "f'(x) = \\lim \\frac{f(x+h) - f(x)}{h}",
     "latex_valido": true, "recorte": "a3", "editado": false},
    {"id": "b3", "pagina": "p1", "orden": 3, "tipo": "manuscrito", "bbox": [120, 420, 900, 520],
     "origen": "ocr", "estado": "no_reconocido", "confianza": 0.22,
     "texto": "", "recorte": "a4", "editado": false},
    {"id": "b4", "pagina": "p1", "orden": 4, "tipo": "tabla", "origen": "usuario", "estado": "reconocido",
     "tabla": {"encabezados": ["Función", "Derivada"], "filas": [["x^2", "2x"]]}, "editado": true}
  ],
  "ampliaciones": [
    {"id": "x1", "concepto": "Derivada", "texto": "…", "estado": "propuesta",
     "fuente": {"titulo": "Derivada", "url": "https://es.wikipedia.org/wiki/Derivada",
                "proveedor": "wikipedia", "consultado": "2026-11-10", "licencia": "CC BY-SA 4.0",
                "autor": "Colaboradores de Wikipedia"},
     "discrepancia": null}
  ]
}
```

| Campo | Valores | Regla |
|-------|---------|-------|
| `bloques[].tipo` | `titulo`, `texto`, `manuscrito`, `formula`, `tabla`, `imagen` | Una tabla tiene `tabla`; una imagen tiene `recorte` |
| `bloques[].origen` | `ocr`, `usuario` | Los bloques creados a mano son `usuario` |
| `bloques[].estado` | `reconocido` (confianza ≥ 0.80), `incierto` (0.50–0.80), `no_reconocido` (< 0.50) | Un `no_reconocido` **conserva el recorte** de la imagen y no inventa texto |
| `bloques[].bbox` | `[x0, y0, x1, y1]` en píxeles de la página procesada | Permite resaltar la región en la foto |
| `bloques[].editado` | bool | Si es `true`, el PDF usa `texto`/`latex` del usuario; `texto_original` se conserva |
| `bloques[].revision` | `null`, `lecturas_distintas`, `sin_confirmar`, `formula_sin_confirmar`, `calidad_insuficiente` | Por qué un bloque pide revisión aunque su confianza sea alta (BACK-28). Si no es `null`, el bloque es `incierto` |
| `bloques[].alternativas` | hasta 3 `{texto, latex?, confianza, variante}` | Otras lecturas **reales** del motor para el mismo fragmento; nunca texto inventado. Usar una es una corrección del usuario |
| `bloques[].procedencia` | `{motor, version, reconocimiento, variante, psm, lecturas}` o `null` | Motor y versión, versión del reconocimiento (`adaptativo/1`), preprocesado que dio el texto y lecturas comparadas |
| `paginas[].calidad` | `{nivel, metricas}` o `null` | `nivel`: `buena`, `aceptable` o `insuficiente`; `metricas`: solo números (resolución, nitidez, brillo, contraste, altura de letra, inclinación). Los códigos de aviso van en `advertencias`: `BAJA_RESOLUCION`, `IMAGEN_BORROSA`, `IMAGEN_OSCURA`, `BAJO_CONTRASTE`, `TEXTO_PEQUENO`, `ILUMINACION_DESIGUAL`, `IMAGEN_GIRADA`, `REPETIR_FOTO` |
| `ampliaciones[].estado` | `propuesta`, `aceptada`, `rechazada` | Solo las `aceptadas` van al PDF, en una sección aparte y citadas |
| `ampliaciones[].discrepancia` | texto o `null` | La fuente parece contradecir al apunte: se pide revisión, nunca se corrige el apunte |

El esquema se rechaza completo si no valida: no se guarda una versión a medias.

**Reglas de procedencia al guardar una edición** (`app/services/documento.py`, `fusionar`):
- En un bloque de OCR, el servidor **conserva** `pagina`, `bbox`, `origen`, `confianza`, `texto_original`, `latex_original`, `recorte`, `palabras_dudosas`, `alternativas`, `procedencia` y `revision` de la versión anterior, aunque el cliente envíe otros valores. `editado` se calcula comparando con el original.
- Los campos de BACK-28 (`revision`, `alternativas`, `procedencia`, `calidad`) son **opcionales**: los apuntes anteriores no los tienen y siguen siendo válidos con el mismo esquema `apuntia.documento/1`.
- Un bloque nuevo debe tener `origen: "usuario"`: no se pueden inventar bloques «de la foto».
- De una ampliación solo se puede cambiar `estado`; su texto y su fuente vienen de la investigación. Quitarla del cuerpo no la borra.

## 4. Autenticación y cuenta (BACK-23, BACK-24)

| Método | Ruta | Cuerpo | Respuesta |
|--------|------|--------|-----------|
| `POST` | `/api/v2/auth/registro` | `{email, nombre, password}` | `201 {usuario, csrf}` + cookie de sesión |
| `POST` | `/api/v2/auth/sesion` | `{email, password}` | `200 {usuario, csrf}` + cookie |
| `GET` | `/api/v2/auth/sesion` | — | `200 {usuario, csrf}` o `401` |
| `GET` | `/api/v2/auth/estado` | — | Siempre `200 {autenticado, usuario, csrf}` (`usuario` y `csrf` son `null` sin sesión). La interfaz lo usa para decidir qué mostrar sin provocar errores 401 |
| `DELETE` | `/api/v2/auth/sesion` | — | `204`, borra la sesión en el servidor |
| `POST` | `/api/v2/auth/recuperacion` | `{email}` | `202` **siempre** (no revela si la cuenta existe) |
| `POST` | `/api/v2/auth/recuperacion/confirmar` | `{token, password}` | `204`; invalida todas las sesiones |
| `PUT` | `/api/v2/auth/password` | `{actual, nueva}` | `204`; invalida las **demás** sesiones |
| `GET` | `/api/v2/auth/sesiones` | — | `200 {otras}`: sesiones abiertas en otros navegadores |
| `DELETE` | `/api/v2/auth/sesiones/otras` | — | `200 {cerradas}`: cierra las demás sesiones y conserva la actual |
| `GET` / `PATCH` | `/api/v2/perfil` | `{nombre?, preferencias?}` | `200 {usuario}`. Preferencias: `tipo_fuente` (`auto` por defecto, `pizarron` o `cuaderno`: tipo propuesto al subir fotos), `idioma_ocr` (`spa+eng`, `spa`, `eng`), `investigacion_permitida` (`false` por defecto; el servidor rechaza la investigación sin ella), `estilo_pdf` (`extendido`/`basico`), `incluir_complementos_pdf` (`true`) e `incluir_originales_pdf` (`false`): opciones propuestas al exportar. `usuario` incluye `creado` |
| `DELETE` | `/api/v2/perfil` | `{password}` | `204`; borra la cuenta, sus apuntes y sus archivos |

- **Contraseñas:** `scrypt` (N=2¹⁴, r=8, p=1) con sal aleatoria; mínimo 10 caracteres.
- **Sesión:** cookie `apuntia_sesion`, `HttpOnly`, `SameSite=Lax`, `Secure` si `COOKIE_SEGURA=1` (HTTPS); expira tras 12 h sin uso o 7 días en total. En la base solo se guarda el SHA-256 del token.
- **CSRF:** toda petición que modifica (`POST`, `PUT`, `PATCH`, `DELETE`) con cookie lleva la cabecera `X-CSRF-Token` con el valor `csrf` recibido; si no coincide → `403 CSRF_INVALIDO`.
- **Fuerza bruta:** 5 fallos por email o 20 por IP en 15 min → `429 DEMASIADOS_INTENTOS`.
- **Recuperación:** token aleatorio de un solo uso, válido 30 min, guardado como hash. Sin servidor de correo, el enlace se escribe en el **buzón de desarrollo** (`DATA_DIR/buzon/`), nunca en el log.
- **Autorización:** cada consulta filtra por el `usuario_id` de la sesión; un recurso ajeno responde **`404`** (igual que uno inexistente), para no revelar que existe.

## 5. Apuntes, trabajos y exportaciones (BACK-11, 21, 26, 27)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v2/apuntes` | Crea un apunte desde 1–20 fotos y lanza su trabajo de **análisis** (preprocesado → OCR → manuscritos → fórmulas). `multipart/form-data`: `paginas` (archivos, en orden), `tipos` (uno por página: `pizarron` o `cuaderno`), `titulo`. Cabecera opcional `Idempotency-Key`. → `202 {apunte, trabajo}` |
| `GET` | `/api/v2/apuntes` | Lista paginada: `?q=&estado=&tipo_fuente=&desde=AAAA-MM-DD&hasta=AAAA-MM-DD&pagina=1&por_pagina=20&orden=reciente\|antiguo\|titulo` → `{elementos, total, pagina, por_pagina}`. `q` busca en el título y en el texto (no en lo investigado); `%` y `_` se buscan literalmente |
| `GET` | `/api/v2/apuntes/{id}` | Apunte con su documento actual, su `version` y `ultimo_trabajo` (estado del análisis, investigación o exportación más reciente) |
| `PUT` | `/api/v2/apuntes/{id}/documento` | Guarda una versión nueva. Cabecera **`If-Match: <version>`** obligatoria; si otra edición se guardó antes → `409 CONFLICTO_VERSION` con la versión actual |
| `GET` | `/api/v2/apuntes/{id}/versiones` | Historial de versiones |
| `GET` | `/api/v2/apuntes/{id}/versiones/{n}` | Documento de una versión |
| `POST` | `/api/v2/apuntes/{id}/versiones/{n}/restaurar` | Crea una versión nueva igual a la `n` (no borra nada) |
| `DELETE` | `/api/v2/apuntes/{id}` | Cancela sus trabajos en curso y borra el apunte, sus versiones, trabajos y archivos |
| `GET` | `/api/v2/apuntes/{id}/estructura` | Apunte estructurado (BACK-19) de la versión actual o de `?version=n`: `{version, estructura: {titulo, secciones, resumen, conceptos, glosario, ejemplos, formulas, tablas, esquemas, pendientes, complementos, avisos}}`. Todo sale del documento: el resumen son frases **extraídas**, el glosario solo recoge definiciones escritas en el apunte, y lo investigado solo aparece en `complementos` (aceptado y con fuente) |
| `GET` | `/api/v2/apuntes/{id}/archivos/{archivo_id}` | Imagen original, procesada o recorte. Solo el propietario |
| `GET` | `/api/v2/apuntes/{id}/conceptos` | Conceptos del propio apunte que se podrían investigar (glosario, títulos, términos frecuentes) y `{disponible, proveedor}`. No consulta nada fuera |
| `POST` | `/api/v2/apuntes/{id}/investigacion` | `{consentimiento: true, conceptos: [1–8 palabras clave], idioma: "es"\|"en"}` → `202 {trabajo}` (tipo `investigacion`). Sin `consentimiento: true` o sin la preferencia `investigacion_permitida` → `400 CONSENTIMIENTO_REQUERIDO`; proveedor desactivado → `503 INVESTIGACION_NO_DISPONIBLE`. Cada concepto: ≤ 80 caracteres, ≤ 6 palabras, sin URLs, emails ni rutas |
| `PATCH` | `/api/v2/apuntes/{id}/ampliaciones/{aid}` | `{estado: "aceptada"\|"rechazada"\|"propuesta"}` (crea una versión; `If-Match` opcional). Solo cambia el estado: el texto y la fuente no se pueden editar |
| `POST` | `/api/v2/apuntes/{id}/exportaciones` | `{version?, estilo: "basico"\|"extendido", incluir_originales: false, incluir_complementos: true}` → `202 {exportacion, trabajo}` (tipo `exportacion`). Si ya existe un PDF de esa versión con esas opciones, o se está generando, lo reutiliza (`200`). Análisis en curso → `409 APUNTE_EN_PROCESO` |
| `GET` | `/api/v2/apuntes/{id}/exportaciones` | PDFs del apunte: `{id, version, opciones, estado, sha256, tamano, paginas, descarga}` |
| `GET` | `/api/v2/exportaciones/{id}` | Estado de una exportación |
| `GET` | `/api/v2/exportaciones/{id}/pdf` | Descarga (`application/pdf`, `Content-Disposition: attachment; filename="<titulo>-v<n>.pdf"`, `ETag` y `X-ApuntIA-Sha256`). Solo el propietario; si no está listo → `409 PDF_NO_LISTO` |
| `GET` | `/api/v2/trabajos/{id}` | `{id, tipo, estado, etapa, progreso, error, intentos}` |
| `DELETE` | `/api/v2/trabajos/{id}` | Cancela (`estado: cancelado`) |
| `POST` | `/api/v2/trabajos/{id}/reintentar` | Solo si `fallido` o `cancelado`; reutiliza el mismo trabajo |
| `POST` | `/api/v2/formulas/validar` | `{latex}` → `{valida, errores, vista_previa}` (PNG en base64). No requiere guardar |

### Estados de un trabajo

```mermaid
stateDiagram-v2
    [*] --> pendiente
    pendiente --> procesando
    procesando --> completado
    procesando --> fallido
    procesando --> parcial: alguna página falló
    pendiente --> cancelado
    procesando --> cancelado
    fallido --> pendiente: reintentar
    cancelado --> pendiente: reintentar
```

- `etapa` (dentro de `procesando`): `validando`, `preprocesando`, `ocr`, `formulas`, `estructurando`, `investigando`, `maquetando`.
- `parcial`: el análisis terminó, pero alguna página falló. El documento contiene las páginas buenas y `error` explica cuáles fallaron. **Nunca** es un `completado` con contenido fingido.
- **Durabilidad:** los trabajos viven en SQLite. Si el servidor se reinicia a mitad, al arrancar se vuelven a encolar (máximo 3 intentos).
- **Límites:** `MAX_TRABAJOS_SIMULTANEOS` (2) en el servidor y 3 trabajos pendientes por usuario → `429 DEMASIADOS_TRABAJOS`.
- **Idempotencia:** el mismo `Idempotency-Key` del mismo usuario devuelve el apunte ya creado; exportar dos veces la misma versión devuelve el mismo PDF.

## 6. Errores nuevos

Misma estructura `{"error": {"codigo", "mensaje"}}`, con un campo opcional `detalles` cuando hay varios fallos. Los mensajes son textos en español para el usuario; el frontend puede traducirlos por `codigo`.

| HTTP | `codigo` | Cuándo |
|------|----------|--------|
| 400 | `DATOS_INVALIDOS` | Cuerpo JSON o formulario con campos inválidos |
| 400 | `DOCUMENTO_INVALIDO` | El documento no cumple el esquema (la versión anterior queda intacta) |
| 400 | `DEMASIADAS_PAGINAS` | Más de `MAX_PAGINAS` (20) |
| 400 | `PAGINAS_INVALIDAS` (o el código de la única página que falla) | Alguna foto no es válida. No se guarda nada y `error.detalles` lista `{pagina, codigo, mensaje}` de cada una |
| 400 | `CONSENTIMIENTO_REQUERIDO` | Investigación sin consentimiento explícito |
| 400 | `LATEX_INVALIDO` / `LATEX_NO_PERMITIDO` | LaTeX que no se puede dibujar / con comandos peligrosos |
| 401 | `NO_AUTENTICADO` | Sin sesión o sesión caducada |
| 401 | `CREDENCIALES_INVALIDAS` | Email o contraseña incorrectos (mismo mensaje en ambos casos) |
| 403 | `CSRF_INVALIDO` | Falta o no coincide `X-CSRF-Token` |
| 403 | `ORIGEN_NO_PERMITIDO` | La cabecera `Origin` es de otro sitio |
| 404 | `NO_ENCONTRADO` | No existe **o no es tuyo** |
| 409 | `EMAIL_EN_USO` | Registro con un email ya usado |
| 409 | `CONFLICTO_VERSION` | `If-Match` no coincide con la versión actual |
| 409 | `APUNTE_EN_PROCESO` | Editar o restaurar mientras el análisis está en marcha (al terminar pisaría la edición) |
| 409 | `PDF_NO_LISTO` | Descargar un PDF que aún se genera o que falló |
| — | `APUNTE_VACIO` / `PDF_MAQUETACION` | Error de un trabajo de exportación (en `trabajo.error.codigo`): el apunte no tiene contenido o un elemento no cabe en la página. No se guarda ningún PDF |
| 409 | `TRABAJO_NO_REINTENTABLE` | Reintentar un trabajo que no falló ni se canceló |
| 413 | `CARGA_DEMASIADO_GRANDE` | El cuerpo supera `MAX_JSON_KB` (JSON) o `MAX_UPLOAD_MB × MAX_PAGINAS` (fotos) |
| 413 | `CUOTA_EXCEDIDA` | El usuario superó `CUOTA_MB_USUARIO` |
| 428 | `VERSION_REQUERIDA` | Falta `If-Match` |
| 429 | `DEMASIADOS_INTENTOS` / `DEMASIADOS_TRABAJOS` / `DEMASIADAS_PETICIONES` | Límites de abuso (ver docs/seguridad-api.md) |
| 507 | `ALMACENAMIENTO_LLENO` | El disco del servidor está lleno: no se guarda nada a medias (en un trabajo, aparece como su `error.codigo`) |
| 503 | `OCR_NO_DISPONIBLE` | Tesseract no está instalado: el análisis falla con este código, no con texto vacío |
| 503 | `INVESTIGACION_NO_DISPONIBLE` | Sin conexión con el proveedor o deshabilitado |

## 7. Privacidad e investigación externa

- Las fotos, el texto y los PDFs **no salen del servidor**, salvo en la investigación opcional.
- La investigación solo envía **los conceptos** elegidos (palabras clave), nunca la foto ni el texto completo, y solo con `consentimiento: true` y la preferencia `investigacion_permitida` del perfil activada.
- Cada ampliación guarda su URL, proveedor, autor, fecha y licencia; si no hay fuente, no se incluye.
- Proveedor (BACK-18): `INVESTIGACION_PROVEEDOR=wikipedia` (API REST pública de es/en.wikipedia.org, CC BY-SA 4.0) o `ninguno`. El servidor solo consulta esos hosts fijos (sin SSRF), con `INVESTIGACION_TIMEOUT_S` (6 s) y una caché en memoria de 200 conceptos durante 24 h.
- Lo externo es dato no confiable: se quita el HTML, se guarda solo un fragmento breve (≤ 600 caracteres, con atribución) y se descarta la página si contiene instrucciones dirigidas a un asistente.
- Las ampliaciones nacen como `propuesta`; solo las `aceptada` salen en el apunte estructurado y el PDF, en una sección aparte. Si la fuente da cifras distintas de las del apunte, la ampliación lleva `discrepancia` y el apunte **no** se corrige.
- Los logs de investigación guardan solo métricas (cuántos conceptos, resultados y fallos, y el tiempo), no los conceptos.
- La generación del apunte y del PDF funciona **sin Internet**.

## 8. Diagnóstico (FULL-21)

- `GET /salud` (viva): contrato v1 + `ocr: {disponible, motor, idiomas}`, `max_paginas`,
  `investigacion: {proveedor, disponible}` y `base_datos: {disponible}`. Siempre 200 si el proceso responde.
- `GET /api/v2/listo` (lista): `200 {listo: true, dependencias}` si funcionan todas las obligatorias
  (base de datos con todas las migraciones, almacenamiento escribible con espacio ≥ `MINIMO_DISCO_MB`,
  despachador de trabajos y OCR si `OCR_MOTOR` no es `ninguno`); si no, `503` con `mensaje` y el detalle
  de cada una. La investigación se informa pero es opcional.
- `GET /api/v2/diagnostico`: métricas (peticiones por ruta con p50/p95 y errores, trabajos por tipo con
  tasa de éxito, duración y códigos de error, pendientes, tamaño de los datos, memoria, límites). **Solo
  desde el propio equipo** (127.0.0.1/::1); desde fuera responde 404.
- Cada respuesta lleva `X-ApuntIA-Peticion-Id` (se respeta el que envía el cliente si es válido), que
  aparece en cada línea del log de esa petición y en la de los trabajos que crea. Los 5xx llevan
  además `X-ApuntIA-Error-Id`, y los trabajos fallidos, `error.referencia`; la interfaz los muestra como
  «Referencia: …». Ninguno contiene datos de la persona.

## 9. Decisiones

| Decisión | Alternativas evaluadas | Motivo |
|----------|------------------------|--------|
| Rutas `/api/v2/...` y v1 intacto | Cambiar `/analisis` para que devuelva JSON | Rompería a los clientes existentes y las 113 pruebas |
| Sesión con cookie `HttpOnly` + CSRF | JWT en `localStorage` | El token no es accesible desde JavaScript (mitiga XSS); se puede invalidar en el servidor |
| SQLite + carpeta privada | PostgreSQL | Proporcional a un proyecto académico, sin servidor extra; el acceso está aislado en `app/datos/` para poder migrar |
| Tesseract | PaddleOCR, EasyOCR, TrOCR | Apache-2.0, buen español, sin GPU ni descargas de cientos de MB; ver `PROCESAMIENTO.md` |
| Hilos + SQLite para trabajos | Celery + Redis | Sin servicios extra; durable y funciona igual en local y en Docker |
| ReportLab + mathtext | WeasyPrint, LaTeX | ReportLab no necesita librerías del sistema; mathtext dibuja LaTeX **sin ejecutar** un motor TeX |

## 10. Motores y perfiles de reconocimiento (FULL-30)

Requieren sesión. No exponen datos del equipo (RAM, GPU): eso solo aparece en `/api/v2/diagnostico`,
que responde únicamente desde el propio servidor. Guía: [`ia-local.md`](ia-local.md).

`GET /api/v2/reconocimiento/motores` → `200`

```json
{"motores": [
  {"nombre": "tesseract", "modelo": "LSTM (spa+eng)", "version": "5.3.4", "licencia": "Apache-2.0",
   "local": true, "detalle": "", "disponible": true,
   "capacidades": ["formula", "layout", "texto_impreso", "texto_manuscrito"]},
  {"nombre": "ollama_vlm", "modelo": "qwen3-vl:4b", "version": "", "licencia": "según el modelo (Qwen3-VL: Apache-2.0)",
   "local": true, "detalle": "desactivado (IA_ACTIVADA=false): opcional", "disponible": false,
   "capacidades": ["diagrama", "formula", "layout", "tabla", "texto_impreso", "texto_manuscrito"]}
]}
```

`GET /api/v2/reconocimiento/perfiles` → `200`

```json
{"configurado": "automatico", "aplicado_en_analisis": false,
 "perfiles": {
   "rapido":      {"disponible": true,  "motores": ["tesseract"], "flujo": "clasico", "detalle": ""},
   "equilibrado": {"disponible": true,  "motores": ["tesseract"], "flujo": "adaptativo", "detalle": ""},
   "avanzado":    {"disponible": false, "motores": ["tesseract", "ollama_vlm"], "flujo": "adaptativo+vlm",
                   "detalle": "desactivado (IA_ACTIVADA=false): opcional"},
   "automatico":  {"disponible": true, "elige": "equilibrado", "motores": ["tesseract"], "flujo": "adaptativo", "detalle": ""}},
 "memoria_vlm": "necesita ~6 GB (estimado); hay 7.4 GB libres"}
```

`aplicado_en_analisis: false`: el análisis de apuntes todavía sigue el flujo de BACK-28 sea cual sea
el perfil (se conecta en el siguiente PR). `/api/v2/listo` incluye la dependencia `ia_local`, que es
**opcional**: no cambia el estado «listo».
