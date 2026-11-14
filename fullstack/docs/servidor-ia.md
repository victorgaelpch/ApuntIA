# Servidor de inferencia de IA (BACK-35)

Servicio independiente, en el mismo repositorio (`ia_servidor/`), que corre en la **PC de casa
con GPU** y convierte UNA imagen en una transcripción estructurada con un modelo visual local
(Qwen3-VL en Ollama). La laptop del profesor sigue teniendo todo lo demás: cuentas, SQLite,
historial, editor y PDF. El servidor IA **no** tiene usuarios, base de datos ni almacenamiento.

> Estado (13/11/2026): implementado, 40 pruebas con Ollama simulado y **probado en la PC
> destino** (Windows 11, RTX 3060 12 GB, controlador 621.14, Ollama 0.40.16, `qwen3-vl:8b`
> Q4_K_M). Medición real en §8: el texto impreso y el manuscrito sintético se leen sin errores,
> pero la variante `qwen3-vl:8b` es **«thinking»** y en fórmulas se queda razonando sin responder.
> Pendiente: probar `qwen3-vl:8b-instruct` y fotos reales (BACK-36).

## 1. Arquitectura

```
LAPTOP (ApuntIA cliente)                          PC DE CASA (servidor IA)
back/motori_magenes  ──HTTPS (túnel, FULL-31)──▶  ia_servidor  127.0.0.1:8100
  cuentas, SQLite,                                   │ valida, mide calidad (OpenCV del backend)
  historial, PDF                                     ▼
                                                  Ollama  127.0.0.1:11434  (nunca expuesto)
                                                     └─ qwen3-vl:8b  (respaldo qwen3-vl:4b)
```

| Pieza | Archivo | Responsabilidad |
|-------|---------|-----------------|
| Configuración | `ia_servidor/config.py` | Variables `IA_*`; se niega a arrancar si es insegura |
| API | `ia_servidor/app.py` | Rutas, correlación, cabeceras, errores |
| Análisis | `ia_servidor/servicio.py` | Cola, inferencia, reintento de JSON, respaldo ante OOM |
| Imagen | `ia_servidor/imagen.py` | Tamaño, firma, cabecera (antibomba), decodificación, reducción |
| OpenCV compartido | `ia_servidor/compartido.py` | Importa `calidad.py` y `perspectiva.py` del backend, sin copiarlos |
| Ollama | `ia_servidor/ollama.py` | Cliente HTTP con rutas permitidas y errores tipados |
| GPU | `ia_servidor/gpu.py` | `nvidia-smi` (informativo, en caché 30 s) |

**Reutilización sin divergencia.** El diagnóstico de calidad (nitidez por varianza del
Laplaciano, contraste, resolución, altura de letra) y la detección de la hoja (Canny/Otsu +
cuadriláteros) son los mismos módulos del backend (BACK-04, BACK-28), importados desde su ruta.
`test_no_importa_bd_ni_config_del_cliente` comprueba en un proceso limpio que eso no carga
`app.core.config`, `app.datos`, las cuentas ni `sqlite3`. La validación de entrada sí es propia
porque la del backend depende de su configuración y de `UploadFile`.

## 2. Arranque

```bash
pip install -r ia_servidor/requirements.txt -c back/motori_magenes/constraints.txt
python -m ia_servidor          # desde la raíz; escucha en 127.0.0.1:8100
```

Configuración por variables de entorno; plantilla sin secretos en `ia_servidor/.env.example`.
La instalación guiada de Ollama y del modelo es tarea de FULL-30 (`instalacion-servidor-ia.md`).

## 3. Contrato HTTP v1 (`api_version` 1.0)

Toda respuesta lleva `X-ApuntIA-Id-Correlacion`, `Cache-Control: no-store` y
`X-Content-Type-Options: nosniff`.

| Método y ruta | Respuesta |
|---------------|-----------|
| `GET /salud` | `200 {"estado":"ok","servicio":"apuntia-ia","api_version":"1.0"}` — solo dice que el proceso vive |
| `GET /listo` | `200`/`503` con `componentes`: `ollama` (versión ≥ 0.12.7), `modelo` (instalado, capacidad `vision`, cuantización), `modelo_respaldo`, `en_memoria` (VRAM de `/api/ps`), `disco`, `gpu`, `cola`; y `avisos` |
| `GET /api/v1/capacidades` | Tareas, formatos, límites, modelos y política de almacenamiento |
| `POST /api/v1/analisis?tarea=T` | Cuerpo = bytes de la imagen (`Content-Type: image/png`, `image/jpeg` o `image/webp`). **No** multipart |

Tareas: `pagina` (por defecto), `texto_impreso`, `texto_manuscrito`, `formula`, `tabla`, `diagrama`.

