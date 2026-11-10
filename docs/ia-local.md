# IA local opcional: Ollama y modelo visual (FULL-30)

ApuntIA funciona **sin IA**: el modo básico (OpenCV + Tesseract) no necesita nada de esto. El
modelo visual (VLM) es un apoyo opcional que se instala aparte, en el mismo equipo o en otro de
la red local. Arquitectura y estado: [`arquitectura-ia.md`](arquitectura-ia.md).

> **Estado actual:** ApuntIA ya detecta el modelo, lo diagnostica y lo expone en la API, pero
> **el análisis de apuntes todavía no lo usa** (llega en el siguiente PR). Instalarlo ahora sirve
> para comprobar que el equipo puede ejecutarlo y para medir.

## 1. Requisitos

El software y los modelos son gratuitos; **el cómputo no**: un VLM necesita mucha memoria y es
lento en CPU.

| Modelo (Ollama) | Archivo | Memoria aproximada* | Para qué equipo |
|---|---|---|---|
| `qwen3-vl:2b` | 1,9 GB | ~4 GB | Portátil con 8 GB de RAM |
| `qwen3-vl:4b` (por defecto) | 3,3 GB | ~6 GB | 16 GB de RAM o GPU con 6 GB |
| `qwen3-vl:8b` | 6,1 GB | ~10 GB | 16–32 GB de RAM o GPU con 10 GB |

\* Estimación (archivo + margen), **no medida en este proyecto**. Tamaños según ollama.com.
Licencia de Qwen3-VL: Apache-2.0. Se necesita **Ollama 0.12.7 o superior**.

Sin GPU funciona, pero cada imagen puede tardar de decenas de segundos a minutos. Con GPU NVIDIA
hacen falta sus controladores; Ollama detecta la GPU solo.

## 2. Instalar

1. Instala Ollama desde https://ollama.com/download (Windows, macOS, Linux).
2. Descarga el modelo. **ApuntIA nunca lo descarga por su cuenta**: lo decide quien administra el equipo.
   ```bash
   ollama pull qwen3-vl:4b
   ```
3. Activa la IA en `fullstack/config/.env` (o en las variables de entorno):
   ```bash
   IA_ACTIVADA=true
   OLLAMA_HOST=http://127.0.0.1:11434
   VLM_MODELO=qwen3-vl:4b
   ```
4. Reinicia ApuntIA (`detener` + `iniciar`) y comprueba:
   ```bash
   back/motori_magenes/.venv/bin/python fullstack/scripts/diagnostico_ia.py --probar
   ```
   (En Windows: `back\motori_magenes\.venv\Scripts\python fullstack\scripts\diagnostico_ia.py --probar`.)
   Muestra el equipo, si el modelo está listo, qué perfiles se pueden usar y el resultado de una
   inferencia con una imagen sintética (no usa ningún apunte).

**Docker:** el backend del contenedor llega a un Ollama instalado en el anfitrión con
`OLLAMA_HOST=http://host.docker.internal:11434` (Docker Desktop; en Linux, añadiendo
`extra_hosts: ["host.docker.internal:host-gateway"]`). Un servicio `ollama` dentro de Compose
queda para un PR posterior: **no se ha probado** y no se declara compatible.

## 3. Variables

| Variable | Por defecto | Qué hace |
|---|---|---|
| `IA_ACTIVADA` | `false` | Activa el VLM local |
| `IA_PROVEEDOR` | `ollama` | Único proveedor por ahora |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Servidor de Ollama. Solo se acepta en este equipo o en la red privada |
| `VLM_MODELO` | `qwen3-vl:4b` | Modelo con capacidad «vision», ya instalado |
| `IA_TIMEOUT_S` | `180` | Tiempo máximo por inferencia |
| `IA_MAX_INFERENCIAS` | `1` | Inferencias a la vez; las demás esperan o devuelven «ocupado» |
| `IA_MAX_LADO_PX` | `1600` | Lado máximo de la imagen enviada (se reduce una copia) |
| `IA_PERMITIR_EXTERNA` | `false` | Solo con `true` se acepta un servidor fuera de la red privada o un modelo `-cloud` |
| `RECONOCIMIENTO_PERFIL` | `automatico` | `rapido`, `equilibrado`, `avanzado` o `automatico` |

