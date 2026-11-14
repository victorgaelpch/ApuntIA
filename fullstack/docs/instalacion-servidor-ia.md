# Instalar el servidor IA en la PC de casa (FULL-30)

Solo en la PC con GPU NVIDIA que hará el reconocimiento avanzado. La laptop del profesor **no**
necesita nada de esto ([instalacion-clientes.md](instalacion-clientes.md)). Qué hace el servicio:
[servidor-ia.md](servidor-ia.md).

> Estado (13/11/2026), probado en la PC destino (Windows 11 Pro 10.0.26200, RTX 3060 12 GB,
> controlador 621.14, Python 3.12): creación del entorno e instalación de dependencias (37 s la
> primera vez, 1 s la segunda, sin reinstalar), parada en el paso manual de Ollama (código 5),
> arranque del servidor IA sin Ollama (en marcha, «no listo» con la causa), doble arranque sin
> duplicar y `detener.bat`. **Pendiente**: instalar Ollama y descargar `qwen3-vl:8b` en esta PC
> (requiere la confirmación del dueño del equipo) y medir la inferencia real.

## 1. Requisitos

| Requisito | Mínimo | Fuente |
|-----------|--------|--------|
| Windows | 10 22H2 o 11, 64 bits | <https://docs.ollama.com/windows> |
| Controlador NVIDIA | 551.61 o superior | <https://docs.ollama.com/windows> |
| GPU | 12 GB de VRAM para `qwen3-vl:8b-instruct` con margen; con menos de 8 GB usar `qwen3-vl:4b-instruct` | tamaños de <https://ollama.com/library/qwen3-vl> |
| Disco | ~12 GB libres: Ollama ≥ 4 GB + modelo 6,2 GB (+3,3 GB el de respaldo) + entorno de Python | ídem |
| Python | 3.10 o superior | — |
| Ollama | 0.12.7 o superior | «Qwen3-VL models require Ollama 0.12.7» (ollama.com) |
| Administrador | **No hace falta**: Ollama se instala en la carpeta del usuario | <https://docs.ollama.com/windows> |

## 2. Instalación guiada

```bat
iniciar.bat
```

En el menú, opción **2. Instalar o reparar el servidor IA**. Equivale a
`iniciar.bat -Modo instalar-ia`. Hace, en orden, y cada paso se puede repetir sin perder nada:

1. Comprueba Windows de 64 bits, espacio en disco, GPU y versión del controlador.
2. Crea `ia_servidor\.venv` e instala `ia_servidor/requirements.txt` con las versiones de
   `back/motori_magenes/constraints.txt`. Solo reinstala si cambian los requisitos.
3. Crea `ia_servidor\.env` desde `.env.example` si no existe (sin secretos; nunca lo sobrescribe).
4. Busca Ollama. Si falta, **pregunta** si instalarlo con `winget install --id Ollama.Ollama`
   (paquete del editor oficial, descarga de los releases de github.com/ollama). Si dices que no,
   o no hay winget o consola, explica las dos vías oficiales y sale con código **5**.
5. Comprueba que Ollama sea 0.12.7 o superior y lo inicia en `127.0.0.1:11434` si no está abierto.
6. Si falta el modelo, **pregunta** antes de descargarlo e indica el tamaño. `ollama pull` muestra
   el progreso y reanuda si se corta. Si ya está instalado, no lo vuelve a descargar.

Para automatizar sin preguntas: `powershell -ExecutionPolicy Bypass -File fullstack\scripts\ia.ps1
-Accion instalar -AceptarDescarga [-ConRespaldo]` (con `-ConRespaldo` descarga también el 4B).

### Instalación manual (si el script no sirve)

```bat
winget install --id Ollama.Ollama --exact --source winget
ollama pull qwen3-vl:8b-instruct
py -3 -m venv ia_servidor\.venv
ia_servidor\.venv\Scripts\python -m pip install -r ia_servidor\requirements.txt -c back\motori_magenes\constraints.txt
copy ia_servidor\.env.example ia_servidor\.env
```

También puedes bajar el instalador `OllamaSetup.exe` de <https://ollama.com/download/windows>.

## 3. Uso diario

| Acción | Menú | Comando |
|--------|------|---------|
| Iniciar el servidor IA (y Ollama si no está abierto) | 3 | `iniciar.bat -Modo servidor-ia` |
| Ver qué falta | 5 | `iniciar.bat -Modo diagnostico` |
| Detener lo que inició ApuntIA | 6 | `detener.bat` |

- `detener.bat` solo termina procesos cuyo PID registró ApuntIA y cuya línea de órdenes sigue
  siendo la suya (`ia_servidor`, `ollama serve`). Si abriste Ollama desde el menú Inicio, no lo
  cierra.
- El modelo sale de la VRAM 10 minutos después del último uso (`IA_KEEP_ALIVE`), así que la GPU
  queda libre para otras cosas, juegos incluidos. Mientras se analiza una imagen, la GPU está ocupada.
- Iniciar con Windows: **no se configura sin permiso**. Si el administrador lo quiere, puede
  crear una tarea programada «Al iniciar sesión» que ejecute
  `iniciar.bat -Modo servidor-ia` (Programador de tareas → Crear tarea básica). Revisa
  también que la PC no se suspenda (Configuración → Sistema → Energía).

### Qué variante del modelo

Usa las variantes **`-instruct`**. En Ollama, `qwen3-vl:8b` (sin sufijo) es la variante
«thinking»: razona antes de responder, ignora `think: false` y en esta PC tardó minutos o no
terminó con fórmulas ([servidor-ia.md §8](servidor-ia.md#8-medición-real-en-la-pc-destino-13112026)).
Si ya la descargaste y no la usas, se puede borrar con `ollama rm qwen3-vl:8b` (libera 6,2 GB).

## 4. Errores frecuentes y solución manual

| Síntoma / código | Causa | Solución |
|------------------|-------|----------|
| Salida 5, «Falta Ollama» | No instalado | `winget install --id Ollama.Ollama --exact --source winget` y repetir |
| Salida 5, «Modelo sin descargar» | Se respondió «no» o no hay consola | `ollama pull qwen3-vl:8b-instruct` |
| Salida 2 en pip | Sin Internet, proxy o disco | Revisar la conexión; repetir (se reanuda) |
| Salida 2 en `ollama pull` | Corte de red o disco lleno | Repetir: continúa la descarga; liberar espacio |
| «Ollama … es antiguo» | Versión < 0.12.7 | `winget upgrade --id Ollama.Ollama` |
| «controlador anterior a 551.61» | Driver NVIDIA viejo | Actualizar desde nvidia.com (GeForce Experience / NVIDIA App) |
| Salida 3 | Puerto 8100 ocupado | Cambiar `IA_PUERTO` en `ia_servidor\.env` |
| «en marcha pero NO listo» | Ollama apagado, modelo ausente, disco | La causa aparece debajo; corregirla y ver `/listo` |
| `SIN_MEMORIA` al analizar | La VRAM está ocupada (p. ej. un juego abierto) | Cerrar el programa que use la GPU, o usar el 4B |
| PowerShell bloquea el script | Directiva de ejecución | Los `.bat` ya usan `-ExecutionPolicy Bypass` solo para ese proceso; **no** desactives la seguridad del sistema |
| `ia_servidor\.env` dañado | Edición manual | Borrarlo: se regenera desde `.env.example` |

## 5. Docker

El servidor IA **no** usa Docker: la GPU en Docker Desktop para Windows requiere WSL2 y
configuración extra que no se ha verificado en la RTX 3060. El `compose.yaml` existente sigue
sirviendo solo para ApuntIA (cliente) y no cambia.