Respuesta 200 de `/api/v1/analisis`:

```json
{
  "api_version": "1.0", "pipeline_version": "1.0.0", "id_correlacion": "9cea5dddb14f4f33",
  "tarea": "formula",
  "modelo": {"nombre": "qwen3-vl:8b", "respaldo_usado": false},
  "imagen": {"formato": "png", "ancho": 2400, "alto": 1200, "bytes": 81234, "lado_enviado_al_modelo": 1600},
  "calidad": {"disponible": true, "nivel": "aceptable", "avisos": ["..."], "metricas": {"...": 0}, "hoja_detectada": false},
  "resultado": {
    "estado": "propuesta", "revision_requerida": true, "origen": "imagen",
    "texto": "...", "latex": "\\frac{d}{dx}x^2 = 2x", "descripcion": null,
    "dudas": ["la última letra podría ser «z»"]
  },
  "metricas": {"segundos_total": 4.1, "tokens_salida": 42, "segundos_modelo": 3.5, "segundos_carga": 1.0}
}
```

- `resultado.estado`: `propuesta` o `ilegible`. Siempre `revision_requerida: true`: un VLM no da
  una confianza calibrada, así que **no se devuelve ningún porcentaje**; las dudas del propio
  modelo van en `dudas`. La integración con los bloques `p{n}b{m}` del editor es BACK-36/BACK-38.
- Lo que no sea un JSON válido con ese esquema se rechaza (`RESPUESTA_INVALIDA`); nunca se
  «rellena» una respuesta incompleta ni se guarda como apunte.

### Errores

`{"error": {"codigo", "mensaje", "reintentable", "id_correlacion"}}`

| Código | HTTP | Reintentable | Causa | Qué hacer |
|--------|------|--------------|-------|-----------|
| `IMAGEN_VACIA` | 400 | no | Cuerpo vacío | Enviar la imagen |
| `IMAGEN_CORRUPTA` | 400 | no | Firma correcta pero no se decodifica | Repetir la foto |
| `FALTA_IMAGEN` | 400 | no | Se envió multipart | Enviar el cuerpo binario |
| `TAREA_INVALIDA` | 400 | no | Tarea desconocida | Ver `/api/v1/capacidades` |
| `IMAGEN_DEMASIADO_GRANDE` | 413 | no | > `IA_MAX_MB` (se corta al leer) | Reducir la imagen |
| `RESOLUCION_EXCESIVA` | 413 | no | > `IA_MAX_MEGAPIXELES` o bomba de descompresión | Reducir la imagen |
| `FORMATO_NO_SOPORTADO` | 415 | no | No es JPEG/PNG/WEBP por firma | Convertirla |
| `OCUPADO` | 429 | sí | Otra inferencia en curso más de `IA_ESPERA_COLA_S` | Esperar `Retry-After` |
| `RESPUESTA_INVALIDA` | 502 | sí | JSON del modelo fuera de contrato tras 1 reintento | Reintentar; si persiste, otra tarea o modelo |
| `NO_DISPONIBLE` | 503 | sí | Ollama apagado o caído | Iniciar Ollama |
| `MODELO_NO_INSTALADO` | 503 | no | Falta el modelo | `ollama pull qwen3-vl:8b` (administrador) |
| `SIN_MEMORIA` | 503 | sí | OOM de GPU (también con el respaldo) | Cerrar programas que usen la GPU; usar 4B |
| `TIEMPO_AGOTADO` | 504 | sí | > `IA_TIMEOUT_S` | Reintentar; imagen más pequeña |
| `ERROR_INTERNO` | 500 | sí | Excepción no prevista (traza solo en el log) | Revisar el log con el id |

### Compatibilidad cliente ↔ servidor

| Cliente | Servidor `api_version` | Resultado |
|---------|------------------------|-----------|
| Pide 1.x | 1.x | Compatible: los campos nuevos se añaden sin quitar los existentes |
| Pide 1.x | 2.x | Incompatible: el cliente (FULL-31) debe comprobar `api_version` en `/salud` y avisar |

Las APIs v1 (`/analisis`) y v2 del backend del cliente no cambian.

## 4. Límites y recursos

