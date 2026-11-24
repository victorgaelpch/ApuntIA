# [FRONT-05] Preparar la interfaz para comunicarse con la API de FastAPI

- Numero de Issue: #16
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/16
- Estado: closed
- Autor: victorgaelpch
- Responsables: Azul-Lopez
- Etiquetas: frontend
- Creacion GitHub: 2026-10-26 11:27:28 -0600 (CDMX)
- Cierre GitHub: 2026-11-03 14:57:24 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-03 14:57:24 -0600 (CDMX)
- Creacion UTC: 2026-10-26T17:27:28Z
- Cierre UTC: 2026-11-03T20:57:24Z

- Fecha de captura: 2026-11-24 12:04:35 -0600 (CDMX)
- [Captura original](%5BFRONT-05%5D%20Preparar%20la%20interfaz%20para%20comunicarse%20con%20la%20API%20de%20FastAPI-original.png)
- [Captura con metadatos](%5BFRONT-05%5D%20Preparar%20la%20interfaz%20para%20comunicarse%20con%20la%20API%20de%20FastAPI.png)

## Descripcion original

<!-- INICIO FRONT-05 -->

# [FRONT-05] Preparar la interfaz para comunicarse con la API de FastAPI

## Objetivo
Desarrollar la capa cliente que enviará solicitudes al backend; la integración de extremo a extremo se validará en FULL-04.

## Descripción y alcance
Esta actividad pertenece al área de **Frontend** de ApuntIA. El responsable deberá revisar primero lo que ya existe en el repositorio y desarrollar o mejorar únicamente lo necesario, coordinando los cambios de interfaz entre equipos.

## Trabajo a realizar
- [ ] Crear módulo de peticiones http.
- [ ] Centralizar url base configurable.
- [ ] Preparar formdata y encabezados correctos.
- [ ] Interpretar estados y errores.
- [ ] Definir funciones reutilizables para enviar imágenes y consultar resultados.
- [ ] Probar con respuestas simuladas si la api no está lista.

## Criterios de aceptación
- [ ] Existe cliente API reutilizable que sigue el contrato.
- [ ] funciona con mocks.
- [ ] no contiene URL rígida dependiente de una computadora.

## Entregables y evidencias
- Código o documentación incorporados al repositorio mediante una rama y un Pull Request, cuando corresponda.
- Enlace a los commits o Pull Request asociados a este Issue.
- Capturas, resultados de pruebas o ejemplos de solicitudes/respuestas según la actividad.
- Instrucciones breves para que otra persona compruebe el resultado.

## Dependencias y coordinación
FULL-03 (contrato de API); puede utilizar respuestas simuladas.

## Bitácora (registrar en comentarios del Issue)
En cada sesión indicar **fecha**, **tiempo real dedicado**, **trabajo realizado**, **resultado**, **dificultades**, **solución o bloqueo**, **evidencias** y **siguiente paso**. No registrar trabajo como realizado si aún está pendiente.

## Cierre
Mover a **Done** únicamente después de comprobar los criterios de aceptación y dejar evidencias. Si queda bloqueada, explicarlo en comentarios y mantener su estado real.

<!-- FIN FRONT-05 -->

## Evidencia visual

![Captura del Issue #16](%5BFRONT-05%5D%20Preparar%20la%20interfaz%20para%20comunicarse%20con%20la%20API%20de%20FastAPI.png)
