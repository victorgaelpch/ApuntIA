# [FULL-30] Implementar un instalador y menú único de ApuntIA y servidor IA en Windows sin romper los scripts actuales

- Numero de Issue: #94
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/94
- Estado: open
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: fullStack
- Creacion GitHub: 2026-11-13 18:37:50 -0600 (CDMX)
- Cierre GitHub: No registrada / no aplica
- Actualizacion GitHub: 2026-11-13 18:37:50 -0600 (CDMX)
- Creacion UTC: 2026-11-14T00:37:50Z
- Cierre UTC: No aplica

- Fecha de captura: 2026-11-24 12:09:39 -0600 (CDMX)
- [Captura original](%5BFULL-30%5D%20Implementar%20un%20instalador%20y%20men%C3%BA%20%C3%BAnico%20de%20ApuntIA%20y%20servidor%20IA%20en%20Windows%20sin%20romper%20los%20scripts%20actuales-original.png)
- [Captura con metadatos](%5BFULL-30%5D%20Implementar%20un%20instalador%20y%20men%C3%BA%20%C3%BAnico%20de%20ApuntIA%20y%20servidor%20IA%20en%20Windows%20sin%20romper%20los%20scripts%20actuales.png)

## Descripcion original

## Objetivo — FULL-30
Ampliar `iniciar.bat` y scripts de `fullstack/scripts/` con perfiles «Iniciar ApuntIA», «Instalar servidor IA», «Iniciar servidor IA», «Configurar conexión», «Diagnosticar», «Detener» y «Salir». Mantener el mismo repositorio y la instalación actual por script o Docker Compose; en la laptop solo dependencias ligeras y en PC doméstica GPU/Ollama/modelos.

## Contexto real del repositorio
`iniciar.bat` actualmente invoca `fullstack/scripts/iniciar.ps1`; soporta `-Puerto`, `-Red`, `-SinNavegador`, `-SinVenv`, `-Reinstalar`, `-Comprobar`. `fullstack/compose.yaml` ya levanta backend + web. No sustituir este contrato, ni requerir Java/Spring Boot inexistente.

## Dependencias
FULL-29. Coordinar con BACK-35 para instalar/activar el servidor IA.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-11-17 · 18:00–20:00 (America/Mexico_City): Diseño de menú y verificación de compatibilidad de scripts.
- [ ] 2026-11-18 · 18:30–21:00 (America/Mexico_City): Implementación incremental del instalador y perfiles.
- [ ] 2026-11-20 · 17:30–20:30 (America/Mexico_City): Pruebas de arranque/detención y recuperación de errores.

## Tareas técnicas detalladas
#### A. Diseño y compatibilidad
- [ ] Inspeccionar código actual y tests de scripts; conservar `iniciar.bat -Puerto 8080`, modo demo, `detener.bat`, rutas relativas, códigos de salida y ejecución sin interfaz para CI.
- [ ] Al ejecutar sin parámetros en una consola interactiva, mostrar menú accesible con números; con argumentos existentes o sin TTY, conservar arranque clásico sin bloquear por lectura de teclado. Exponer `-Modo app|servidor-ia|instalar-ia|diagnostico` u opción equivalente documentada.
- [ ] Crear configuraciones por rol sin mezclar `APUNTIA_...` de cliente con credenciales IA de servidor. La configuración real es local, ignorada por Git; los `.example` no contienen secretos.
#### B. Perfil «ApuntIA cliente»
- [ ] Instalar/verificar dependencias existentes y abrir la interfaz; no descargar Ollama, CUDA, PyTorch o modelos en la laptop del profesor.
- [ ] Consultar la disponibilidad de IA remota por endpoint de diagnóstico (sin bloquear inicio por una caída) y ofrecer modo local, volver a intentar o configuración manual.
- [ ] Mostrar mensajes claros de puerto ocupado, PATH, Python incompatible, permisos, disco, proxy corporativo y falta de Internet; reanudar instalaciones parciales sin borrar datos.
#### C. Perfil «Servidor IA»
- [ ] Verificar Windows, arquitectura, espacio disponible, Python compatible, NVIDIA RTX/VRAM mediante `nvidia-smi`, controladores y Ollama (versión mínima según modelo). Preparar venv y dependencias con versiones fijadas.
- [ ] Instalar Ollama mediante un procedimiento oficial y confiable: si requiere privilegios o confirmación del usuario, explicar y solicitarla; NO ejecutar instaladores de origen dudoso ni eludir controles de Windows.
- [ ] Descargar Qwen3-VL 8B cuantizado con comprobación de modelo instalado, progreso y reintentos; ofrecer 4B solo como respaldo configurable. No bajar todo en cada inicio.
- [ ] Configurar FastAPI del servidor IA y health/readiness; Ollama escucha solo en loopback. Verificar VRAM real disponible y evitar dos instancias de modelo simultáneas.
- [ ] Permitir iniciar/detener servicios y opcionalmente configurarlos para arranque al iniciar Windows CON consentimiento del administrador; registrar PID/identidad del proceso para no matar procesos ajenos.
- [ ] Comprobar que los archivos de arranque/actualización no interrumpan la aplicación de cliente ya en uso ni borren datos o modelos.
#### D. Docker existente y variantes
- [ ] Mantener funcional `docker compose -f fullstack/compose.yaml up --build -d` para ApuntIA; documentar el modo cliente bajo Docker, cómo recibe URL/configuración externa y cómo conservar el volumen de datos.
- [ ] Si se considera contenedor opcional para el servidor IA, incorporarlo únicamente tras verificar compatibilidad Windows/WSL2/GPU con la RTX 3060; no imponer Docker como requisito de la PC doméstica.

