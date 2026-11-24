# ApuntIA alojado en una laptop (sin IP pública)

Esta configuración permite mantener **una sola instalación** de ApuntIA en la laptop: frontend, API FastAPI, OpenCV, Tesseract, cuentas, SQLite, PDFs e historial. El servicio IA con Ollama **permanece independiente** y se vincula **una sola vez** desde la consola de la laptop. Todas las personas con acceso a la web usan la misma instalación y, si está habilitado, la conexión IA ya autorizada.

## 0. Seguridad previa

- Usa una laptop dedicada con Docker moderno, SSD y respaldos; mantén el sistema actualizado y evita que entre en suspensión.
- **No abras puertos en el router**. El contenedor publica `127.0.0.1:8000` solamente. Instala `cloudflared` en la laptop anfitriona, no dentro del contenedor.
- Crea un **túnel administrado de Cloudflare** para un dominio estable; los Quick Tunnels son temporales y solo sirven para pruebas.
- La aplicación contiene registro de usuarios, almacenamiento de documentos y un endpoint público de mejora de imágenes; antes de invitar usuarios desconocidos, define límites de tráfico y almacenamiento, política de privacidad y recuperación de cuentas por correo (el código actual usa un buzón local, **no envía emails reales**).
- Protege las credenciales del túnel, el `.env`, las copias de SQLite, fotos y PDF. Nunca los subas a GitHub.

## 1. Primera instalación

Desde la raíz de ApuntIA, instala Docker Desktop (Windows) o Docker Engine + Compose v2 (Linux) y ejecuta:

```bash
cp fullstack/config/.env.example fullstack/config/.env
```

En Windows copia `fullstack/config/.env.example` a `fullstack/config/.env` con el explorador.

Abre `fullstack/config/.env` y configura **obligatoriamente** la URL pública final (sin ruta ni barra final), por ejemplo:

```dotenv
URL_PUBLICA=https://apuntia.tudominio.com
APUNTIA_PUERTO=8000
```

La plantilla existente del repositorio contiene otras variables de OCR y límites: mantenlas como prefieras. **No uses** `http://localhost:8000` como `URL_PUBLICA` de producción. La composición de servidor fija `COOKIE_SEGURA=1` independientemente del valor de la plantilla, para que las cookies solo se envíen por HTTPS.

Arranca:

```bash
docker compose --env-file fullstack/config/.env -f fullstack/compose.servidor.yaml up --build -d
```

Comprueba el motor:

```bash
docker compose --env-file fullstack/config/.env -f fullstack/compose.servidor.yaml ps
curl http://127.0.0.1:8000/salud
```

`/` redirige a `/inicio` y el resto de la interfaz usa `/front/…`. **En `http://localhost:8000` es normal que los inicios de sesión no persistan** porque la cookie `Secure` exige HTTPS. Prueba el registro, acceso, subida de fotos y PDF desde el dominio HTTPS real.

## 2. Publicación con Cloudflare Tunnel

1. Agrega tu dominio a Cloudflare y crea un túnel administrado desde el panel de Cloudflare Zero Trust > Networks > Tunnels (la navegación exacta puede cambiar).
2. Instala **cloudflared en el sistema anfitrión** de la laptop, como servicio, siguiendo el comando de instalación que entrega Cloudflare. No coloques ni publiques su token en este repositorio.
3. Configura un **public hostname** como `apuntia.tudominio.com`, tipo **HTTP**, destino **`localhost:8000`**. Cloudflare publica HTTPS y se conecta a tu puerto de loopback.
4. Asegúrate de que el `URL_PUBLICA` del archivo `.env` sea exactamente `https://apuntia.tudominio.com`. Si lo cambias, vuelve a crear el contenedor (`up -d --force-recreate`).
5. Desde el celular, usando **datos móviles** (fuera de la red de la laptop), abre `https://apuntia.tudominio.com/inicio`, registra una cuenta de prueba, sube una foto y genera un PDF.

**Solo para una prueba temporal**, antes de disponer de un dominio, en la laptop:

```bash
cloudflared tunnel --url http://localhost:8000
```

Copia la URL `https://....trycloudflare.com` a `URL_PUBLICA`, recrea el contenedor y prueba la web con esa URL. Al reiniciar el Quick Tunnel la dirección puede cambiar y tendrás que volver a actualizar `URL_PUBLICA`. El uso continuo requiere un túnel administrado.

## 3. Conectar el servidor IA existente (Ollama)

**No se modifica `ia_servidor/` ni se instala Ollama en la laptop.** La PC con GPU sigue exponiendo **únicamente el servicio IA**, mediante su túnel HTTPS o el acceso remoto ya configurado. Debe seguir encendida si quieres usar el modo IA. Ollama permanece escuchando en `127.0.0.1:11434` en esa PC.

