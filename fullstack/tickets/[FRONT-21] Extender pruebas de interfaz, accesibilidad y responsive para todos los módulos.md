# [FRONT-21] Extender pruebas de interfaz, accesibilidad y responsive para todos los módulos

- Numero de Issue: #81
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/81
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-11-09 17:42:25 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:02:50 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:02:50 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:42:25Z
- Cierre UTC: 2026-11-10T17:02:50Z

- Fecha de captura: 2026-11-24 12:08:47 -0600 (CDMX)
- [Captura original](%5BFRONT-21%5D%20Extender%20pruebas%20de%20interfaz%2C%20accesibilidad%20y%20responsive%20para%20todos%20los%20m%C3%B3dulos-original.png)
- [Captura con metadatos](%5BFRONT-21%5D%20Extender%20pruebas%20de%20interfaz%2C%20accesibilidad%20y%20responsive%20para%20todos%20los%20m%C3%B3dulos.png)

## Descripcion original

## Objetivo
Actualizar Playwright y pruebas de interfaz para cubrir flujos desde foto hasta PDF, cuentas, historial y perfil, incluyendo pantalla móvil y errores reales.

## Contexto técnico y alcance
La suite actual incluye pruebas con API simulada e integración con FastAPI. No reemplazar los tests existentes por capturas visuales ni depender de proveedores externos en cada ejecución.

## Actividades detalladas
- [ ] Inventariar suite Playwright actual y conservar casos de cámara, carga, validación, comparación y PNG.
- [ ] Agregar recorridos E2E de subida multipágina, OCR, corrección, fórmula, investigación opcional y exportación.
- [ ] Agregar tests de registro/login/logout, cambio de contraseña, cuenta A/B e historial.
- [ ] Comprobar responsive en anchos de móvil, tableta y escritorio con capturas de diferencias.
- [ ] Revisar accesibilidad de etiquetas, foco, contraste, teclado, errores y modales, incluyendo editor de fórmulas.
- [ ] Separar suite con mocks reproducibles de suite conectada al backend real; evitar gastos de OCR cloud.
- [ ] Usar datos de prueba sintéticos, limpiar cuentas/archivos y aislar tests paralelos.
- [ ] Publicar reportes de fallo y trazas saneadas en CI.
- [ ] Documentar limitaciones de cámaras, navegadores y equipos realmente probados.

## Criterios de aceptación
- [ ] Los flujos críticos pueden ejecutarse en CI y detectan regresiones evidentes.
- [ ] La interfaz mantiene usabilidad básica móvil y teclado en pantallas nuevas.
- [ ] Pruebas actuales siguen pasando o sus cambios se justifican por contrato aprobado.
- [ ] No se requieren cuentas reales ni claves privadas para pruebas automáticas.

## Pruebas y verificación obligatoria
- Ejecutar suite mock y suite API real; reproducir fallo intencional.
- Comprobar capturas y resultados de teclado y lector de pantalla cuando sea posible.
- Validar casos con dos usuarios y sesión vencida.

## Archivos y entregables esperados
- Suites Playwright ampliadas, fixtures seguras, reportes.
- Matriz navegadores/dispositivos y evidencias.

## Dependencias y coordinación
- **Depende de / coordinar con:** FRONT-11..FRONT-20; FULL-17.
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

![Captura del Issue #81](%5BFRONT-21%5D%20Extender%20pruebas%20de%20interfaz%2C%20accesibilidad%20y%20responsive%20para%20todos%20los%20m%C3%B3dulos.png)