## Errores previsibles y recuperación manual
- Python/Ollama ausente: mensajes y pasos manuales oficiales; el cliente puede abrirse aun sin IA remota.
- GPU incompatible, VRAM insuficiente o modelo no descargable: instalar versión ligera o deshabilitar reconocimiento avanzado, sin prometer que 8B correrá siempre.
- Instalación interrumpida: paso idempotente y reanudable.
- Puerto ocupado: diagnóstico y selección de puerto sin alterar otro proceso.
- Archivo `.env` dañado: respaldo y recuperación a partir de `.env.example` sin pisar credenciales reales.
- Defender/PowerShell bloqueado: documentación de política, firma/ruta o alternativa de ejecución SIN desactivar la seguridad del equipo.

## Pruebas y evidencia obligatoria
- Pruebas PowerShell/Pester o mocks de comandos (sin descarga gigante en CI); arranque antiguo con parámetros y menú nuevo; rutas con espacios y acentos; doble inicio; detener solo procesos propios.
- Prueba real en Windows con hardware RTX 3060 y laptop sin GPU; prueba Docker existente en Linux CI.
- Logs de instalación correctamente sanitizados y prueba de recuperación tras matar el instalador.

## Entregables
- Scripts `iniciar.bat`, `detener.bat` y módulos `fullstack/scripts/` modificados sin romper compatibilidad; pruebas.
- Configuración de ejemplo por perfil; instrucciones de requisitos/espacio/arranque en `fullstack/docs/instalacion-clientes.md` y `fullstack/docs/instalacion-servidor-ia.md`.

## Criterios de aceptación (Definition of Done)
- [ ] En la laptop, un comando inicia ApuntIA y nunca descarga modelos de IA.
- [ ] En la PC de casa, un flujo guiado instala/verifica servidor y modelo con opción de reanudar.
- [ ] Los argumentos antiguos, Docker y modo demo siguen funcionando.
- [ ] Ningún error común obliga a rehacer toda la instalación; hay salida manual segura documentada.

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

-------------------------- FIN DESCRIPCIÓN --------------------------

============================================================================================

ISSUE 03/10 — BACK-35 | BACKEND | PRIORIDAD Crítica
TÍTULO PARA PEGAR EN GITHUB:
[BACK-35] Crear el servicio independiente de inferencia de IA local y su contrato versionado en el mismo repositorio
LABEL: backend
DEPENDENCIAS: FULL-29 para rutas de documentación; trabajo en paralelo con FULL-30.
PLAN DE SESIONES (PROPUESTA, NO HISTORIAL DE TRABAJO):
  - 2026-11-17 · 19:00–21:00 (CDMX) · PROGRAMADO · Inspección de APIs, esquemas y separación de responsabilidades.
  - 2026-11-19 · 18:00–21:00 (CDMX) · PROGRAMADO · Implementación del servidor de inferencia y adaptadores.
  - 2026-11-21 · 10:00–13:00 (CDMX) · PROGRAMADO · Contrato, pruebas simuladas, inferencia real y memoria GPU.

------------------------- INICIO DESCRIPCIÓN (COPIAR EN GITHUB) -------------------------

## Objetivo — BACK-35
Incorporar `ia_servidor/` (o nombre acordado) en el MISMO repo para ejecutar FastAPI + Ollama + Qwen3-VL en la PC Windows de casa, con una API de inferencia robusta, versionada y medible; mantener en el cliente autenticación, SQLite, historial, edición e impresión PDF. El servidor no recibirá contraseñas ni base de datos de usuarios.

## Contexto real del repositorio
ApuntIA ya tiene FastAPI y servicios OpenCV en `back/motori_magenes/`, contratos de trabajos y bloques, OCR parcial y PDF. Reutilizar transformaciones puras sin importar la configuración de base de datos del cliente. Evitar copiar carpetas enteras con divergencia futura.

## Dependencias
FULL-29 para rutas de documentación; trabajo en paralelo con FULL-30.

