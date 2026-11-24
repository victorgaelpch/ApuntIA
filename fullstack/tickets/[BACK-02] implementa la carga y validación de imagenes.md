# [BACK-02] implementa la carga y validación de imagenes

- Numero de Issue: #3
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/3
- Estado: closed
- Autor: victorgaelpch
- Responsables: I-Yane-I
- Etiquetas: backend
- Creacion GitHub: 2026-10-26 10:35:37 -0600 (CDMX)
- Cierre GitHub: 2026-11-03 14:57:08 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-03 14:57:08 -0600 (CDMX)
- Creacion UTC: 2026-10-26T16:35:37Z
- Cierre UTC: 2026-11-03T20:57:08Z

- Fecha de captura: 2026-11-24 12:03:41 -0600 (CDMX)
- [Captura original](%5BBACK-02%5D%20implementa%20la%20carga%20y%20validaci%C3%B3n%20de%20imagenes-original.png)
- [Captura con metadatos](%5BBACK-02%5D%20implementa%20la%20carga%20y%20validaci%C3%B3n%20de%20imagenes.png)

## Descripcion original

<!-- INICIO BACK-02 -->

# [BACK-02] Implementar la carga y validación de imágenes

## Objetivo
Preparar un endpoint para recibir fotografías del pizarrón mediante multipart/form-data y rechazar entradas inválidas.

## Descripción y alcance
Esta actividad pertenece al área de **Backend** de ApuntIA. El responsable deberá revisar primero lo que ya existe en el repositorio y desarrollar o mejorar únicamente lo necesario, coordinando los cambios de interfaz entre equipos.

## Trabajo a realizar
- [ ] Acordar nombre del campo con full stack.
- [ ] Validar archivo presente, tamaño máximo y formatos admitidos (por ejemplo jpeg/png).
- [ ] Comprobar que el contenido pueda decodificarse como imagen.
- [ ] Usar nombres seguros y almacenamiento temporal si procede.
- [ ] Devolver respuestas http claras.

## Criterios de aceptación
- [ ] Imagen válida aceptada.
- [ ] archivo vacío, corrupto, demasiado grande o no permitido rechazado.
- [ ] contrato de entrada/salida documentado.

## Entregables y evidencias
- Código o documentación incorporados al repositorio mediante una rama y un Pull Request, cuando corresponda.
- Enlace a los commits o Pull Request asociados a este Issue.
- Capturas, resultados de pruebas o ejemplos de solicitudes/respuestas según la actividad.
- Instrucciones breves para que otra persona compruebe el resultado.

## Dependencias y coordinación
FULL-03 (contrato de API); puede avanzar en paralelo una vez acordados los campos.

## Bitácora (registrar en comentarios del Issue)
En cada sesión indicar **fecha**, **tiempo real dedicado**, **trabajo realizado**, **resultado**, **dificultades**, **solución o bloqueo**, **evidencias** y **siguiente paso**. No registrar trabajo como realizado si aún está pendiente.

## Cierre
Mover a **Done** únicamente después de comprobar los criterios de aceptación y dejar evidencias. Si queda bloqueada, explicarlo en comentarios y mantener su estado real.
<!-- FIN BACK-02 -->

## Evidencia visual

![Captura del Issue #3](%5BBACK-02%5D%20implementa%20la%20carga%20y%20validaci%C3%B3n%20de%20imagenes.png)
