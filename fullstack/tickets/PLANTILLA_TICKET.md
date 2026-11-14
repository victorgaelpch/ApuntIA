# Plantilla de ticket y de bitácora real

## Bitácora (`fullstack/tickets/bitacora/<ID>.md`)

Una línea por sesión **efectiva**, escrita al terminarla. Copia este formato:

```markdown
# Bitácora real — <ID> (#<número de GitHub>)

- Sesión real: YYYY-MM-DD HH:MM–HH:MM (America/Mexico_City). Responsable: <usuario de GitHub>.
  Actividad: <qué se hizo>. Evidencia: <SHA del commit · URL del PR · comando de prueba y resultado>.
```

Reglas:

- La hora es la del reloj al trabajar, no la del cronograma planificado.
- Sin evidencia verificable (commit, PR, prueba, captura) no hay sesión que registrar.
- Si una sesión no se anotó en su momento, se escribe «hora no registrada» en vez de estimarla.
- Sin contraseñas, tokens, datos personales ni contenido de apuntes de estudiantes.

## Notas manuales de una ficha

Debajo del bloque `<!-- SINCRONIZADO:FIN -->` de cada ficha puedes añadir, por ejemplo:

```markdown
## Notas manuales

- Decisión: <qué se decidió y por qué; alternativa descartada>.
- Bloqueo: <qué falta (hardware, credenciales, aprobación)> desde YYYY-MM-DD.
- Pendiente de prueba real: <qué solo se probó con mocks>.
```

## Estados de una tarea dentro de la ficha

Usa estas palabras exactas para no afirmar más de lo comprobado:

| Estado | Significa |
|--------|-----------|
| implementado | El código existe, sin pruebas que lo demuestren |
| probado con mocks | Pruebas automáticas con dobles (sin hardware/red reales) |
| probado en equipo real | Ejecutado en el equipo destino (indicar cuál) |
| pendiente | No empezado |
| bloqueado | No se puede avanzar sin algo externo (indicar qué) |
