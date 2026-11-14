# Conexión remota segura con el servidor IA (FULL-31)

Cómo la laptop del profesor, en **otra red**, usa la GPU de la PC de casa sin abrir puertos,
sin exponer Ollama y sin que una copia pública del repositorio dé acceso a la GPU.
Seguridad en detalle: [seguridad-servidor-ia.md](seguridad-servidor-ia.md). Qué hacer cuando
falla: [recuperacion-conexion.md](recuperacion-conexion.md).

> Estado (14/11/2026). **Probado en la PC destino** (Windows 11, RTX 3060, `qwen3-vl:8b-instruct`),
> con la «laptop» como un segundo proceso en el mismo equipo y conectando por `http://127.0.0.1:8100`:
> diagnóstico sin vincular (falla en «credencial», como debe), vinculación aprobada en la
> consola del servidor (2,8 s tras aprobar), credencial cifrada con DPAPI, retomar una
> solicitud ya aprobada, diagnóstico completo (5/5), análisis real de fórmulas, revocación
> (`AI_REVOCADO`) y cambio de URL sin enviar la credencial (`AI_NO_VINCULADO`).
> Pruebas automáticas: 29 del servidor (vinculación) y 41 del cliente.
> **Pendiente**: la prueba desde OTRA red real a través de Tailscale o Cloudflare (requiere crear
> la cuenta o el dominio, una decisión del dueño de la PC) y la interfaz web (FRONT-25).

## 1. Piezas

```
LAPTOP (otra red)                                   PC DE CASA
navegador ──▶ backend ApuntIA ──HTTPS──▶ túnel ──▶ ia_servidor 127.0.0.1:8100 ──▶ Ollama 127.0.0.1:11434
              (el token vive aquí,           (Tailscale Serve o
               cifrado con DPAPI)             Cloudflare Tunnel)
```

- El navegador **nunca** recibe el token: habla con el backend de su propio equipo, y es el
  backend quien llama al servidor IA (`app/services/ia_remota.py`).
- `ia_servidor` solo escucha en 127.0.0.1 (o en la IP 100.x de Tailscale). El túnel se conecta
  a 127.0.0.1 desde la propia PC: el router de casa no se toca y el puerto 11434 nunca sale del equipo.

## 2. Vinculación (una vez por laptop)

| Paso | Quién | Dónde | Cómo |
|------|-------|-------|------|
| 1 | Profesor | Laptop | `iniciar.bat -Modo configurar` → URL del servidor → «¿Vincular ahora?» → aparece un código como `JX9T-CUGJ` |
| 2 | Profesor | Teléfono o mensaje | Dicta el código al administrador |
| 3 | Administrador | PC de casa | `iniciar.bat -Modo dispositivos` → opción 1 → escribe el código → aprobar |
| 4 | — | Laptop | Recibe la credencial (una sola vez), la cifra y queda vinculada |

- El código caduca a los 10 min. Si se cierra la ventana, al volver a ejecutar el paso 1 se
  **retoma** la misma solicitud en vez de pedir otro código.
- Sin aprobación no hay credencial: clonar el repositorio o conocer la URL no da acceso a la GPU.
- Después, cada arranque es automático: ApuntIA comprueba el servidor y usa la credencial guardada.

Equivalentes sin menú: `cd back\motori_magenes` y `python -m herramientas.vincular_ia`
(`--url URL`, `--diagnostico`, `--probar foto.png --tarea formula`, `--desvincular`), y en la PC:
`python -m ia_servidor.admin pendientes|aprobar CÓDIGO|rechazar CÓDIGO|dispositivos|revocar ID`.

## 3. API del backend (para la interfaz, FRONT-25)

| Método y ruta | Quién | Respuesta |
|---------------|-------|-----------|
| `GET /api/v2/ia/estado` | Cualquier usuario con sesión | `modo` (`local`/`remoto`), `url`, `vinculado`, `requiere_vinculacion`, `vinculacion_en_curso`, `proteccion_credencial`, `circuito_abierto`. Nunca el token |
| `PUT /api/v2/ia/configuracion` `{url}` | Solo desde el propio equipo, con sesión y CSRF | Cambia la URL (null = la de `APUNTIA_IA_URL`) |
| `POST /api/v2/ia/vinculacion` | Ídem | `{codigo, expira_en_s, instrucciones}` |
| `GET /api/v2/ia/vinculacion` | Ídem | `{estado: pendiente\|vinculado\|rechazada\|expirada\|anulada}` |
| `DELETE /api/v2/ia/vinculacion` | Ídem | Borra la credencial local (la revocación en el servidor la hace su administrador) |
| `GET /api/v2/ia/diagnostico` | Ídem | Pasos `configuracion`, `dns`, `salud_tls_y_version`, `credencial`, `modelo_y_gpu`, cada uno con `ok`, `codigo` y `solucion` |

