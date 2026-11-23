# Instrucciones para Claude Code en ApuntIA

Las convenciones completas están en [CONTRIBUTING.md](CONTRIBUTING.md). Lo que más se olvida:

## Autoría de los commits

- **El autor de cada commit es la persona del equipo que dirige la sesión**, no Claude. Claude
  figura solo como coautor, con la línea `Co-Authored-By: Claude …` al final del mensaje.
- Antes del primer commit de la sesión, ejecuta `git config user.email`. Si está vacío o es
  `noreply@anthropic.com` (lo normal en Claude Code en la web), **no hagas commit todavía**:
  pregunta a la persona con qué nombre y correo de GitHub firma, y configúralo solo en este
  repositorio:

  ```bash
  git config user.name "Nombre"
  git config user.email "correo-vinculado-a-su-cuenta-de-GitHub"
  ```

  Usa siempre el correo que esa persona te indique (el de su cuenta de GitHub, o su dirección
  `…@users.noreply.github.com`). No lo deduzcas de otros commits, porque podría ser de otra persona.
- **No quites** la línea `Co-Authored-By` ni el enlace de la sesión cuando Claude escribió el
  cambio: declarar la ayuda de la IA es parte de la honestidad del historial, y GitHub no cuenta a
  los coautores en *Contributors*.
- No reescribas el historial compartido ni hagas `push --force` sobre `main` o ramas de otros.

## Formato

Conventional Commits en español, con el issue en el pie (`Refs: #N` o `Closes #N`); la CI lo revisa
con commitlint.
