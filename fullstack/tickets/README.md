# Tickets de ApuntIA (`fullstack/tickets/`)

Aquí se consultan **todos** los Issues del proyecto (abiertos y cerrados) con su número real de
GitHub, identificador lógico, responsable, estado, fechas y evidencia, separando lo **planificado**
de lo **realmente trabajado**.

| Archivo | Qué es | ¿Quién lo escribe? |
|---------|--------|--------------------|
| [INDICE.md](INDICE.md) | Tabla de todos los Issues, colisiones detectadas y PRs | Generado por el sincronizador |
| `FULL-n.md`, `BACK-n.md`, `FRONT-n.md`, `issue-n.md` | Una ficha por Issue (enlazadas desde el índice) | Bloque sincronizado + notas manuales |
| [cronograma-planeado.md](cronograma-planeado.md) | Sesiones PROPUESTAS de ApuntIA 3.0 (no es trabajo hecho) | A mano |
| [PLANTILLA_TICKET.md](PLANTILLA_TICKET.md) | Plantilla de bitácora real y de notas de ficha | A mano |
| [bitacora/](bitacora/README.md) | Registro REAL de sesiones: fecha y hora efectivas + commit/PR/prueba | A mano; el sincronizador nunca lo toca |
| [datos/issues.json](datos/issues.json) | Snapshot normalizado de la API de GitHub (uso offline) | Generado |

## Las tres fechas que no hay que confundir

| Campo | Fuente | Significa | NO significa |
|-------|--------|-----------|--------------|
| `created_at` / `updated_at` / `closed_at` | API de GitHub (UTC, mostrado también en CDMX) | Cuándo se creó, modificó o cerró el Issue | Que ese día se trabajó |
| FECHA PLANIFICADA | Descripción del Issue / `cronograma-planeado.md` | Sesión propuesta para repartir el trabajo | Trabajo realizado (aunque la fecha ya haya pasado) |
| REGISTRO REAL | `bitacora/<ID>.md` | Sesión efectiva, con hora real y enlace a commit, PR o prueba | — |

Si una ficha no tiene bitácora se muestra «no registrada»: nunca se estima ni se deduce.
Zona horaria: `America/Mexico_City` (UTC−06:00 todo el año desde el 30/10/2022).

## Sincronizar

Después de crear, cerrar o editar un Issue, o de fusionar un PR:

```bash
python fullstack/scripts/sincronizar_tickets.py
```

- Usa la API pública de GitHub (60 peticiones/hora sin token; el repositorio cabe en 2).
  Para más margen: `GITHUB_TOKEN=<token de solo lectura> python fullstack/scripts/sincronizar_tickets.py`
  (el token se lee del entorno, no se guarda ni se imprime; no lo pongas en archivos).
- Sin Internet: `python fullstack/scripts/sincronizar_tickets.py --offline` regenera las fichas
  desde `datos/issues.json`.
- Si GitHub falla (DNS, red, 403/429 por límite, 5xx, JSON inválido) usa el snapshot, avisa y sale
  con código 3; sin snapshot sale con 2 y no escribe nada. Vuelve a ejecutarlo más tarde.
- Es **idempotente**: si nada cambió en GitHub, no modifica ningún archivo (`git status` limpio).

Reglas que aplica:

- Los Pull Requests **no** generan ficha (la API de Issues los mezcla; se reconocen por
  `pull_request`). Aparecen al final del índice, con los Issues que declaran cerrar.
- El identificador lógico sale del título (`[FULL-29] …`). `FULL-29` **no** es el `#29` de GitHub.
- Sin identificador → `issue-<número>.md`.
- Dos Issues con el mismo identificador → no se pisan: el dueño previo conserva `<ID>.md` y el otro
  va a `<ID>-issue-<número>.md`; el índice registra la colisión.
- En cada ficha solo se reescribe lo que hay entre `<!-- SINCRONIZADO:INICIO -->` y
  `<!-- SINCRONIZADO:FIN -->`. Lo que escribas debajo («Notas manuales») se conserva.

## Registrar trabajo real

1. Al empezar una sesión, anota la hora (la del reloj, no la planificada).
2. Al terminar, añade una línea en `bitacora/<ID>.md` con el formato de
   [PLANTILLA_TICKET.md](PLANTILLA_TICKET.md) y el SHA del commit, el PR o la prueba ejecutada.
3. Ejecuta el sincronizador: la ficha mostrará el número de sesiones reales registradas.

No se registran horas que no ocurrieron, ni se hacen commits con fechas alteradas.

## Conflictos

- Conflicto de Git en una ficha dentro del bloque sincronizado: acepta cualquiera de los dos lados
  y vuelve a sincronizar; el bloque se regenera.
- Conflicto en `bitacora/` o en notas manuales: resolverlo a mano (son datos humanos).
- `INDICE.md` y `datos/issues.json`: acepta cualquiera y vuelve a sincronizar.

## Trello

No se encontró en el repositorio ninguna referencia a un tablero de Trello. Si existe, sus tarjetas
pueden citarse en las notas manuales de cada ficha (enlace sin claves ni tokens).

## Pruebas

```bash
python -m unittest discover -s fullstack/tests/tickets
```