## Plan de ejecución previsto (no representa horas trabajadas)
- [ ] 2026-11-17 · 19:00–21:00 (America/Mexico_City): Inspección de APIs, esquemas y separación de responsabilidades.
- [ ] 2026-11-19 · 18:00–21:00 (America/Mexico_City): Implementación del servidor de inferencia y adaptadores.
- [ ] 2026-11-21 · 10:00–13:00 (America/Mexico_City): Contrato, pruebas simuladas, inferencia real y memoria GPU.

## Tareas técnicas detalladas
#### Arquitectura del servicio
- [ ] Mapear las funciones actuales de validación, carga, OpenCV, OCR y modelos de bloque; documentar frontera entre procesamiento ligero cliente vs pesado servidor, y proponer `shared/` o paquete instalable solo si evita ciclos y cambios excesivos.
- [ ] Implementar `ia_servidor/app/main.py`, configuración Pydantic, servicios Ollama y esquemas versionados (`api_version`, `model_version`, `pipeline_version`), tests y `requirements.txt` con dependencias fijadas.
- [ ] Definir endpoints mínimos: `GET /salud` (sin datos sensibles), `GET /listo` (Ollama/modelo/GPU/disco), `GET /api/v1/capacidades` (formatos, modalidades, límites), `POST /api/v1/analisis` (o envío de trabajo compatible con BACK-37) y respuesta/errores estructurados; versionar sin modificar v1/v2 existentes.
- [ ] Validar imagen por firma binaria, MIME real, extensión permitida, bytes, meg píxeles, decodificación, contenido vacío, número de páginas, límites de concurrencia y tiempo; proteger contra imágenes bomba y rutas de archivos externas; no aceptar URLs arbitrarias de descarga.
- [ ] Adaptador Ollama con timeout de conexión, lectura y generación, reintentos acotados, estado de carga del modelo, fallos de GPU y memoria; preferir `qwen3-vl:8b` cuantizado, perfil de menor consumo `4b` como contingencia.
- [ ] Usar entrada de imágenes compatible con Ollama (sin subirlas a nubes); respuestas en JSON validadas por esquema estricto con campos de procedencia y alertas de incertidumbre; si el modelo devuelve texto no JSON, corregir una sola vez o marcar error técnico.
- [ ] Aislar Ollama en `127.0.0.1:11434`; servidor API accesible solo a través del túnel autorizado; deshabilitar exposición accidental por 0.0.0.0 en 11434.
- [ ] Registrar métricas: duración, tamaño, tasa de error, modelo y versión, GPU/VRAM, cola y disponibilidad; sin texto, imágenes, tokens ni datos personales en logs.
- [ ] Decidir retención mínima: memoria/transitorio y borrado seguro de temporales; no almacenar apuntes remotos por defecto, sólo devolver análisis estructurado.
- [ ] Documentar errores con código, status HTTP, `retryable`, mensaje público, id correlación y logs sanitizados.

## Errores previsibles y recuperación manual
- Ollama caído/modelo ausente: `NO_DISPONIBLE`/`MODELO_NO_INSTALADO`, endpoint listo no saludable, sin afirmar que se analizó.
- CUDA OOM: descargar modelo, reducir parámetros/recortes/concurrencia o perfil 4B; devolver error recuperable sin perder imagen.
- JSON corrupto / respuesta fuera de contrato: rechazado con detalle técnico sanitizado; nunca salvar basura como apunte final.
- Subida inválida: 400/413/415 consistentes con catálogo existente.
- Modelo tarda mucho: trabajo asíncrono (BACK-37) y estado de espera; no colgar la petición de la interfaz.

## Pruebas y evidencia obligatoria
- Pytest con Ollama falso: respuestas válidas, no JSON, OOM, 401, límite de tamaño, imagen bomba, timeout y errores reproducibles.
- Prueba real en Windows/RTX 3060: `nvidia-smi`, carga 8B (si cabe), inferencia con una de las fotos de prueba; medir VRAM y memoria pico, tiempo y registrar LIMITACIONES sin falsear porcentajes.
- Verificar que el código compartido no importa la base de datos del cliente y que v1 `/analisis` continúa igual.

## Entregables
- `ia_servidor/` con API, adaptador Ollama, schemas, configuración ejemplo, tests, guía técnica y OpenAPI.
- Contrato JSON de documentos/bloques, códigos de error y matriz de compatibilidad cliente-servidor.

## Criterios de aceptación (Definition of Done)
- [ ] Servidor recibe imagen válida, consulta el modelo local y devuelve JSON validado con versión de contrato.
- [ ] No expone Ollama ni credenciales; no requiere la base de datos del cliente.
- [ ] Limitaciones, fallos y capacidades comprobables por endpoints y pruebas.
- [ ] El backend cliente existente sigue pasando sus pruebas.

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

![Captura del Issue #94](%5BFULL-30%5D%20Implementar%20un%20instalador%20y%20men%C3%BA%20%C3%BAnico%20de%20ApuntIA%20y%20servidor%20IA%20en%20Windows%20sin%20romper%20los%20scripts%20actuales.png)
