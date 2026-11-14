# Modelos y requisitos de ApuntIA 3.0 (FULL-32)

Qué hace falta en cada equipo, qué modelos se usan, con qué licencia y **cuánto consumen medido** en
la PC del servidor. Las cifras llevan fecha; si cambias de modelo o de controlador, vuelve a medir con
`fullstack\scripts\validar.ps1 -Gpu`.

## 1. Dos perfiles

| | Laptop del profesor (cliente) | PC de casa (servidor IA) |
|---|---|---|
| Qué ejecuta | ApuntIA web + backend local + base de datos, historial y PDF + cliente del servidor IA | FastAPI del servidor IA (`ia_servidor`) + OpenCV + Ollama con Qwen3-VL |
| GPU | no hace falta | NVIDIA con ≥ 8 GB de VRAM (probado: RTX 3060 12 GB) |
| Sistema | Windows 10/11 (probado en Windows 11); Linux/macOS con `iniciar.sh` | Windows 10/11 de 64 bits (probado en Windows 11 Pro 10.0.26200) |
| Python | 3.10+ (probado con 3.12) | 3.10+ (probado con 3.12) |
| Disco | ~500 MB (entorno de Python) + tus apuntes | ~12 GB: Ollama + modelo 6,2 GB (+3,3 GB el de respaldo) + entorno |
| Otros | Tesseract 5 **con español** para el modo local | controlador NVIDIA reciente (probado 621.14) |
| Red | solo sale hacia la URL del servidor IA (HTTPS) y, si lo permites, a Wikipedia/Wikilibros | Ollama y el servidor IA escuchan solo en 127.0.0.1 (comprobado); se publica únicamente el nombre del túnel o de Tailscale |
| Guía | [instalacion-clientes.md](instalacion-clientes.md) | [instalacion-servidor-ia.md](instalacion-servidor-ia.md) |

Sin la PC encendida, la laptop sigue funcionando en **modo local** (Tesseract) con avisos claros
([recuperacion-conexion.md](recuperacion-conexion.md)).

## 2. Modelos

| Modelo | Uso | Tamaño | Licencia (comprobada) | Estado |
|--------|-----|--------|-----------------------|--------|
| `qwen3-vl:8b-instruct` (Q4_K_M, 8,2 B parámetros + proyector de visión de 576 M) | principal | 6,2 GB en disco · 6,6 GB cargado con contexto 8192 | **Apache 2.0**: `ollama show qwen3-vl:8b-instruct --license` (14/11/2026) | por defecto |
| `qwen3-vl:4b-instruct` | respaldo automático si falta VRAM (`SIN_MEMORIA`) | 3,3 GB | Apache 2.0 (misma familia) | opcional (`-ConRespaldo`) |
| `qwen3-vl:8b` (variante *thinking*) | ninguno: ignora `think:false` y razona antes de responder; no se usa | 6,2 GB | Apache 2.0 | instalada en la PC de pruebas; se puede borrar con `ollama rm qwen3-vl:8b` |
| Tesseract 5 + `spa`/`eng` | OCR local de la laptop | ~30 MB | Apache 2.0 | respaldo sin GPU |
| PaddleOCR-VL 1.6 | — | — | — | **no integrado** (no se verificó en Windows/RTX 3060) |

Los pesos **no se suben a GitHub**: Ollama los descarga en la PC (`iniciar.bat -Modo instalar-ia`,
pide confirmación porque son ~6 GB). Versión de Ollama probada: 0.40.16. Reinstalar o cambiar de
modelo: `IA_MODELO` / `IA_MODELO_RESPALDO` en `ia_servidor\.env` y `ollama pull`; volver atrás es
poner el nombre anterior (los modelos quedan en disco hasta `ollama rm`).

## 3. Consumo medido (RTX 3060 12 GB, Ryzen 7 5700X, 24 GB de RAM)

| Medida | Valor | Cómo / cuándo |
|--------|-------|---------------|
| Modelo cargado | 6,6 GB, «100 % GPU», contexto 8192 | `ollama ps`, 14/11/2026 |
| VRAM total ocupada con el modelo cargado | 9 953 MiB de 12 288 | `nvidia-smi`, 14/11/2026 (incluye ~2,9 GB del escritorio y programas abiertos) |
| Pico de VRAM durante el análisis | 9 971 MB (corpus sintético) · 10,8 GB (foto real, 8B) · 8,2 GB (foto real, 4B) | `validar.ps1 -Gpu` (14/11) · [evaluacion-multimodal.md](evaluacion-multimodal.md) |
| RAM del proceso del modelo (`llama-server`) | 3,3 GB en uso, 11,5 GB comprometidos | Administrador de tareas / `Get-Process`, 14/11/2026 |
| Tiempo por imagen (corpus sintético, 11 casos) | 2,3–7,0 s (el primero incluye calentar) · CER 0 en los 11 | `validar.ps1 -Gpu`, 14/11/2026 |
| Foto real del pizarrón, de extremo a extremo | 24 s con el modelo cargado · 70 s en frío (17 regiones) | [generacion-pdf.md §7](generacion-pdf.md) |
| Carga del modelo | 9–14 s | [evaluacion-multimodal.md](evaluacion-multimodal.md) |

Los resultados de calidad con fotos reales salen de **una sola foto** y no son generalizables
([evaluacion-multimodal.md](evaluacion-multimodal.md)).

## 4. Límites de la RTX 3060

- Con un juego u otro programa usando la GPU, el 8B puede no caber: el servidor responde
  `SIN_MEMORIA` y reintenta con el 4B; si tampoco cabe, la laptop ofrece el modo local.
- Un trabajo a la vez en la GPU (`IA_MAX_INFERENCIAS` = 1); los demás esperan en cola (`IA_MAX_COLA` = 10) y la
  laptop muestra la posición.
- El modelo se descarga de la VRAM 10 min después del último uso (`IA_KEEP_ALIVE`): la primera página
  tras una pausa tarda más.
