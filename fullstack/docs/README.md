# Documentación de ApuntIA (`fullstack/docs/`)

Índice de toda la documentación **transversal** del proyecto. La documentación específica de la
interfaz está en [`front/docs/`](../../front/docs/README.md); las notas técnicas internas del
backend viven junto a su código ([`back/motori_magenes/`](../../back/motori_magenes/README.md)).
Los Issues, su cronograma y sus bitácoras están en [`fullstack/tickets/`](../tickets/README.md).

Reglas de ubicación y mapa completo: [ESTRUCTURA_DOCUMENTAL.md](ESTRUCTURA_DOCUMENTAL.md).

> Hasta FULL-29 (noviembre de 2026) esta carpeta estaba en `docs/` en la raíz. Se movió con
> `git mv`, así que `git log --follow fullstack/docs/<archivo>.md` muestra su historial completo.

## Arquitectura, flujo y datos

| Documento | Contenido |
|-----------|-----------|
| [arquitectura.md](arquitectura.md) | Componentes, despliegue, configuración y árbol del repositorio (FULL-10) |
| [flujo.md](flujo.md) | Requerimientos, flujo v1, errores y alcance (FULL-01, FULL-05) |
| [flujo-v2.md](flujo-v2.md) | De la foto al PDF: interfaz, API, trabajos, almacenamiento (FULL-16) |
| [datos.md](datos.md) | Base de datos, archivos privados y migraciones (BACK-22) |
| [permisos.md](permisos.md) | Cuentas, historial y permisos de extremo a extremo (FULL-18) |

## Contratos de la API

| Documento | Contenido |
|-----------|-----------|
| [api.md](api.md) | Contrato v1 (`/analisis`, `/salud`) (FULL-03) |
| [api-v2.md](api-v2.md) | Contrato v2: cuentas, apuntes, trabajos, fórmulas, PDF (FULL-15) |
| [compatibilidad.md](compatibilidad.md) | Compatibilidad real frontend ↔ backend (FULL-06) |
| [servidor-ia.md](servidor-ia.md) | Servidor de inferencia IA en la PC con GPU: arquitectura, contrato v1, errores, límites (BACK-35) |
| [conexion-remota.md](conexion-remota.md) | Vinculación, API `/api/v2/ia`, Tailscale y Cloudflare Tunnel (FULL-31) |

## Arranque, operación y entrega

| Documento | Contenido |
|-----------|-----------|
| [arranque.md](arranque.md) | `iniciar.*` / `detener.*` sin Docker, opciones y códigos de salida (FULL-11) |
| [docker.md](docker.md) | Docker Compose (FULL-13) |
| [instalacion-clientes.md](instalacion-clientes.md) | Laptop: menú, `-Modo`, conexión con el servidor IA y diagnóstico (FULL-30) |
| [instalacion-servidor-ia.md](instalacion-servidor-ia.md) | PC con GPU: Ollama, modelo, arranque y errores (FULL-30) |
| [ejecutar.md](ejecutar.md) | Ejecución manual de las dos partes, CORS, celular (FULL-04) |
| [diagnostico.md](diagnostico.md) | Salud, preparación y manejo de fallos (FULL-21) |
| [respaldo.md](respaldo.md) | Copias de seguridad y recuperación (FULL-23) |
| [recuperacion-conexion.md](recuperacion-conexion.md) | Códigos `AI_*` de la conexión remota y solución manual (FULL-31) |
| [entrega.md](entrega.md) | Instalación desde cero, demostración, versión y actualización (FULL-22) |

## Seguridad y privacidad

| Documento | Contenido |
|-----------|-----------|
| [seguridad.md](seguridad.md) | Auditoría transversal de seguridad (FULL-20) |
| [seguridad-api.md](seguridad-api.md) | Protecciones de la API v2 (BACK-24) |
| [privacidad.md](privacidad.md) | Política de datos (FULL-20) |
| [seguridad-servidor-ia.md](seguridad-servidor-ia.md) | Amenazas y controles del servidor IA y la conexión remota (FULL-31) |
| [dependencias.md](dependencias.md) | Dependencias, vulnerabilidades y licencias |

## Calidad, pruebas y evidencias

| Documento | Contenido |
|-----------|-----------|
| [ci.md](ci.md) | Pruebas y CI de todo el proyecto (FULL-17) |
| [pruebas-backend.md](pruebas-backend.md) | Pruebas del backend (BACK-25) |
| [pruebas-integracion.md](pruebas-integracion.md) | Integración interfaz + FastAPI reales (FULL-07) |
| [evaluacion.md](evaluacion.md) | Banco de evaluación y métricas de OCR, fórmulas y PDF (FULL-19, BACK-28) |
| [aceptacion.md](aceptacion.md) | Aceptación educativa y evidencias de entrega (FULL-24) |
| [validacion-ux.md](validacion-ux.md) | Validación de la experiencia de usuario (FULL-09) |
| [incidencias.md](incidencias.md) | Errores multicapa: causa, solución y evidencia (FULL-08) |
| [evidencias/](evidencias/full-22-clon-limpio.md) | Capturas y registros usados como evidencia (una sola copia) |

## Proyecto y proceso

| Documento | Contenido |
|-----------|-----------|
| [alcance.md](alcance.md) | Cumplimiento del alcance por Issue |
| [definicion-de-hecho.md](definicion-de-hecho.md) | Definition of Done |
| [integracion.md](integracion.md) | Plan de integración, bloqueos y decisiones (FULL-02) |
| [historial-git.md](historial-git.md) | Calidad del historial de cambios |
| [ESTRUCTURA_DOCUMENTAL.md](ESTRUCTURA_DOCUMENTAL.md) | Dónde va cada documento (FULL-29) |
| [Tickets](../tickets/README.md) | Fichas de todos los Issues, cronograma planificado y bitácoras reales (FULL-29) |
