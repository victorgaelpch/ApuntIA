# [BACK-23] Crear autenticación segura: registro, login, sesión, logout y recuperación de contraseña

- Numero de Issue: #66
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/66
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-11-09 17:35:25 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:29 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:29 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:35:25Z
- Cierre UTC: 2026-11-10T17:02:29Z

- Fecha de captura: 2026-11-24 12:07:35 -0600 (CDMX)
- [Captura original](%5BBACK-23%5D%20Crear%20autenticaci%C3%B3n%20segura-%20registro%2C%20login%2C%20sesi%C3%B3n%2C%20logout%20y%20recuperaci%C3%B3n%20de%20contrase%C3%B1a-original.png)
- [Captura con metadatos](%5BBACK-23%5D%20Crear%20autenticaci%C3%B3n%20segura-%20registro%2C%20login%2C%20sesi%C3%B3n%2C%20logout%20y%20recuperaci%C3%B3n%20de%20contrase%C3%B1a.png)

## Descripcion original

## Objetivo
Permitir cuentas de usuario seguras para acceder a ApuntIA y conservar apuntes. Implementar registro, inicio y cierre de sesión, cambio y recuperación de contraseña con prácticas actuales.

## Contexto técnico y alcance
Elegir estrategia de autenticación consistente con frontend estático y API FastAPI: preferir sesión con cookie `HttpOnly`, `Secure` en HTTPS y `SameSite` apropiado, o tokens si se justifica. Nunca guardar contraseñas en claro ni tokens en localStorage por defecto.

## Actividades detalladas
- [ ] Definir modelo Usuario con identificador, correo único normalizado, nombre visible opcional, hash de contraseña, estado y fechas.
- [ ] Aplicar hashing de contraseña resistente (Argon2id o bcrypt con parámetros correctos) y nunca registrar contraseñas.
- [ ] Agregar rutas de registro, login, usuario actual, logout, cambio de contraseña y recuperación segura por token efímero de un solo uso.
- [ ] Definir mecanismo de sesión/cookie, expiración, renovación e invalidación; usar `Secure` bajo HTTPS y comportamiento local documentado.
- [ ] Implementar validación de correo y política razonable de contraseña; bloquear contraseñas débiles sin reglas arbitrarias imposibles.
- [ ] Aplicar rate limiting a login/registro/restablecimiento y respuestas que no permitan enumerar cuentas por correo.
- [ ] Implementar CSRF para operaciones de estado cuando se usan cookies y configurar CORS con orígenes específicos.
- [ ] Definir envío de correo vía proveedor configurable; si no existe correo configurado, ofrecer modo demo transparente sin flujo falso de restablecimiento.
- [ ] Mantener secretos fuera del repositorio y añadir opciones de configuración documentadas.
- [ ] Integrar errores estables en español, tests, migraciones y documentación de sesión.

## Criterios de aceptación
- [ ] Registro/login/logout funcionan con contraseñas almacenadas como hashes seguros.
- [ ] La sesión expira y puede invalidarse; cambio de contraseña puede invalidar sesiones anteriores según política.
- [ ] La recuperación utiliza tokens únicos, expiran y no pueden reutilizarse.
- [ ] La autenticación resiste intentos básicos de fuerza bruta y no revela usuarios existentes.

## Pruebas y verificación obligatoria
- Contraseñas incorrectas, usuario inexistente, correo repetido, CSRF, sesión expirada y logout.
- Restablecimiento: token inválido/usado/vencido, cambio exitoso y bloqueo de uso repetido.
- Pruebas de cookies, rate limiting y no filtración de información sensible.

## Archivos y entregables esperados
- Modelos y rutas de autenticación con pruebas.
- Configuración de sesiones, correo opcional y seguridad.
- Documentación para frontend y para configuración local/Docker.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-22; FULL-15.
- **Área responsable:** backend.
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

![Captura del Issue #66](%5BBACK-23%5D%20Crear%20autenticaci%C3%B3n%20segura-%20registro%2C%20login%2C%20sesi%C3%B3n%2C%20logout%20y%20recuperaci%C3%B3n%20de%20contrase%C3%B1a.png)
