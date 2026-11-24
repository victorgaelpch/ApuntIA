# [FULL-18] Integrar autenticación, historial de apuntes y permisos de extremo a extremo

- Numero de Issue: #48
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/48
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:25:34 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:12 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:12 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:25:34Z
- Cierre UTC: 2026-11-10T17:05:12Z

- Fecha de captura: 2026-11-24 12:06:08 -0600 (CDMX)
- [Captura original](%5BFULL-18%5D%20Integrar%20autenticaci%C3%B3n%2C%20historial%20de%20apuntes%20y%20permisos%20de%20extremo%20a%20extremo-original.png)
- [Captura con metadatos](%5BFULL-18%5D%20Integrar%20autenticaci%C3%B3n%2C%20historial%20de%20apuntes%20y%20permisos%20de%20extremo%20a%20extremo.png)

## Descripcion original

## Objetivo
Conectar los módulos de identidad, perfiles, almacenamiento e historial para lograr que cada persona pueda iniciar sesión y consultar exclusivamente sus propios apuntes en todas las pantallas y descargas.

## Contexto técnico y alcance
El sistema actual trabaja sin cuentas y devuelve imágenes en la respuesta, sin persistencia. La incorporación de usuarios exige migración de flujos y permisos, nunca exposición directa de carpetas de exportaciones ni URLs públicas permanentes.

## Actividades detalladas
- [ ] Revisar contrato de autenticación y sesión acordado, estado real del backend y almacenamiento.
- [ ] Conectar alta, inicio/cierre de sesión y recuperación de cuenta con el cliente HTTP y estado global de interfaz.
- [ ] Definir comportamiento al refrescar, expirar sesión o abrir una nota mediante enlace; impedir pérdidas de cambios.
- [ ] Integrar dashboard, búsqueda, paginación, detalle, edición, exportación y borrado por propietario.
- [ ] Aplicar autorización en cada endpoint y en las rutas de descarga; no confiar en ocultar botones del frontend.
- [ ] Coordinar CSRF/CORS/orígenes/cookies seguros de acuerdo con los modos script y Docker.
- [ ] Conectar perfil y cambio de contraseña, invalidación de sesiones y mensajes de confirmación.
- [ ] Definir migración de notas existentes sin dueño, si existieran, sin asignarlas arbitrariamente.
- [ ] Comprobar que login y cookies no rompen la demostración ni el endpoint heredado según el alcance aprobado.
- [ ] Preparar pruebas con dos cuentas para comprobar aislamiento y persistencia tras reinicio.

## Criterios de aceptación
- [ ] Los apuntes, PDFs, ediciones y descargas son accesibles únicamente al usuario propietario.
- [ ] Las sesiones tienen expiración, cierre efectivo y tratamiento de errores claro.
- [ ] Los datos siguen disponibles después de reiniciar la app y no aparecen en otro perfil.
- [ ] Los modos local y Docker conservan autenticación y persistencia consistentes.
- [ ] La implementación no registra contraseñas/tokens ni revela rutas privadas.

## Pruebas y verificación obligatoria
- E2E con usuario A/B: intento de leer, editar, borrar y descargar recursos ajenos devuelve 403 o 404 según contrato.
- Probar expiración de sesión, login incorrecto, logout, recuperación/cambio de contraseña y CSRF.
- Smoke de la app desde sesión nueva y después de reiniciar servicios.

## Archivos y entregables esperados
- Integración completa de flujos de cuentas e historial.
- Matriz de permisos y pruebas de aislamiento.
- Guía de despliegue y de migración de datos.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-15; BACK-22..BACK-24; BACK-26; FRONT-17..FRONT-19.
- **Área responsable:** fullStack.
- **Prioridad:** Crítica.

### Reglas obligatorias de implementación para Claude o cualquier desarrollador
- Antes de escribir código, inspeccionar la rama objetivo y el estado REAL del repositorio (`README.md`, `docs/api.md`, `docs/arquitectura.md`, `back/`, `front/`, `fullstack/` si existe, scripts, tests y PR relacionados). No asumir rutas, tecnologías o funcionalidades que no estén presentes.
- NO crear una segunda implementación si ya existe: extender, refactorizar de manera incremental y reutilizar módulos. Resolver discrepancias del código real y documentarlas en el PR.
- Conservar compatibilidad del sistema previo: `POST /analisis` recibe campo `file` y devuelve PNG; `GET /salud` y el formato `{ "error": { "codigo": "...", "mensaje": "..." } }` siguen disponibles salvo decisión explícita y versionada.
- No eliminar ni debilitar validaciones, seguridad, módulos, pruebas ni documentación existentes; no introducir rutas absolutas, claves en el repositorio ni datos privados de alumnos.
- Antes de cerrar, ejecutar tests afectados (y suites disponibles), corregir fallos, revisar integración con frontend/backend/fullstack, actualizar README/contrato/arquitectura y registrar comandos + resultados reales.
- Adjuntar en el PR evidencia reproducible, capturas o archivos sintéticos cuando correspondan, problemas detectados y decisiones técnicas; NO declarar pruebas como aprobadas sin haberlas ejecutado.

## Evidencia y bitácora
- Fecha, responsable, actividades realizadas y tiempo invertido.
- Archivos editados, endpoints/contratos afectados y motivo de cada cambio.
- Comandos de pruebas realmente ejecutados, resultados y capturas/logs saneados.
- Incidencias, soluciones, limitaciones y enlaces al Pull Request/commits.

## Evidencia visual

![Captura del Issue #48](%5BFULL-18%5D%20Integrar%20autenticaci%C3%B3n%2C%20historial%20de%20apuntes%20y%20permisos%20de%20extremo%20a%20extremo.png)