«Solo desde el propio equipo» = petición desde 127.0.0.1: un alumno conectado por la red del
aula (`iniciar.bat -Red`) no puede cambiar el servidor ni vincular (403 `SOLO_EQUIPO_LOCAL`).

## 4. Elegir el canal entre redes

| Opción | Necesita | Ventajas | Limitaciones | Recomendación |
|--------|----------|----------|--------------|---------------|
| **Tailscale Serve** | Cuenta gratuita de Tailscale en ambos equipos | HTTPS con certificado válido (`https://<pc>.<tailnet>.ts.net`), privado a la tailnet, sin dominio | La laptop debe tener Tailscale abierto; los nombres de equipo quedan en un registro público de certificados | **Primera opción** para 2 equipos |
| **Cloudflare Tunnel con nombre** | Dominio con DNS en Cloudflare | URL estable y pública; se puede añadir Cloudflare Access | Hace falta el dominio; servicio de Windows requiere consola de administrador | Si el proyecto tiene dominio |
| Cloudflare Quick Tunnel | Nada | Para una prueba en minutos | «Solo para pruebas», sin garantía de disponibilidad, la URL cambia cada vez, «cualquiera con la URL accede» (aquí: solo a `/salud` y a pedir vinculación) | Solo para probar |
| Abrir un puerto en el router | — | — | Expone la PC a Internet | **No usar** |

### 4.1 Tailscale Serve (recomendado; no probado aún entre redes)

Fuentes: <https://tailscale.com/kb/1312/serve>, <https://tailscale.com/docs/how-to/set-up-https-certificates>.

1. Instalar Tailscale en la PC y en la laptop e iniciar sesión con la MISMA cuenta (o compartir el equipo).
2. En la consola de administración de Tailscale → DNS: activar **MagicDNS** y **HTTPS Certificates**
   (aviso de Tailscale: los nombres de equipo quedan en un registro público; no uses nombres con datos personales).
3. En la PC, con el servidor IA en marcha (`iniciar.bat -Modo servidor-ia`):
   `tailscale serve --bg 8100` (sirve `http://127.0.0.1:8100` por HTTPS a la tailnet y persiste tras
   reiniciar; se apaga con el mismo comando y `off`). Muestra la URL `https://<pc>.<tailnet>.ts.net`.
4. En la laptop: `iniciar.bat -Modo configurar` con esa URL y vincular (§2).

### 4.2 Cloudflare Tunnel con nombre (si hay dominio; no probado)

Fuentes: <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/local-management/create-local-tunnel/>
y la página de Windows como servicio del mismo sitio.

```bat
cloudflared tunnel login
cloudflared tunnel create apuntia-ia
cloudflared tunnel route dns apuntia-ia ia.<tu-dominio>
cloudflared tunnel run apuntia-ia
```

`%USERPROFILE%\.cloudflared\config.yml`:

```yaml
tunnel: <UUID-del-túnel>
credentials-file: C:\Users\<usuario>\.cloudflared\<UUID-del-túnel>.json
ingress:
  - hostname: ia.<tu-dominio>
    service: http://127.0.0.1:8100
  - service: http_status:404
```

Para que arranque con Windows: `cloudflared.exe service install` desde una consola de
administrador (la guía oficial copia la configuración al perfil del servicio). Opcional: una
política de Cloudflare Access con *service token* delante; el cliente de ApuntIA todavía no envía
las cabeceras `CF-Access-Client-Id/Secret` (pendiente si se adopta).

### 4.3 Prueba rápida con Quick Tunnel (solo pruebas)

`cloudflared tunnel --url http://localhost:8100` imprime una URL `https://….trycloudflare.com`.
Sirve para comprobar la vinculación desde otra red en minutos; luego se cierra con Ctrl+C.

## 5. Operación en casa

- La PC debe estar encendida y sin suspenderse (Configuración → Energía) con el servidor IA
  y el túnel en marcha. Si se apaga, la laptop sigue funcionando en **modo local** (Tesseract).
- Arranque automático: solo con el permiso del administrador (tarea programada «Al iniciar
  sesión» con `iniciar.bat -Modo servidor-ia`; `tailscale serve --bg` ya persiste).
- Antes de una clase: desde la laptop en OTRA red (por ejemplo, el hotspot del celular),
  `iniciar.bat -Modo diagnostico` debe mostrar «IA remota … responde» y, en
  `python -m herramientas.vincular_ia --diagnostico`, los 5 pasos en OK.