El modo IA del proyecto siempre ha tenido una configuración **por instalación, no por usuario**. En la web pública se **bloquean las rutas de configuración y vinculación por HTTP**, incluso para localhost, porque un proxy/túnel puede ocultar o falsificar el origen de la conexión. La configuración de la laptop se hace con la **herramienta CLI existente** incluida ahora en la imagen Docker:

```bash
docker compose --env-file fullstack/config/.env -f fullstack/compose.servidor.yaml exec backend python -m herramientas.vincular_ia --url https://tu-servidor-ia.ejemplo.com
```

La herramienta mostrará un código. En la **PC que tiene Ollama**, apruébalo con el sistema que ya usas:

```bat
iniciar.bat -Modo dispositivos
```

Deja la consola de la laptop abierta mientras el administrador aprueba el código. La credencial del equipo se guarda en `/datos/ia_remota.json` dentro del volumen persistente de ApuntIA, **no en el navegador**. Esa vinculación es compartida por los usuarios de esta instalación: protege el acceso al sistema y limita los usos de IA.

Para verificar la conexión (sin volver a vincular):

```bash
docker compose --env-file fullstack/config/.env -f fullstack/compose.servidor.yaml exec backend python -m herramientas.vincular_ia --diagnostico
```

Si cambias de servidor IA, vuelve a ejecutar `--url https://...` y vincula el equipo nuevo. Para desactivar la vinculación de esta instalación:

```bash
docker compose --env-file fullstack/config/.env -f fullstack/compose.servidor.yaml exec backend python -m herramientas.vincular_ia --desvincular
```

**Importante:** la pantalla «Servidor IA» de la web permite ver el estado, pero no cambiarlo ni pedir códigos. Es intencional en una instalación pública centralizada. Los usuarios eligen «Automático», «Servidor IA» o «Local» al crear sus apuntes, según la disponibilidad del servidor, pero **no vinculan servidores distintos por cuenta**. Para permitir servidores particulares haría falta un modelo de credenciales y permisos por usuario.

## 4. Administración de la laptop

```bash
# Ver logs del backend
docker compose --env-file fullstack/config/.env -f fullstack/compose.servidor.yaml logs -f backend

# Actualizar tras revisar la rama y ejecutar pruebas
git pull
docker compose --env-file fullstack/config/.env -f fullstack/compose.servidor.yaml up --build -d

# Parar sin borrar datos
docker compose --env-file fullstack/config/.env -f fullstack/compose.servidor.yaml down
```

**No uses `down -v`**: ese comando borraría el volumen con SQLite, fotos y PDF. La instrucción normal `down` conserva el volumen.

### Respaldos

Detén escrituras antes de un respaldo completo consistente. Guarda fuera de la laptop una copia cifrada y periódica de todo el volumen `apuntia-servidor_datos` (nombre habitual de Docker Compose) que contiene `apuntia.sqlite3`, imágenes, PDFs y `ia_remota.json` con el token. Comprueba periódicamente la restauración. Los scripts de respaldo del proyecto están diseñados para la instalación local y **no debes asumir que apuntan al volumen Docker de este despliegue**.

### Problemas frecuentes

- **Registro/login falla con `ORIGEN_NO_PERMITIDO`:** verifica `URL_PUBLICA` exactamente igual a la URL del navegador (esquema HTTPS y hostname, sin rutas). Reconstruye/recrea el contenedor tras cambiar `.env`.
- **Al entrar por localhost no se guarda la sesión:** correcto con `COOKIE_SEGURA=1`; usa el dominio HTTPS.
- **Modo IA `SOLO_ADMIN_SERVIDOR`:** configuración reservada al CLI por seguridad; usa `docker compose ... exec backend python -m herramientas.vincular_ia`.
- **Servidor IA no disponible:** revisa si la PC con GPU y su túnel siguen activos; el procesamiento OCR local debe continuar funcionando.
- **OCR incorrecto o ausente:** verifica `GET /api/v2/listo`, idioma `spa+eng` y logs de Tesseract.
- **Fotos grandes:** los límites de carga del proxy de Cloudflare pueden ser inferiores a los límites de la API; reduce tamaño/cantidad de fotos por solicitud. Monitorea RAM, CPU y almacenamiento.

## 5. Seguridad y límites pendientes

Esta entrega prepara la publicación en un único servidor doméstico, **no equivale a auditoría de seguridad ni prueba de carga**. Antes de abrir la página al público general revisa la exposición de la API v1 sin cuenta (`/analisis`), el rate limiting de subida, el manejo de la IP cliente detrás del túnel, las políticas de recuperación de contraseñas sin correo saliente, los límites de almacenamiento y el backup. `--no-proxy-headers` evita confiar en cabeceras enviadas por clientes no autenticados, pero detrás del túnel todos los usuarios pueden aparecer con la misma IP de puerta de enlace, por lo que el límite por IP podría afectar a varios usuarios. No elimines esa protección sin diseñar una forma segura de obtener la IP real.
