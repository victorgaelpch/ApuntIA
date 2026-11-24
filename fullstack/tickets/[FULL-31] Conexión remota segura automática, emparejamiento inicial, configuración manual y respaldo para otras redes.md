# [FULL-31] Conexión remota segura automática, emparejamiento inicial, configuración manual y respaldo para otras redes

- Numero de Issue: #95
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/95
- Estado: open
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: fullStack
- Creacion GitHub: 2026-11-13 18:39:19 -0600 (CDMX)
- Cierre GitHub: No registrada / no aplica
- Actualizacion GitHub: 2026-11-13 18:39:19 -0600 (CDMX)
- Creacion UTC: 2026-11-14T00:39:19Z
- Cierre UTC: No aplica

- Fecha de captura: 2026-11-24 12:09:45 -0600 (CDMX)
- [Captura original](%5BFULL-31%5D%20Conexi%C3%B3n%20remota%20segura%20autom%C3%A1tica%2C%20emparejamiento%20inicial%2C%20configuraci%C3%B3n%20manual%20y%20respaldo%20para%20otras%20redes-original.png)
- [Captura con metadatos](%5BFULL-31%5D%20Conexi%C3%B3n%20remota%20segura%20autom%C3%A1tica%2C%20emparejamiento%20inicial%2C%20configuraci%C3%B3n%20manual%20y%20respaldo%20para%20otras%20redes.png)

## Descripcion original

## Objetivo — FULL-31
Hacer que ApuntIA en la laptop del profesor encuentre el servidor de casa automáticamente en ejecuciones posteriores a una vinculación segura inicial, manteniendo configuración manual para cambiar URL o reautorizar. Conectar ambas redes sin abrir Ollama/11434 y sin publicar ningún secreto en GitHub.

## Contexto real del repositorio
Aplicación local y servidor IA separados físicamente. La URL del servidor puede ser pública, pero una URL NO autoriza el uso de la GPU. «Automático para toda instalación recién clonada sin autorización» sería inseguro: implementar vinculación inicial de un solo uso o aprobación explícita.

## Dependencias
BACK-35 y FULL-30 al menos con endpoints de salud y esquema de cliente.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-11-23 · 18:00–21:00 (America/Mexico_City): Contrato de conexión y riesgos de seguridad; configuración de túnel.
- [ ] 2026-11-25 · 18:00–21:00 (America/Mexico_City): Emparejamiento y almacenamiento local de credenciales.
- [ ] 2026-11-28 · 10:00–13:00 (America/Mexico_City): Pruebas desde otra red, diagnóstico, recuperación manual.

## Tareas técnicas detalladas
#### Infraestructura de red
- [ ] Documentar y configurar Cloudflare Tunnel con hostname estable sobre dominio administrado por el proyecto; usar HTTPS y comprobación de certificado. Nunca publicar puerto 11434 de Ollama ni abrir router a ciegas.
- [ ] En el servidor IA, aplicar control de acceso propio a las rutas de inferencia, límites de tamaño/frecuencia, protección de solicitudes y registro mínimo; cuando corresponda, complementar con Cloudflare Access por cliente/servicio.
- [ ] Diseñar conexión secundaria manual: URL alternativa HTTPS autorizada, o VPN Tailscale como contingencia para dispositivos enrolados; aclarar que escribir la MISMA URL no arregla una caída de Internet/túnel.
#### Autorización y uso
- [ ] Establecer URL de descubrimiento predeterminada en configuración PÚBLICA, sin credenciales. Cliente no autorizado debe consultar salud limitado y entrar a flujo de emparejamiento, no enviar imágenes.
- [ ] Generar solicitud de autorización con identificador aleatorio del dispositivo y código de un solo uso, expiración corta, límite de intentos y aprobación del administrador del servidor; nunca basar autorización solo en hostname/IP del dispositivo.
- [ ] Guardar token individual cifrado/protegido mediante Windows Credential Manager o DPAPI, fuera de Git; implementar renovación, revocación y borrado en «Desvincular dispositivo».
- [ ] En siguientes inicios, autoconectar con token local y comprobar `health`, auth, versión API y modelo; evitar que el navegador/frontend posea el token: el backend cliente realiza las llamadas al servidor.
- [ ] Permitir modo manual para URL y nueva vinculación; validar esquema `https`, hostname, certificado y evitar SSRF/redirecciones inseguras. No reenviar credenciales a un servidor desconocido por cambiar la URL.
- [ ] Permitir fallback «sin IA remota» y configurar temporalmente `OCR_MOTOR=tesseract`/modo local cuando sea funcional; informar capacidades limitadas, no falsear resultados.
- [ ] Registrar preferencia de conexión por instalación: `automatico`, `manual`, `local`; mostrar estado no sensible y última comprobación; cache segura de URL (sin claves).
- [ ] Implementar diagnósticos con DNS, TLS, conectividad, túnel, HTTP, auth, versión, modelo, GPU y cola; dar solución manual específica por error.
#### Operación doméstica
- [ ] Crear procedimiento para activar servidor/túnel al arrancar Windows mediante servicio/tarea programada solo con aprobación; revisar suspensión, reinicios, firewall, actualización de IP, caída de luz e Internet doméstico.
- [ ] Crear checklist «Antes de exponer» desde la laptop en OTRA red y desde casa; ofrecer prueba sintética privada de extremo a extremo.

