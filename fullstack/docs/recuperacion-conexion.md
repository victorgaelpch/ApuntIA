# Recuperación de la conexión con el servidor IA (FULL-31)

Cuando el servidor IA no está disponible, **ApuntIA sigue funcionando en modo local**
(Tesseract) y no se pierde ningún apunte. Esta tabla relaciona cada código que muestra el
diagnóstico (`iniciar.bat -Modo diagnostico`, `python -m herramientas.vincular_ia --diagnostico`
o `GET /api/v2/ia/diagnostico`) con su causa y su solución manual.

| Código | Qué pasa | ¿Se reintenta solo? | Solución |
|--------|----------|---------------------|----------|
| `AI_NO_CONFIGURADO` | No hay URL | — | `iniciar.bat -Modo configurar` (mientras tanto, modo local) |
| `AI_URL_INVALIDA` | URL con usuario, parámetros, http externo o IP en HTTPS | No | Usar `https://<nombre>` |
| `AI_NO_VINCULADO` | Sin credencial para ESTA URL (nunca vinculado o URL cambiada) | No | Vincular ([conexion-remota.md §2](conexion-remota.md#2-vinculación-una-vez-por-laptop)) |
| `AI_VINCULACION` | Código caducado, rechazado o anulado | No | Pedir un código nuevo |
| `AI_NET_DNS` | No se resuelve el nombre | Sí (2 veces) | Revisar Internet, la URL, que Tailscale esté abierto en la laptop |
| `AI_NET_CONEXION` | PC apagada, dormida, servidor IA o túnel caídos | Sí | Encender la PC; `iniciar.bat -Modo servidor-ia`; revisar el túnel |
| `AI_NET_TIMEOUT` | Sin respuesta a tiempo | Sí | Igual que el anterior; si la red es lenta, reintentar |
| `AI_NET_TLS` | Certificado inválido o caducado | **No**: no se envía nada | Revisar la URL o el túnel. **Nunca** desactivar la verificación |
| `AI_REDIRECCION` | El servidor intentó redirigir | No | Revisar la URL (posible portal cautivo o servidor equivocado) |
| `AI_AUTH` (401) | La credencial ya no vale | No | Vincular de nuevo |
| `AI_REVOCADO` (403) | El administrador revocó el equipo | No | Pedir al administrador una nueva vinculación |
| `AI_LIMITE` (429) | Demasiadas peticiones | Sí, respetando `Retry-After` | Esperar |
| `AI_SERVIDOR` (5xx) | Modelo ausente, GPU sin memoria (p. ej. un juego abierto), tiempo agotado | Según el servidor | Leer el mensaje: cerrar programas que usen la GPU, `iniciar.bat -Modo instalar-ia`… |
| `AI_RESPUESTA` | Respuesta que no es del servidor IA (portal cautivo, proxy) | Sí | Revisar la red o la URL |
| `AI_VERSION` | Versiones de API incompatibles | No | Actualizar ApuntIA en ambos equipos (`git pull`) |
| `AI_CIRCUITO_ABIERTO` | Tras 3 fallos de red seguidos se deja de insistir 30 s | Sí, tras la pausa | Nada: evita bloquear la aplicación; revisar la causa original |

## Comportamiento automático

- Reintentos: hasta 2, con espera de 0,5 s y 1 s (o la de `Retry-After`, máximo 10 s), solo en
  fallos reintentables. 401, 403, TLS y redirecciones nunca se reintentan.
- Tiempos: 10 s para consultas y 240 s para un análisis (`APUNTIA_IA_TIMEOUT_S`,
  `APUNTIA_IA_TIMEOUT_ANALISIS_S`).
- Circuit breaker por servidor: 3 fallos de red seguidos → 30 s sin intentarlo.
- Escribir la MISMA URL otra vez no arregla una caída de Internet o del túnel: el diagnóstico
  dice en qué paso está el problema.

## Pendiente (BACK-37)

La cola durable de trabajos remotos (guardar la foto y reintentar más tarde sin perderla,
cancelar, evitar duplicados) es BACK-37. Hoy el cliente reintenta dentro de una misma petición.
