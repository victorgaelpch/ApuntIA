# Exposición paso a paso de ApuntIA 3.0 (FULL-32)

Guía para enseñar el sistema completo (laptop + servidor IA en casa) en unos 10 minutos, con plan B
si la red de la universidad falla. La demostración clásica sin servidor IA sigue en
[entrega.md §5](entrega.md#5-guía-de-demostración--10-minutos).

> Estado: los pasos de la PC (servidor IA, vinculación, análisis real, PDF) se ejecutaron en la PC
> de pruebas el 14/11/2026. **La conexión desde otra red (laptop fuera de casa por el túnel) aún no
> se ha probado**: necesita la cuenta de Cloudflare o Tailscale del dueño del proyecto
> ([pruebas-y-metricas.md §3](pruebas-y-metricas.md)).

## 1. La noche anterior, en casa (lista de puesta en marcha)

| ✔ | Qué | Cómo comprobarlo |
|---|-----|------------------|
| ☐ | PC encendida y **sin suspensión** (Energía → «Nunca» con corriente) y sin actualizaciones pendientes de reinicio | Configuración de Windows |
| ☐ | Corriente e Internet estables (si se va la luz, la PC no vuelve sola salvo que la BIOS lo permita) | — |
| ☐ | Espacio libre ≥ 2 GB (`IA_MIN_DISCO_MB`) | `iniciar.bat -Modo diagnostico` |
| ☐ | Ollama en marcha y el modelo descargado | `ollama list` muestra `qwen3-vl:8b-instruct` |
| ☐ | Servidor IA listo | `iniciar.bat -Modo servidor-ia` y `http://127.0.0.1:8100/listo` → 200 |
| ☐ | Ollama y el servidor IA solo en 127.0.0.1; firewall sin reglas nuevas | [seguridad-servidor-ia.md](seguridad-servidor-ia.md) |
| ☐ | Túnel activo (Cloudflare Tunnel o Tailscale Serve) | desde el móvil con datos: `https://<tu-nombre>/salud` → `{"estado":"ok"}` |
| ☐ | La laptop está vinculada | en la laptop, «Servidor IA» → «Conectado» (o `validar.ps1 -SoloRemoto -Remoto https://<tu-nombre>`) |
| ☐ | GPU libre: cerrar juegos y programas que usen la GPU | `nvidia-smi` |
| ☐ | Registros a mano por si algo falla | `fullstack\.estado\ia-servidor.err.log` y `ollama.log` (sin contenido de apuntes ni tokens) |

## 2. Antes de entrar a clase (laptop)

1. `iniciar.bat` → «Iniciar ApuntIA». Abrir «Servidor IA»: debe decir **Conectado** con el nombre del
   equipo y el modelo. Si no: «Diagnosticar» (5 pasos con la causa).
2. Tener una cuenta de demostración y 2–3 fotos **propias o sintéticas** (nunca de alumnos sin permiso).
3. Dejar abierto un apunte ya analizado y su PDF (para el plan B).

## 3. Recorrido (≈ 10 minutos)

| Min | Qué se enseña | Qué decir |
|-----|---------------|-----------|
| 0–1 | Arquitectura: laptop sin GPU ↔ HTTPS ↔ PC con RTX 3060 ([arquitectura.md](arquitectura.md#apuntia-30-dos-equipos)) | «La GPU está en casa; aquí solo viaja la foto y vuelve el texto.» |
| 1–2 | Pantalla «Servidor IA»: estado, modelo, «Diagnosticar» | «El token está cifrado en esta laptop y nunca llega al navegador.» |
| 2–5 | «Nuevo apunte» con reconocimiento «Servidor IA»: la barra dice «En cola en el servidor IA» y «El servidor IA está leyendo la foto» | tiempos reales: ~25 s una foto de pizarrón con el modelo cargado, ~70 s en frío |
| 5–7 | Editor: «Propuesta de IA · sin revisar» junto a su recorte, dudas del modelo, corregir una fórmula, «Marcar como revisado» | «Es una propuesta: nunca se presenta como transcripción confirmada.» |
| 7–8 | Información complementaria (opcional): permiso, palabras clave, fuente citada, aceptar | «Solo se envían las palabras que marco; nunca la foto.» |
| 8–10 | PDF: portada con avisos, etiquetas de IA y recortes, fórmulas, fuentes | «Si algo no se pudo leer, va como imagen; no se inventa.» |

Mostrar la GPU (opcional): en la PC, `nvidia-smi` o el Administrador de tareas → GPU → «Memoria de GPU
dedicada»; `ollama ps` muestra el modelo y «100 % GPU».

## 4. Plan B

| Si… | Entonces |
|-----|----------|
| La red de la universidad bloquea el túnel o no hay Internet | En «Servidor IA», «Continuar sin IA»: analizar con Tesseract y enseñar el apunte guardado, la edición y el PDF (todo funciona sin red). Decir el límite real: el modo local lee peor manuscrito y fórmulas 2D. |
| La PC de casa no responde (apagada, suspendida, sin luz) | La laptop lo muestra («El servidor IA no está disponible (PC apagada, túnel o Internet caídos)…», `AI_NO_DISPONIBLE`) y el editor ofrece «Analizar en modo local»; la foto se conserva. |
| «La GPU del servidor IA no tiene memoria libre» (`AI_MEMORIA_INSUFICIENTE`) | Alguien está usando la GPU en casa: el servidor ya intentó con el 4B; reintentar en unos minutos o modo local. |
| El análisis tarda | La barra indica la posición en la cola; se puede cancelar sin perder la foto. |
| El navegador muestra un error con «Referencia: …» | Buscarla en el registro ([diagnostico.md](diagnostico.md)). |

## 5. Después (detener, limpiar, volver atrás)

- **Detener**: `detener.bat` (o `iniciar.bat -Modo detener`) en cada equipo para lo que inició ApuntIA; en
  la PC, para liberar la GPU al momento, `ollama stop qwen3-vl:8b-instruct`.
- **Revocar la laptop** si se perdió o se prestó: en la PC, `iniciar.bat -Modo dispositivos`
  ([conexion-remota.md](conexion-remota.md)).
- **Limpiar sin borrar apuntes**: los datos están en `DATA_DIR`; `respaldar` antes de cualquier
  cambio ([respaldo.md](respaldo.md)). No borrar `ia_servidor\.datos` (contiene las vinculaciones).
- **Volver al modo clásico** (sin servidor IA): «Continuar sin IA» en la laptop, o no configurar
  la URL. Ningún apunte depende del servidor IA para abrirse ni para generar su PDF.
