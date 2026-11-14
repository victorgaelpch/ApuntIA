# Seguridad del servidor IA y de la conexión remota (FULL-31)

Complementa la [auditoría general](seguridad.md) y la guía de [conexión remota](conexion-remota.md).
Referencia: OWASP API Security Top 10 (<https://owasp.org/API-Security/>).

## 1. Qué se protege y de quién

| Activo | Amenaza | Control | Prueba |
|--------|---------|---------|--------|
| GPU de la PC de casa | Cualquiera que clone el repo o conozca la URL la usa | Toda inferencia exige token individual obtenido con aprobación manual del administrador | `test_rutas_protegidas_sin_credencial`, `test_flujo_completo` |
| Token del dispositivo | Robo del registro del servidor | El servidor solo guarda SHA-256 del token; el secreto de sondeo también solo como hash | `test_el_registro_no_guarda_tokens_ni_secretos` |
| Token en la laptop | Lectura del disco por otra cuenta | DPAPI (ámbito usuario de Windows); fuera de Windows, archivo con permisos 0600 | `test_dpapi_cifra_la_credencial` (real en Windows) |
| Token en tránsito | Servidor falso o URL cambiada | Solo HTTPS (o loopback), certificado verificado, el token solo va al origen con el que se vinculó, no se siguen redirecciones | `test_credencial_solo_para_su_origen`, `test_no_sigue_redirecciones_ni_filtra_el_token`, E2E con cambio de URL |
| Token en el navegador | XSS en la interfaz | El navegador nunca lo recibe: las llamadas las hace el backend | `GET /api/v2/ia/estado` no lo incluye (`test_estado_sin_configurar_es_modo_local`) |
| Vinculación | Adivinar o reutilizar códigos | Código de 8 caracteres de un alfabeto de 32 (≈1,1·10¹²), 10 min de vigencia, máx. 5 pendientes y 20/hora, 10 sondeos fallidos anulan la solicitud, token entregado una sola vez | `test_limite_de_pendientes`, `test_secreto_incorrecto_y_anulacion`, `test_caduca` |
| Administración | Aprobar o revocar desde la red | No hay rutas HTTP de administración (por el túnel todo llega desde 127.0.0.1): solo consola en la PC | Diseño; `test_consola_de_administracion` |
| Configuración de la laptop | Un alumno por la red del aula cambia el servidor | Rutas `/api/v2/ia/*` de escritura solo desde 127.0.0.1, con sesión y CSRF | `test_acciones_solo_desde_el_propio_equipo`, `test_configurar_exige_csrf` |
| Ollama | Acceso directo al modelo | Solo 127.0.0.1:11434; el servicio se niega a usar otra dirección | `test_configuracion_insegura_no_arranca` |
| Servicio IA | Escucha en toda la red | Solo 127.0.0.1 o la IP 100.x de Tailscale; nunca 0.0.0.0 ni la LAN | `test_hosts_permitidos` |
| Información del equipo | Reconocimiento (GPU, versiones) | `/listo` sin credencial solo dice `listo: true/false`; sin `/docs` ni `/openapi.json` | `test_listo_sin_credencial_no_revela_el_equipo` |
| Disponibilidad | Abuso de un dispositivo vinculado | 30 análisis/min por dispositivo (429 + Retry-After), una inferencia a la vez | `test_limite_por_dispositivo`, `test_cola_llena_devuelve_429_con_retry_after` |
| SSRF desde la laptop | La URL manual apunta a la red interna | Solo `https://<nombre>` o loopback; sin IP pública en HTTPS, sin usuario, ruta ni parámetros; sin redirecciones | `test_validar_url` |

## 2. Registros sin secretos

- Servidor: método, ruta, estado, tiempo, tamaño, modelo y nº de caracteres. Nunca la cabecera
  `Authorization`, el código de vinculación, el texto reconocido ni la imagen.
- Cliente: códigos `AI_*` y si se reintenta; nunca el token ni el secreto.

## 3. Rotación y revocación

| Situación | Qué hacer |
|-----------|-----------|
| Laptop perdida o robada | En la PC: `iniciar.bat -Modo dispositivos` → revocar. El token deja de valer al instante (403) |
| Revincular (p. ej., otra cuenta de Windows) | Volver a vincular: el token anterior del mismo dispositivo se invalida |
| Sospecha de que se filtró el registro del servidor | Solo contiene hashes; aun así, revocar todos y revincular |
| Token de administrador local (`ia_servidor/.datos/admin.token`) | Solo para herramientas de la propia PC; para rotarlo, borrar el archivo y reiniciar el servidor |

## 4. Riesgos aceptados y pendientes

- El administrador debe comprobar que el código que aprueba es el que le dictan: aprobar un
  código ajeno da acceso a la GPU (la consola lo advierte).
- Quick Tunnel deja `/salud` y la petición de vinculación accesibles a quien tenga la URL; los
  límites de solicitudes acotan el abuso, pero solo debe usarse para pruebas.
- El límite por dispositivo vive en memoria: se reinicia con el servicio.
- Cloudflare Access (doble autenticación en el borde) no está integrado en el cliente.
- Pendiente de verificar entre dos redes reales (ver [conexion-remota.md](conexion-remota.md)).
