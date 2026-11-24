# [FRONT-17] Diseñar e integrar registro, inicio de sesión y recuperación de contraseña

- Numero de Issue: #77
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/77
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:40:46 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:45 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:45 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:40:46Z
- Cierre UTC: 2026-11-10T17:02:45Z

- Fecha de captura: 2026-11-24 12:08:28 -0600 (CDMX)
- [Captura original](%5BFRONT-17%5D%20Dise%C3%B1ar%20e%20integrar%20registro%2C%20inicio%20de%20sesi%C3%B3n%20y%20recuperaci%C3%B3n%20de%20contrase%C3%B1a-original.png)
- [Captura con metadatos](%5BFRONT-17%5D%20Dise%C3%B1ar%20e%20integrar%20registro%2C%20inicio%20de%20sesi%C3%B3n%20y%20recuperaci%C3%B3n%20de%20contrase%C3%B1a.png)

## Descripcion original

## Objetivo
Implementar pantallas seguras de creación de cuenta, inicio, cierre de sesión y recuperación de acceso, conectadas a las rutas reales del backend.

## Contexto técnico y alcance
El proyecto actual puede usarse sin cuentas; al añadirlas no colocar contraseñas/tokens en HTML, URL, logs o localStorage. Reutilizar módulos JS y diseño existente sin copiar framework sin necesidad.

## Actividades detalladas
- [ ] Crear vistas/formularios de registro, iniciar sesión, contraseña olvidada y restablecimiento cuando API lo soporte.
- [ ] Validar correo, contraseña y confirmación en cliente, pero confiar en backend como autoridad.
- [ ] Integrar cliente HTTP con manejo seguro de cookies/sesiones y token CSRF según contrato.
- [ ] Gestionar redirecciones y estados `sin sesión`, `autenticando`, `sesión activa`, `expirada` y `error`.
- [ ] Presentar errores precisos sin revelar si un correo de otra persona está registrado.
- [ ] Añadir opción mostrar/ocultar contraseña accesible, teclado y etiquetas correctas.
- [ ] No almacenar secretos en `localStorage`, query params, consola o capturas de prueba.
- [ ] Implementar logout real y limpieza de estados/archivos temporales privados del cliente.
- [ ] Conservar o bloquear flujo antiguo sin login de acuerdo con decisión documentada, no por accidente.
- [ ] Probar las pantallas desde servidor local y Docker bajo orígenes y cookies correctos.

## Criterios de aceptación
- [ ] Registro/login/logout se conectan al servidor real y mantienen sesión conforme al contrato.
- [ ] Errores son comprensibles y no filtran existencia de cuentas ni información interna.
- [ ] No quedan contraseñas/tokens expuestos en el navegador de forma insegura.
- [ ] Formularios son accesibles y adaptables a móviles.

## Pruebas y verificación obligatoria
- Playwright usuario nuevo, cuenta existente, contraseña incorrecta, sesión expirada, recuperación válida/expirada.
- Revisión de almacenamiento local/cookies y CSRF.
- Pruebas de redirección a recurso privado y logout.

## Archivos y entregables esperados
- Pantallas de autenticación y módulo de sesión.
- Tests de flujos y textos de ayuda.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-23, FULL-15.
- **Área responsable:** frontend.
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

![Captura del Issue #77](%5BFRONT-17%5D%20Dise%C3%B1ar%20e%20integrar%20registro%2C%20inicio%20de%20sesi%C3%B3n%20y%20recuperaci%C3%B3n%20de%20contrase%C3%B1a.png)
