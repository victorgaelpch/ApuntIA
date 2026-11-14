# Ejecutar ApuntIA completo (frontend + backend) (FULL-04)

> **Hoy lo recomendado es `./iniciar.sh` (o `iniciar.bat`) o Docker:** ver [arranque.md](arranque.md) y [docker.md](docker.md). Esta guía describe el modo manual de la versión 1, con dos servidores, que sigue funcionando para «Mejorar una foto»; las páginas con cuenta necesitan que el backend sirva la interfaz (`/inicio`, `/front/…`).

ApuntIA tiene dos partes que se ejecutan por separado:

| Parte | Qué es | Puerto por defecto |
|-------|--------|--------------------|
| **Backend** | API FastAPI que procesa la imagen (`back/motori_magenes`) | `8000` |
| **Frontend** | Página estática (`index.html` + `front/`) | Cualquiera (o `file://`) |

## 1. Levantar el backend

La instalación completa está en [`back/motori_magenes/README.md`](../../back/motori_magenes/README.md). En resumen, con el entorno virtual activo:

```bash
cd back/motori_magenes
```

```bash
uvicorn main:app --reload
```

Comprueba que responde en http://localhost:8000/salud.

## 2. Abrir el frontend

Hay tres opciones, de la más simple a la más completa:

**a) Doble clic** en `index.html`. La página detecta que se abrió como archivo y usa `http://localhost:8000`.

**b) Servidor local** (recomendado: la cámara en vivo solo funciona en `localhost` o `https`). Desde la raíz del repositorio:

```bash
python -m http.server 5500
```

Abre http://localhost:5500/index.html.

**c) Desde el celular en la misma red Wi-Fi:**

1. Levanta el backend escuchando en la red:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

2. Sirve el frontend también para la red (desde la raíz del repositorio):

```bash
python -m http.server 5500 --bind 0.0.0.0
```

3. Averigua la IP de la computadora (`ipconfig` en Windows, `ip addr` o `ifconfig` en macOS/Linux) y abre en el celular `http://<ip>:5500/index.html`. La página usa automáticamente `http://<ip>:8000` como API.

> Por `http://<ip>` el navegador no permite la cámara en vivo: «Tomar foto» abre la app de cámara del celular, que funciona igual.
> Si el firewall de la computadora pregunta, permite las conexiones de Python.

## 3. Configurar la URL de la API

Sin tocar código, por orden de prioridad:

1. **Parámetro en la URL de la página:** `index.html?api=http://192.168.1.20:8001`
2. **`front/js/config.js`:** `apiUrl: "http://mi-servidor:8000"`
3. **Por defecto:** el mismo host que la página, en el puerto `8000`.

No hay credenciales ni claves en el código: la API no las usa.

## 4. CORS

El frontend y el backend están en orígenes distintos (otro puerto, `file://` o la IP), así que el backend debe permitirlo:

- `CORS_ORIGINS` en `back/motori_magenes/.env`: por defecto `*` (cualquier origen), adecuado en desarrollo. Para restringirlo, indica los orígenes separados por comas, por ejemplo `CORS_ORIGINS=http://localhost:5500,http://192.168.1.20:5500`. Al abrir con doble clic, el origen es `null`.
- El backend **expone** `Content-Disposition` y las cabeceras `X-ApuntIA-*` (`Access-Control-Expose-Headers`). Sin eso, el navegador no deja leerlas y la interfaz no puede mostrar si el pizarrón se enderezó.
- No se envían cookies ni credenciales (`allow_credentials=False`).

## 5. Comprobar que la integración funciona

1. Abre la página, elige `back/bd/img/image.png` o cualquier foto de un pizarrón y pulsa «Procesar imagen».
2. Debe aparecer la imagen procesada con una línea como `✓ Pizarrón detectado y enderezado · 1191×810 px · 138 KB · procesada en 0.2 s`.
3. En la terminal de uvicorn se ve `POST /analisis HTTP/1.1" 200 OK`.

| Si ves… | Revisa |
|---------|--------|
| «No se pudo conectar con el servidor de ApuntIA» | ¿Está uvicorn levantado? ¿La URL de la API (puerto, IP) es la correcta? |
| Error de CORS en la consola del navegador (F12) | `CORS_ORIGINS` incluye el origen de la página; reinicia uvicorn tras cambiar `.env` |
| El resultado aparece, pero sin la línea de «Pizarrón…» | Backend antiguo sin `expose_headers`: actualiza el código |
| Desde el celular no carga nada | Que los dos servidores usen `0.0.0.0`, que estén en la misma red y el firewall |

## 6. Trabajar sin backend

Añade `?mock=ok` (u otro escenario: `lento`, `tipo`, `servidor`, `red`…) a la URL de la página para usar respuestas simuladas. Ver [`front/README.md`](../../front/README.md).
