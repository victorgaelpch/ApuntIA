# [FRONT-19] Implementar perfil de usuario, preferencias y cambio seguro de contraseña

- Numero de Issue: #79
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/79
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:41:50 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:47 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:48 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:41:50Z
- Cierre UTC: 2026-11-10T17:02:47Z

- Fecha de captura: 2026-11-24 12:08:38 -0600 (CDMX)
- [Captura original](%5BFRONT-19%5D%20Implementar%20perfil%20de%20usuario%2C%20preferencias%20y%20cambio%20seguro%20de%20contrase%C3%B1a-original.png)
- [Captura con metadatos](%5BFRONT-19%5D%20Implementar%20perfil%20de%20usuario%2C%20preferencias%20y%20cambio%20seguro%20de%20contrase%C3%B1a.png)

## Descripcion original

## Objetivo
Construir página de Perfil/Configuración para consultar y cambiar información personal autorizada, preferencias de apuntes, contraseña y opciones de privacidad/gestión de cuenta.

## Contexto técnico y alcance
El perfil debe operar con rutas reales y validaciones de backend, sin ofrecer controles falsos que no guarden cambios.

## Actividades detalladas
- [ ] Crear vista de datos de cuenta: nombre visible, correo, fecha de creación si expuesta y estados pertinentes.
- [ ] Implementar edición de datos permitidos, confirmación y error de duplicados o validación.
- [ ] Implementar cambio de contraseña con contraseña actual y confirmación de la nueva según contrato.
- [ ] Permitir configurar preferencias documentadas (idioma, plantilla PDF, incluir fuentes, nivel de detalle) y guardarlas si backend lo soporta.
- [ ] Proporcionar controles transparentes sobre consentimiento de investigación externa y uso de imágenes.
- [ ] Agregar opciones de cierre de sesión (y otras sesiones si backend las soporta) y borrado de cuenta con confirmación fuerte.
- [ ] Revalidar sesión y manejar 401/403 sin pérdida insegura de datos privados.
- [ ] No mostrar datos sensibles en HTML oculto ni conservar password en estado después de enviar.
- [ ] Aplicar accesibilidad, ayuda contextual y estados guardando/guardado/error.

## Criterios de aceptación
- [ ] Las preferencias y datos se guardan y pueden recuperarse tras login posterior.
- [ ] El cambio de contraseña requiere validación real y no expone valores sensibles.
- [ ] Controles de privacidad aplican en backend, no solo visualmente.
- [ ] Borrado de cuenta muestra advertencias claras y confirmación explícita si se implementa.

## Pruebas y verificación obligatoria
- Editar perfil, recuperar valores, contraseña incorrecta, expiración de sesión.
- Verificar limpieza de campos de password y errores de validación.
- Pruebas de accesibilidad y móvil.

## Archivos y entregables esperados
- Página Perfil/Configuración, lógica JS segura.
- Tests funcionales y guía de usuario.

## Dependencias y coordinación
- **Depende de / coordinar con:** BACK-23, BACK-24, FRONT-17.
- **Área responsable:** frontend.
- **Prioridad:** Alta.

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

![Captura del Issue #79](%5BFRONT-19%5D%20Implementar%20perfil%20de%20usuario%2C%20preferencias%20y%20cambio%20seguro%20de%20contrase%C3%B1a.png)
