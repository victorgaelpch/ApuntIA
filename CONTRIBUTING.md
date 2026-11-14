# Cómo contribuir a ApuntIA

## Flujo de trabajo

1. **Un issue = una rama** creada desde `main` actualizado:

```bash
git switch main
```

```bash
git pull
```

```bash
git switch -c back-11-descripcion-corta
```

   Formato del nombre: `<area>-<nn>-<descripcion>`, donde el área es `back`, `front` o `full`.
2. Commits pequeños con el formato de la sección siguiente.
3. PR hacia `main` usando la plantilla (incluye la [Definición de Hecho](fullstack/docs/definicion-de-hecho.md)).
4. La CI debe estar en verde y otro integrante debe aprobar el PR antes de fusionarlo con «Create a merge commit».

## Mensajes de commit: Conventional Commits

```
<tipo>(<ámbito>): <descripción en imperativo y minúscula>

<cuerpo: qué cambia y por qué; cómo se comprobó>

Refs: #<número del issue>
```

**Tipos:**

| Tipo | Cuándo |
|------|--------|
| `feat` | Funcionalidad nueva |
| `fix` | Corrección de un error |
| `perf` | Mejora de rendimiento |
| `refactor` | Cambio de estructura sin cambiar el comportamiento |
| `test` | Pruebas nuevas o corregidas |
| `docs` | Solo documentación |
| `ci` | Integración continua |
| `build` | Dependencias o empaquetado |
| `style` | Formato, sin cambio de lógica |
| `chore` | Mantenimiento |
| `revert` | Revierte un commit anterior |

**Ámbitos:** `back`, `front`, `api` (contrato), `full` (integración), `docs`, `alcance`, `deps`, `git`, `ci`, `tests`.

**Vínculo con el issue (obligatorio):**
- En el pie: `Refs: #3` si el commit avanza el issue, o `Closes #3` en el commit o PR que lo termina.
- Los números son los de los issues de `victorgaelpch/ApuntIA`. Desde un fork, usa la forma completa: `Refs: victorgaelpch/ApuntIA#3`.

**Ejemplos:**

```
feat(back): valida la firma binaria de la imagen recibida

Rechaza archivos que no son JPEG, PNG ni WEBP aunque tengan la extensión
correcta. Probado con un PDF renombrado a .png → 415.

Refs: #3
```

```
fix(full): incluye cabeceras CORS en los errores 500 inesperados

Closes #29
```

**Plantilla en el editor:** para que `git commit` abra el editor con la plantilla:

```bash
git config commit.template .gitmessage
```

**Validación:**
- La CI revisa los commits de cada PR con commitlint (`commitlint.config.cjs`): el formato incorrecto es un **error**; la falta de referencia a un issue, un **aviso**.
- En local, después de `npm install`:

```bash
npm run lint:commits
```

## Qué no hacer

- No reescribir (`push --force`) ramas compartidas ni `main`.
- No mezclar varios issues en una rama o en un commit.
- No subir `.env`, claves ni rutas de una computadora concreta.
