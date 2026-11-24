# [FULL-13] Implementar arranque alternativo mediante Docker y Docker Compose en fullstack

- Numero de Issue: #43
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/43
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 17:23:14 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:05 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:05 -0600 (CDMX)
- Creacion UTC: 2026-11-09T23:23:14Z
- Cierre UTC: 2026-11-10T17:05:05Z

- Fecha de captura: 2026-11-24 12:05:49 -0600 (CDMX)
- [Captura original](%5BFULL-13%5D%20Implementar%20arranque%20alternativo%20mediante%20Docker%20y%20Docker%20Compose%20en%20fullstack-original.png)
- [Captura con metadatos](%5BFULL-13%5D%20Implementar%20arranque%20alternativo%20mediante%20Docker%20y%20Docker%20Compose%20en%20fullstack.png)

## Descripcion original

## Objetivo
Agregar un segundo modo de ejecución con Docker Compose que levante los componentes efectivos de ApuntIA con un comando. Conservar el arranque local mediante scripts: ambos caminos deben ofrecer la misma funcionalidad principal.

## Contexto técnico y alcance
El `main` consultado documenta frontend estático y FastAPI/OpenCV, NO Spring Boot. Generar imágenes y servicios solo para componentes realmente existentes; agregar servicios adicionales únicamente si se integran y justifican. Los archivos Docker pertenecen a `fullstack/` y deben funcionar desde la raíz mediante un wrapper o comando inequívoco.

## Actividades detalladas
- [ ] Inventariar servicios, puertos, dependencias nativas de OCR/PDF, estado persistente y rutas verdaderas.
- [ ] Crear Dockerfile reproducible para FastAPI y un servicio estático para el frontend (por ejemplo Nginx), usando builds multietapa si procede.
- [ ] Crear `fullstack/compose.yaml` con contextos correctos, red interna, variables de entorno, healthchecks y `depends_on` condicionado por salud cuando aplique.
- [ ] Configurar rutas de API del frontend para funcionar en navegador sin confundir hostname de contenedor con hostname accesible por el usuario; preferir proxy de ruta `/api` si conviene.
- [ ] Agregar volúmenes persistentes únicamente para archivos y base de datos que de verdad requieran persistencia; evitar guardar datos de usuarios en la imagen.
- [ ] Crear `fullstack/.env.example`; separar secretos de configuración, no incluir contraseñas reales y fijar valores locales documentados.
- [ ] Aplicar usuario no root, dependencias fijadas, `.dockerignore`, límites razonables de recursos y cierre ordenado.
- [ ] Incorporar comandos fáciles `docker compose -f fullstack/compose.yaml up --build -d`, `logs`, `down`; opcionalmente wrappers en la raíz.
- [ ] Definir comportamiento de desarrollo vs entrega, política de imágenes/modelos OCR grandes y descarga inicial verificable.
- [ ] Actualizar README y comparar funcionalidad local vs contenedores para carga de imagen, extracción, PDF, autenticación y acceso a archivos cuando estén implementados.

## Criterios de aceptación
- [ ] Con Docker instalado, el usuario puede iniciar ApuntIA con un único comando documentado sin instalar paquetes del proyecto manualmente.
- [ ] Los servicios reportan salud real y el frontend puede llamar a la API sin errores de CORS ni nombres inaccesibles.
- [ ] `docker compose down` finaliza los contenedores y los datos persistentes sobreviven al reinicio cuando corresponde.
- [ ] El arranque local de FULL-11 continúa funcionando y no existe dependencia obligatoria de Docker.
- [ ] La instalación no usa secretos hardcodeados ni publica servicios internos innecesariamente.

## Pruebas y verificación obligatoria
- Build desde cero sin caché en una máquina/CI limpia compatible y smoke tests `GET /salud` y carga de archivo.
- Validar `docker compose config`, los logs, arranque después de reiniciar, persistencia y una petición desde navegador.
- Comparar resultados con el modo script; verificar que ninguno rompe rutas ni contratos existentes.

## Archivos y entregables esperados
- Dockerfile(s), `.dockerignore`, `fullstack/compose.yaml`, ejemplos de variables.
- Script o comando público de arranque/parada Docker.
- README y guía de diagnóstico Docker con evidencias de pruebas.

## Dependencias y coordinación
- **Depende de / coordinar con:** FULL-12; FULL-11 (no sustituir scripts locales).
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

![Captura del Issue #43](%5BFULL-13%5D%20Implementar%20arranque%20alternativo%20mediante%20Docker%20y%20Docker%20Compose%20en%20fullstack.png)