## Errores previsibles y recuperación manual
- DNS/TLS/túnel caído: mostrar AI_NET_x y permitir cambiar dirección solo a destino autorizado; usar local o tarea pendiente.
- 401: renovar/vincular; 403: solicitar aprobación; 429: respetar espera; 503: servicio ocupado; discrepancia API: exigir actualización compatible.
- Credencial robada/revocada: no reutilizar; bloqueo y nueva vinculación.
- PC doméstica suspendida: alertar al administrador y reintentar con backoff; no reiniciar indebidamente la laptop del profesor.
- Fallo del proveedor de túnel: ofrecer VPN secundaria previamente habilitada o modo degradado; nunca apagar autenticación por emergencia.

## Pruebas y evidencia obligatoria
- Pruebas automáticas con fake HTTP 200/401/403/408/429/500/503, DNS, TLS expirado, token vencido, cambio de URL maliciosa, redirecciones, rate limit.
- Prueba real red universidad/hotspot vs PC casa, primera vinculación y segundo arranque sin pasos, revocación posterior y recuperación manual.
- Escaneo de secretos y prueba de que no hay token en HTML/JS/README/logs; tráfico Ollama solo loopback.

## Entregables
- Cliente IA remoto reutilizable en backend, endpoints de emparejamiento en servidor, panel básico admin seguro, configuración y tests.
- `fullstack/docs/conexion-remota.md`, `seguridad-servidor-ia.md`, `recuperacion-conexion.md` y guía Cloudflare/Tailscale probada.

## Criterios de aceptación (Definition of Done)
- [ ] Una laptop vinculada previamente se conecta automáticamente desde otra red.
- [ ] Equipo recién clonado requiere primera autorización; ninguna clave se publica en el repositorio.
- [ ] La conexión manual y el modo local funcionan cuando corresponde, sin saltarse controles.
- [ ] Los fallos devuelven códigos y soluciones claras; no se pierden datos.

### Instrucciones obligatorias para Claude (aplican a este Issue)
- ANTES DE MODIFICAR: inspeccionar el estado real de `main`, ramas/PR abiertos, issues anteriores, rutas y contratos; presentar mapa de archivos afectados, dependencias y riesgos. El repositorio tiene `front/`, `back/motori_magenes/`, `fullstack/`, `docs/` (que se migrará), `iniciar.bat`, `iniciar.sh` y `fullstack/compose.yaml`. No asumir Spring Boot: el backend actual es FastAPI.
- REUTILIZAR: preservar endpoints `/analisis` (v1), `/apuntes`, `/trabajos/{id}`, el editor, autenticación, almacenamiento/versiones, PDF y pruebas de regresión. No duplicar lógica ni migrar funcionalidades de manera destructiva.
- DESARROLLO INCREMENTAL: rama `feature/<ID>-descripcion`, cambios pequeños, pruebas antes/después; PR enlazado a este Issue, descripción de archivos, capturas o logs saneados, resultados verificables. No fusionar si CI está roja. No sobrescribir correcciones humanas.
- SEGURIDAD: sin claves, tokens, contraseñas, datos privados, fotografías reales de estudiantes ni modelos pesados en Git. Utilizar `.env.example`, `.gitignore` y almacenamiento seguro del sistema operativo cuando proceda; nunca registrar el contenido de los apuntes ni encabezados de autorización.
- FALLOS: para todo punto crítico, definir comportamiento normal, fallo detectado, reintento acotado, alternativa manual o modo degradado, mensaje útil, código de error, prueba reproducible y forma de recuperación sin pérdida de datos.
- DOCUMENTACIÓN: actualizar las secciones aplicables en `fullstack/docs/`, `front/docs/` y enlaces del `README.md` raíz (una vez hecha la migración del Issue FULL-29); documentar razones técnicas y límites reales, no prometer reconocimiento perfecto.
- BITÁCORA: registrar hora REAL de ejecución y evidencias (commit, PR, test) en `fullstack/tickets/`; los horarios propuestos de este archivo son PLANIFICACIÓN, no trabajo realizado. No inventar fechas históricas ni resultados de pruebas.

## Registro de trabajo (rellenar únicamente al ejecutarlo)
- [ ] Sesión real: YYYY-MM-DD HH:MM–HH:MM (America/Mexico_City). Responsable: ____. Actividad realizada: ____. Evidencia Git SHA / PR / prueba: ____.
- [ ] PR de entrega: URL real: ____. Resultado CI: ____. Riesgos pendientes y plan de reversión: ____.


## Evidencia visual

![Captura del Issue #95](%5BFULL-31%5D%20Conexi%C3%B3n%20remota%20segura%20autom%C3%A1tica%2C%20emparejamiento%20inicial%2C%20configuraci%C3%B3n%20manual%20y%20respaldo%20para%20otras%20redes.png)
