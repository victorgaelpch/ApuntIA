# [FRONT-25] Añadir panel de estado IA, conexión automática/manual, vinculación y diagnóstico accesible

- Numero de Issue: #98
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/98
- Estado: open
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-13 18:42:20 -0600 (CDMX)
- Cierre GitHub: No registrada / no aplica
- Actualizacion GitHub: 2026-11-13 18:42:20 -0600 (CDMX)
- Creacion UTC: 2026-11-14T00:42:20Z
- Cierre UTC: No aplica

**Captura no disponible:** Locator.wait_for: InvalidSelectorError: Error while parsing selector `heading[name=/\[FRONT\-25\]\ Añadir\ panel\ de\ estado\ IA,\ conexión\ automática/manual,\ vinculación\ y\ diagnóstico\ accesible/i]` - unexpected symbol "a" at position 83 during parsing attribute value
    at syntaxError (<anonymous>:2050:11)
    at readAttribute (<anonymous>:2182:7)
    at parseAttributeSelector (<anonymous>:2195:28)
    at Object.queryAll (<anonymous>:5578:22)
    at InjectedScript._queryEngineAll (<anonymous>:7292:49)
    at InjectedScript.querySelectorAll (<anonymous>:7279:30)
    at eval (eval at evaluate (:370:30), <anonymous>:2:42)
    at UtilityScript.evaluate (<anonymous>:372:16)
    at UtilityScript.<anonymous> (<anonymous>:1:44)
Call log:
  - waiting for internal:role=heading[name=/\[FRONT\-25\]\ Añadir\ panel\ de\ estado\ IA,\ conexión\ automática/manual,\ vinculación\ y\ diagnóstico\ accesible/i] >> nth=0 to be visible


## Descripcion original

## Objetivo — FRONT-25
Ofrecer una experiencia clara y accesible: la aplicación se abre aunque falle el servidor de casa; muestra si la IA está conectada, en cola, procesando o en modo local y permite diagnóstico, reintento, configuración manual o emparejamiento, SIN exponer credenciales al navegador.

## Contexto real del repositorio
Respetar `front/`, la navegación actual, editor de apuntes, historial, login/perfil y mensajes de validación. No recrear pantallas o tablas existentes ni llamar directamente desde el navegador al servidor IA.

## Dependencias
FULL-31 para endpoints y BACK-37 para estado de trabajos; usar mocks mientras tanto.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-11-28 · 16:00–18:00 (America/Mexico_City): Diseño UX de conexión y estados con API simulada.
- [ ] 2026-11-30 · 18:00–20:30 (America/Mexico_City): Interfaz de emparejamiento, perfil y mensajes.
- [ ] 2026-12-02 · 18:30–20:30 (America/Mexico_City): Pruebas E2E, teclado y navegación móvil.

## Tareas técnicas detalladas
- [ ] Inspeccionar estructura HTML/JS/CSS existente, componentes reutilizables, estados, ARIA, tests, responsive y catálogo actual de errores.
- [ ] Añadir indicador de estado (IA conectada / no autorizada / procesando / en cola / offline / procesamiento local) con texto además de color y sin polling agresivo.
- [ ] Crear pantalla/modal «Conexión IA» con automático (predeterminado), manual, continuar sin IA y diagnóstico. Mostrar URL sin secretos, cambios validados y test de conexión seguro a través del backend local.
- [ ] Diseñar primera vinculación con código temporal/solicitud para autorización del administrador y estados pendiente, aceptado, rechazado, expirado; ofrecer volver a vincular sin recargar toda la web.
- [ ] Mostrar códigos de error (`AI_...`) traducidos a español, acción concreta, botón reintentar y enlace al apartado correcto de ayuda, sin detalles internos ni trazas.
- [ ] Informar que el servidor remoto está en casa y puede estar apagado; explicar qué partes (edición, historial, PDF y mejora local) siguen disponibles.
- [ ] En creación de apunte, mostrar progreso real por fases/página, estado pendiente/cola, posibilidad de cancelar y acceso al resultado al reabrir la página.
- [ ] La URL de IA y el token nunca se guardan en `localStorage` ni en JS público; configuración y llamadas sensibles solo en el backend local. No romper protección CSRF/CORS ni sesiones de usuario.
- [ ] Mantener UX con teclado, lector pantalla, mensajes aria-live, foco, colores accesibles y vista móvil; nunca bloquear la interfaz con un spinner infinito.
- [ ] Crear `front/docs/CONEXION_IA_UI.md`, `ESTADOS_Y_ERRORES.md` y pruebas con capturas desde Playwright.

## Errores previsibles y recuperación manual
- Red caída: mostrar «Conexión interrumpida. Tu apunte está guardado» con reintentar.
- Credencial caducada: proceso de nueva vinculación; no pedir claves secretas por chat/URL.
- Modelo no listo/cola llena: informar espera aproximada sin inventar tiempos.
- Servidor ambiguo o URL malformada: no guardar, explicar restricción HTTPS.
- Usuario cambia de página: continuar mostrando trabajo desde historial.

## Pruebas y evidencia obligatoria
- Playwright con estados 200, pendiente, 401/403, 429, 503, sin respuesta, rechazada y caducada; probar dispositivo móvil, teclado y lector.
- Validación estática sin tokens en bundle ni peticiones cliente directo a Cloudflare.
- No romper creación de notas, historial, editor y exportación PDF existente.

## Entregables
- Cambios mínimos de HTML/JS/CSS y front/tests; `front/docs/` con guías de pantallas y troubleshooting para usuarios.
- Capturas verificables antes/después y evidencia E2E.

## Criterios de aceptación (Definition of Done)
- [ ] Cualquier estado de conexión muestra mensaje y acción en español.
- [ ] Modo local disponible y trabajos no se pierden al navegar.
- [ ] Sin secretos en browser; endpoints via backend local.
- [ ] Frontend existente y accesibilidad conservados.

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


