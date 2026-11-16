# Estados y errores del servidor IA en la interfaz (FRONT-25)

## Indicador de estado (`#estadoIA[data-estado]`)

| `data-estado` | Texto visible | Cuándo |
|---------------|---------------|--------|
| `cargando` | Comprobando… | Durante una comprobación |
| `local` | Sin servidor IA: modo local | Sin URL o «Continuar sin IA» |
| `sin_vincular` | Servidor configurado, este equipo aún no está vinculado | Hay URL, no hay credencial para ella |
| `vinculado` | Vinculado (pulsa «Comprobar ahora»…) | Hay credencial; aún no se comprobó la conexión |
| `conectado` | Conectado y listo | Diagnóstico completo en verde |
| `no_listo` | Conectado, pero el modelo o la GPU no están listos | Falla solo «Modelo y GPU» |
| `sin_conexion` | Sin conexión con el servidor IA: se usa el modo local | DNS, TLS, red, túnel o PC apagada |
| `no_autorizado` | El servidor no reconoce este equipo: vuelve a vincularlo | 401/403 o credencial ausente |
| `solo_local` | Solo se puede consultar en el equipo donde corre ApuntIA | Uso desde otro dispositivo de la red |

## Etapas del análisis (editor)

| Etapa | Texto |
|-------|-------|
| `ia_enviando` | Enviando la foto al servidor IA |
| `ia_en_cola` | En cola en el servidor IA |
| `ia_procesando` | El servidor IA está leyendo la foto… N % (por regiones) |

## Mensajes (catálogo `front/js/mensajes.js`)

Todos los códigos tienen texto en español y, cuando aplica, botón de acción. La foto original
siempre se conserva.

| Código | Tipo | Acción en pantalla |
|--------|------|--------------------|
| `AI_NO_DISPONIBLE` | aviso | Reintentar · Analizar en modo local |
| `AI_NO_AUTORIZADA` | error | Vincular desde «Servidor IA» |
| `AI_MODELO_AUSENTE` | error | Avisar al administrador |
| `AI_MEMORIA_INSUFICIENTE` | aviso | Reintentar |
| `AI_TIEMPO_AGOTADO` | aviso | Reintentar (recoge el resultado sin repetir) |
| `AI_RESPUESTA_INVALIDA` | error | Reintentar · Analizar en modo local |
| `AI_COLA_LLENA` | aviso | Reintentar |
| `AI_CONTRATO_INCOMPATIBLE` | error | Actualizar ambos equipos |
| `AI_URL_INVALIDA` | error (en el campo) | Corregir la dirección |
| `SOLO_EQUIPO_LOCAL` | error | Usar el equipo donde corre ApuntIA |
| `AI_VINCULACION` | aviso | Pedir otro código |
| `APUNTE_CON_EDICIONES` | aviso | Diálogo: «Analizar de nuevo» crea una versión nueva; las correcciones quedan en el historial |

Ayuda para cada código (causa y solución manual): [recuperacion-conexion.md](../../fullstack/docs/recuperacion-conexion.md)
y [trabajos-remotos.md](../../fullstack/docs/trabajos-remotos.md#3-códigos-públicos-y-recuperación).

## Evidencias

Capturas de una sesión REAL en la PC del servidor (vinculación aprobada en la consola y
diagnóstico completo): `fullstack/docs/evidencias/front-25-*.png` (ver §5 de
[CONEXION_IA_UI.md](CONEXION_IA_UI.md#pruebas)).
