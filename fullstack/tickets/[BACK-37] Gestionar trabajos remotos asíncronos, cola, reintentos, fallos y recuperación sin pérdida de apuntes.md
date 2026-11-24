# [BACK-37] Gestionar trabajos remotos asíncronos, cola, reintentos, fallos y recuperación sin pérdida de apuntes

- Numero de Issue: #97
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/97
- Estado: open
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-13 18:41:24 -0600 (CDMX)
- Cierre GitHub: No registrada / no aplica
- Actualizacion GitHub: 2026-11-13 18:41:24 -0600 (CDMX)
- Creacion UTC: 2026-11-14T00:41:24Z
- Cierre UTC: No aplica

- Fecha de captura: 2026-11-24 12:09:53 -0600 (CDMX)
- [Captura original](%5BBACK-37%5D%20Gestionar%20trabajos%20remotos%20as%C3%ADncronos%2C%20cola%2C%20reintentos%2C%20fallos%20y%20recuperaci%C3%B3n%20sin%20p%C3%A9rdida%20de%20apuntes-original.png)
- [Captura con metadatos](%5BBACK-37%5D%20Gestionar%20trabajos%20remotos%20as%C3%ADncronos%2C%20cola%2C%20reintentos%2C%20fallos%20y%20recuperaci%C3%B3n%20sin%20p%C3%A9rdida%20de%20apuntes.png)

## Descripcion original

## Objetivo — BACK-37
Evitar bloqueos y pérdidas cuando la IA remota tarda, la PC de casa se suspende, el túnel falla o la GPU se satura; integrar el procesamiento remoto con el sistema EXISTENTE de `/trabajos/{id}`, su reintento y cancelación, evitando crear una segunda fuente de verdad de estados de los apuntes.

## Contexto real del repositorio
Existe `POST /apuntes` con `Idempotency-Key`, API `/trabajos/{id}`, reintentos y estados `pendiente/procesando/completado/parcial/fallido/cancelado`, historial y exportaciones por versión. Preservar exactamente ese comportamiento externo.

## Dependencias
BACK-35 + FULL-31 + esquema BACK-36.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-11-30 · 19:00–21:00 (America/Mexico_City): Diseño de estados de trabajos y reanudación.
- [ ] 2026-12-02 · 18:00–21:00 (America/Mexico_City): Cola y adaptador sin duplicación; códigos de error.
- [ ] 2026-12-04 · 18:00–20:00 (America/Mexico_City): Pruebas de fallos reales y recuperación.

## Tareas técnicas detalladas
- [ ] Inspeccionar gestor actual de trabajos y persistencia; diseñar estados internos remotos y mapeo sin cambiar contratos públicos existentes.
- [ ] Implementar cola persistente simple o respaldada por SQLite para una sola GPU con concurrencia inicial 1; estados, timestamps reales, TTL, prioridad razonable, límite de tamaño de cola, cancelación y recuperación tras reinicio.
- [ ] Diseñar `job_id` del cliente y remoto, clave idempotente por operación/página/versión, deduplicación y persistencia de resultado; los reintentos no generan apuntes/PDF repetidos.
- [ ] Evitar timeout HTTP largo: solicitar procesamiento, consultar progreso con backoff y jitter, finalizar, dar `retry_after` cuando esté saturado.
- [ ] Si se apaga la PC, conservar original/versión y marcar trabajo como reintentable; reanudar tras reconexión solo si el usuario lo solicita o la política lo permite, sin procesamientos duplicados.
- [ ] Recuperar en reinicio servidor los trabajos `procesando` interrumpidos de forma consistente; no reportar `completado` si no existe JSON validado.
- [ ] Definir códigos públicos `AI_NO_DISPONIBLE`, `AI_NO_AUTORIZADA`, `AI_MODELO_AUSENTE`, `AI_MEMORIA_INSUFICIENTE`, `AI_TIEMPO_AGOTADO`, `AI_RESPUESTA_INVALIDA`, `AI_COLA_LLENA`, `AI_CONTRATO_INCOMPATIBLE` con mensajes en español y acción manual sugerida.
- [ ] Implementar modo local existente como alternativa únicamente si está disponible; nunca hacer «fallback silencioso» que cambie el origen sin avisar, y no sustituir texto corregido de versiones anteriores.
- [ ] Métricas y logs con ID de correlación, resultado, latencia y fase; excluir contenido y tokens; purgar temporales y emplear retención/limpieza configurable.
- [ ] Añadir pruebas de simultaneidad y bloqueo SQLite; limitar trabajo de la GPU y no descargar el modelo por cada petición.

## Errores previsibles y recuperación manual
- Timeout/503: reintentar N veces con backoff máximo; después `pendiente de reintento` o `parcial`, sin perder fotos.
- 401/403: NO reintentar en bucle; solicitar vinculación.
- 429: respetar `Retry-After`, mostrar cola/espera y permitir cancelar.
- Cliente pierde Internet mientras trabaja servidor: recuperar por `job_id` al reconectar, sin duplicar facturación/consumo GPU.
- Usuario cierra navegador: progreso persistido, accesible desde historial.

## Pruebas y evidencia obligatoria
- Pruebas de 2-5 solicitudes simultáneas, cancelación, dos reintentos, kill -restart servidor, red caída a mitad de solicitud, respuesta duplicada, cola llena, 401, 429 y tiempo agotado.
- Validación de versiones y permisos: usuario B nunca ve trabajo del usuario A; PDF no se duplica al repetir la petición.
- Auditoría de que el modo antiguo se comporta igual sin servidor IA.

## Entregables
- Implementación de cola y adaptador de trabajo remoto, persistencia e idempotencia, tests, guía de códigos de error, diagnóstico y recuperación en `fullstack/docs/`.

## Criterios de aceptación (Definition of Done)
- [ ] Usuario no pierde un apunte ante reinicio/red caída/GPU ocupada.
- [ ] Estados y reintentos son coherentes con la API existente; no hay duplicados.
- [ ] Cada fallo tiene código, acción manual y test reproducible.
- [ ] Sin acceso cruzado entre usuarios ni filtración de contenidos en logs.

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

![Captura del Issue #97](%5BBACK-37%5D%20Gestionar%20trabajos%20remotos%20as%C3%ADncronos%2C%20cola%2C%20reintentos%2C%20fallos%20y%20recuperaci%C3%B3n%20sin%20p%C3%A9rdida%20de%20apuntes.png)