Equivalencias con los nombres propuestos en el issue: `APUNTIA_AI_ENABLED` = `IA_ACTIVADA`,
`APUNTIA_OLLAMA_HOST` = `OLLAMA_HOST`, `APUNTIA_VLM_MODEL` = `VLM_MODELO`,
`APUNTIA_RECOGNITION_MODE` = `RECONOCIMIENTO_PERFIL`, `APUNTIA_AI_TIMEOUT_SECONDS` = `IA_TIMEOUT_S`,
`APUNTIA_MAX_CONCURRENT_INFERENCES` = `IA_MAX_INFERENCIAS`, `APUNTIA_ALLOW_EXTERNAL_AI` =
`IA_PERMITIR_EXTERNA`. El backend no usa el prefijo `APUNTIA_` en sus variables.

## 4. Privacidad y seguridad

- **Local por defecto.** El servidor de inferencia debe estar en el propio equipo o en la red
  privada; se rechazan las direcciones públicas y las de metadatos de la nube (169.254.x.x).
- **Sin Ollama Cloud.** Los modelos `*-cloud` (p. ej. `qwen3-vl:235b-cloud`) mandan la imagen a
  servidores ajenos: están bloqueados salvo `IA_PERMITIR_EXTERNA=true`.
- **No expongas Ollama a Internet.** Por defecto escucha solo en `127.0.0.1`; si lo abres a la red
  (`OLLAMA_HOST=0.0.0.0` en el servidor de Ollama), hazlo solo en una red de confianza: Ollama no
  tiene autenticación.
- **Sin descargas.** ApuntIA solo llama a `/api/version`, `/api/tags`, `/api/show` y `/api/chat`.
- **El contenido de la foto es dato.** Si un apunte contiene «ignora tus instrucciones…», el modelo
  debe transcribirlo, no obedecerlo; la respuesta se valida contra un esquema JSON y nunca se ejecuta.
- **Registros sin contenido:** solo tiempos, tamaños y modelo, nunca el texto reconocido.

## 5. Problemas frecuentes

| Mensaje del diagnóstico | Solución |
|---|---|
| `desactivado (IA_ACTIVADA=false)` | Es lo normal sin IA. Para activarla: `IA_ACTIVADA=true` |
| `Ollama no responde en OLLAMA_HOST` | Abre Ollama (o `ollama serve`) y revisa la URL y el puerto |
| `el modelo «…» no está instalado` | `ollama pull qwen3-vl:4b` |
| `Ollama … es antiguo` | Actualiza Ollama a 0.12.7 o superior |
| `no admite imágenes (capacidad «vision»)` | Elige un modelo con visión, p. ej. `qwen3-vl:4b` |
| `necesita ~6 GB … y hay 3 GB libres` | Usa `qwen3-vl:2b` o cierra programas |
| `no es una dirección local ni privada` | Usa Ollama en tu equipo o tu red, o (bajo tu responsabilidad) `IA_PERMITIR_EXTERNA=true` |
| Prueba con `TIEMPO_AGOTADO` | El equipo es lento: sube `IA_TIMEOUT_S` o usa un modelo más pequeño |
| Prueba con `SIN_MEMORIA` | El modelo no cabe: usa uno más pequeño |

## 6. Desactivar o desinstalar

- Desactivar: `IA_ACTIVADA=false` y reinicia. ApuntIA sigue igual que antes.
- Borrar el modelo: `ollama rm qwen3-vl:4b`. Desinstalar Ollama: desde el sistema operativo
  (Windows: Configuración → Aplicaciones; Linux: según https://github.com/ollama/ollama/blob/main/docs/linux.md).