| Variable | Defecto | Motivo |
|----------|---------|--------|
| `IA_MODELO` | `qwen3-vl:8b` | 6,2 GB en Ollama (cuantización Q4_K_M según `/api/tags`), cabe en 12 GB con margen para el contexto |
| `IA_MODELO_RESPALDO` | `qwen3-vl:4b` | 3,3 GB; se usa UNA vez si el principal da OOM y está instalado |
| `IA_MAX_INFERENCIAS` | 1 | Una inferencia pesada a la vez en 12 GB de VRAM |
| `IA_ESPERA_COLA_S` | 20 | Después, 429 `OCUPADO` en vez de colgar la petición (la cola durable es BACK-37) |
| `IA_TIMEOUT_S` | 180 | Tope por inferencia |
| `IA_MAX_LADO_MODELO` | 1600 px | Se envía una copia reducida; la original no se modifica |
| `IA_MAX_MB` / `IA_MAX_MEGAPIXELES` | 10 / 40 | Igual de prudentes que el backend |
| `IA_KEEP_ALIVE` | `10m` | El modelo sale de la VRAM tras 10 min sin uso (libera la GPU para otros usos) |

Fuentes: <https://ollama.com/library/qwen3-vl> (tamaños, «requires Ollama 0.12.7»),
<https://docs.ollama.com/api/chat> (`images`, `format` con esquema, `keep_alive`),
<https://docs.ollama.com/faq> (Ollama escucha en 127.0.0.1:11434 por defecto).
Licencia del modelo: Apache-2.0 según la ficha de Qwen3-VL de Qwen; **verificarla** en la ficha
del modelo descargado (`ollama show qwen3-vl:8b --license`) antes de la entrega.

| `IA_NUM_CTX` | 8192 | El defecto de Ollama (4096) se agotó con imagen + respuesta en fórmulas (§8) |
| `IA_MAX_TOKENS` | 2048 | Tope de generación: un modelo «thinking» puede razonar sin fin (§8) |

Cifras reales de VRAM y latencia: §8.

## 5. Seguridad y privacidad

- Ollama solo en loopback: `IA_OLLAMA_URL` debe ser `http://127.0.0.1:…` o el servicio no arranca.
- El propio servicio solo escucha en 127.0.0.1 hasta que exista la vinculación autenticada de
  FULL-31; con `IA_HOST=0.0.0.0` sale con código 2 y un mensaje claro.
- Solo se llaman `/api/version`, `/api/tags`, `/api/show`, `/api/ps` y `/api/chat`; nunca
  `/api/pull`, `/api/delete` ni `/api/create`. Se rechazan los modelos `*cloud`.
- La imagen solo existe en memoria: el cuerpo se lee por trozos con límite (no multipart, que
  usa archivos temporales) y no se escribe nada en disco.
- Logs: método, ruta, estado, tiempo, tamaño, modelo y nº de caracteres. Nunca el texto
  reconocido, la imagen, cabeceras ni consultas (`test_logs_sin_contenido_de_la_imagen`).
- El texto de la foto es un DATO para el modelo: el prompt le ordena transcribir, no obedecer.

## 6. Decisiones

| Decisión | Alternativa descartada | Por qué |
|----------|------------------------|---------|
| Ollama + Qwen3-VL 8B | PyTorch/transformers en el servicio | Ollama gestiona CUDA, cuantización y descarga; el servicio queda ligero y sin CUDA en sus dependencias |
| Cuerpo binario | multipart | Sin temporales en disco y límite real de lectura |
| `urllib` para Ollama | `httpx`/`requests` | Sin dependencias nuevas; el transporte es inyectable para las pruebas |
| Importar calidad/perspectiva del backend | Copiarlas o crear un paquete `shared/` | Una sola versión sin reorganizar el backend; la prueba vigila que no arrastre la BD |
| Respaldo 4B automático solo ante OOM | Elegir el modelo por petición | La elección queda en el administrador; el cliente ve `respaldo_usado` |

## 7. Pruebas

```bash
python -m pytest ia_servidor/tests          # 40 pruebas, sin red ni GPU
```

Cubren: contrato de `/salud`, `/listo`, capacidades y análisis; JSON inválido con un reintento;
OOM con y sin respaldo; modelo ausente; Ollama caído; tiempo agotado; respuesta cortada;
vacío, PDF, GIF, PNG corrupto, tamaño, bomba de descompresión, multipart, tarea inválida; cola
llena (429 + `Retry-After`) y una sola inferencia simultánea; rutas de Ollama prohibidas; logs
sin contenido; configuración insegura; independencia de la BD del cliente; `nvidia-smi`.
Se ejecutan en `fullstack/scripts/validar.sh` y en la CI.

Pendiente en el equipo real (no simulable): inferencia con `qwen3-vl:8b`, pico de VRAM,
latencia por tarea, OOM real y calidad con fotos de prueba.

## 8. Medición real en la PC destino (13/11/2026)

