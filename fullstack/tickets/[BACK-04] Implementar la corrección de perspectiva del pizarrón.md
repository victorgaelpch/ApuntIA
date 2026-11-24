# [BACK-04] Implementar la corrección de perspectiva del pizarrón

- Numero de Issue: #5
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/5
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-10-26 11:19:19 -0600 (CDMX)
- Cierre GitHub: 2026-11-03 14:57:11 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-03 14:57:11 -0600 (CDMX)
- Creacion UTC: 2026-10-26T17:19:19Z
- Cierre UTC: 2026-11-03T20:57:11Z

- Fecha de captura: 2026-11-24 12:03:52 -0600 (CDMX)
- [Captura original](%5BBACK-04%5D%20Implementar%20la%20correcci%C3%B3n%20de%20perspectiva%20del%20pizarr%C3%B3n-original.png)
- [Captura con metadatos](%5BBACK-04%5D%20Implementar%20la%20correcci%C3%B3n%20de%20perspectiva%20del%20pizarr%C3%B3n.png)

## Descripcion original

<!-- INICIO BACK-04 -->

# [BACK-04] Implementar la corrección de perspectiva del pizarrón

## Objetivo
Detectar el área del pizarrón y rectificar la fotografía cuando haya inclinación.

## Descripción y alcance
Esta actividad pertenece al área de **Backend** de ApuntIA. El responsable deberá revisar primero lo que ya existe en el repositorio y desarrollar o mejorar únicamente lo necesario, coordinando los cambios de interfaz entre equipos.

## Trabajo a realizar
- [ ] Explorar bordes y contornos.
- [ ] Identificar cuatro esquinas cuando sea posible.
- [ ] Ordenar puntos.
- [ ] Aplicar transformación de perspectiva.
- [ ] Controlar casos donde no se detecta un cuadrilátero fiable.
- [ ] Conservar proporciones legibles.

## Criterios de aceptación
- [ ] Fotografías inclinadas de prueba producen rectificación útil.
- [ ] casos sin detección no bloquean el servicio y reportan resultado adecuado.

## Entregables y evidencias
- Código o documentación incorporados al repositorio mediante una rama y un Pull Request, cuando corresponda.
- Enlace a los commits o Pull Request asociados a este Issue.
- Capturas, resultados de pruebas o ejemplos de solicitudes/respuestas según la actividad.
- Instrucciones breves para que otra persona compruebe el resultado.

## Dependencias y coordinación
BACK-03 (pipeline base).

## Bitácora (registrar en comentarios del Issue)
En cada sesión indicar **fecha**, **tiempo real dedicado**, **trabajo realizado**, **resultado**, **dificultades**, **solución o bloqueo**, **evidencias** y **siguiente paso**. No registrar trabajo como realizado si aún está pendiente.

## Cierre
Mover a **Done** únicamente después de comprobar los criterios de aceptación y dejar evidencias. Si queda bloqueada, explicarlo en comentarios y mantener su estado real.

<!-- FIN BACK-04 -->

## Evidencia visual

![Captura del Issue #5](%5BBACK-04%5D%20Implementar%20la%20correcci%C3%B3n%20de%20perspectiva%20del%20pizarr%C3%B3n.png)