Equipo: Windows 11 Pro 10.0.26200, RTX 3060 12 GB (controlador 621.14), Ollama 0.40.16,
`qwen3-vl:8b` (8,2 B parámetros, Q4_K_M, 6,2 GB). Comando reproducible, con el servidor en marcha:
`python -m ia_servidor.medir` (corpus **sintético** de `herramientas/corpus.py`, con verdad
generada por código; resultados en `fullstack/evaluacion/resultados/`, no versionado).

Configuración de esta primera tanda: la del servidor antes de añadir `IA_NUM_CTX`/`IA_MAX_TOKENS`
(contexto 4096 por defecto de Ollama).

| Muestra | Tarea | Resultado | Latencia | CER VLM | CER Tesseract (línea base) |
|---------|-------|-----------|----------|---------|----------------------------|
| impreso_cuaderno | texto_impreso | 200 | 132,8 s (en frío: carga del modelo) | 0 % | 0,68 % |
| cuaderno_con_sombra | texto_impreso | 200 | 35,3 s | 0 % | 0,68 % |
| cuaderno_cuadriculado | texto_impreso | 200 | 20,1 s | 0 % | 0,68 % |
| impreso_pizarron | texto_impreso | 200 | 38,5 s | 0 % | 0,68 % |
| pizarron_oscuro | texto_impreso | 200 | 43,0 s | 0 % | 0,68 % |
| pizarron_con_ruido | texto_impreso | 502 `RESPUESTA_INVALIDA` (cortada) | 51,0 s | — | — |
| manuscrito_cuaderno | texto_manuscrito | 200 | 20,6 s | 0 % | 0 % |
| manuscrito_dificil | texto_manuscrito | 200 | 22,2 s | 0 % | 5,56 % |
| formulas_pizarron | formula | 502 (cortada) | 65,1 s | — | — |
| formulas_2d | formula | 502 (cortada) | 63,4 s | — | — |
| diagrama | diagrama | 200, descripción prudente («círculo, flecha hacia un rectángulo, línea curva»), sin inventar | 21,4 s | — | — |

- **VRAM**: el modelo cargado ocupa 5,8 GB según `/api/ps` con contexto 4096 y 7,9 GB con
  16384. Pico de la GPU durante la tanda: 10,7 GB, incluidos ~3,6 GB que ya usaban otros
  programas del escritorio. Con un juego abierto que use más de ~4 GB de VRAM, es esperable `SIN_MEMORIA`.
- **Por qué es lento y por qué falla**: `ollama show` indica `renderer qwen3-vl-thinking` y
  «thinking default true». La API **ignora `think: false`** en esta variante (medido: sigue
  devolviendo razonamiento). Así, 147 caracteres de respuesta costaron hasta 2 505 tokens. En
  fórmulas, imagen + razonamiento agotaron el contexto de 4096 (`done_reason: length`).
  Con contexto 16384 el modelo razonó 50 000–68 000 caracteres durante ~6 min por imagen y
  **tampoco** terminó. Por eso existen ahora `IA_NUM_CTX` y `IA_MAX_TOKENS` (con ellos, el peor
  caso termina en un error acotado en vez de colgarse).
- `ollama show` declara `requires 0.30.0` para este modelo, aunque la página de la biblioteca
  dice 0.12.7. El servidor sigue exigiendo ≥ 0.12.7; con un Ollama más antiguo que 0.30 el modelo
  no carga y `/listo` lo indicaría como error de Ollama.

**Prueba de mitigación sin descargas** (mismo `qwen3-vl:8b`, prompt corto de una línea, sin
esquema JSON en `format`, contexto 8192, tope 2048 tokens): las tres muestras que fallaban
terminaron. `formulas_2d` dio 18,7 s, `rac{a}{b} + rac{c}{d}`, `\sqrt{x + 1}` y
`E = mc^2` correctos (CER 8,6 % contra la verdad, solo por espacios y llaves); `formulas_pizarron`,
6,0 s, transcripción literal (`a/b + c/d` tal como está dibujado); `pizarron_con_ruido`, 9,9 s
y CER 0 %. El razonamiento bajó de 10 000–68 000 a 500–860 caracteres. Conclusión: el disparador
es el prompt largo de reglas junto con el esquema JSON, no la imagen. El CER contra una cadena
LaTeX penaliza diferencias sin significado (`x^2` y `x^{2}`): las fórmulas deben compararse
normalizando el LaTeX o por equivalencia con SymPy (BACK-36).

Lectura honesta: el CER 0 % se obtuvo en un corpus **sintético y fácil** (texto dibujado con
fuentes). No permite afirmar nada sobre fotos reales de pizarrón; eso es BACK-36.
Siguiente paso propuesto: repetir la tanda con `qwen3-vl:8b-instruct` (mismo tamaño, sin
razonamiento) y, si mejora, hacerlo el modelo por defecto.
