# Definición de Hecho (rúbrica, punto 2: *Definition of Done*)

Un issue está **Hecho** solo si se cumplen **todas** estas condiciones. La plantilla de PR
([`.github/pull_request_template.md`](../../.github/pull_request_template.md)) las incluye como lista para marcar.

| # | Condición | Cómo se verifica |
|---|-----------|------------------|
| 1 | **Rama correcta:** sale de `main`, se llama `<area>-<nn>-<descripcion>` y contiene solo ese issue | Nombre de la rama y commits del PR |
| 2 | **Criterios de aceptación** del issue cumplidos al 100 % | Matriz de [`alcance.md`](alcance.md) |
| 3 | **Pruebas aprobadas** en la CI: backend y evaluación del OCR (pytest), interfaz (Playwright), integración v1/v2 con el backend real, scripts y Docker | Todos los trabajos de [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) en verde (ver [`fullstack/docs/ci.md`](ci.md)) |
| 4 | **Sin vulnerabilidades conocidas** en las dependencias | Paso `pip-audit` de la CI |
| 5 | **Revisado por pares:** al menos 1 aprobación de alguien que no sea el autor | Revisión del PR en GitHub |
| 6 | **Contrato al día:** si cambia la API, se actualizan en el mismo PR `fullstack/docs/api.md`, el mock y las pruebas | Revisión del PR |
| 7 | **Documentación** del cambio actualizada | Revisión del PR |
| 8 | **Commits** con Conventional Commits y referencia al issue | [`CONTRIBUTING.md`](../../CONTRIBUTING.md) |
| 9 | **Listo para UAT:** se puede levantar en el entorno de pruebas sin pasos extra | Sección «Entornos» |

## Entornos

| Entorno | Para qué | Cómo se levanta |
|---------|----------|-----------------|
| **Desarrollo** | Programar y probar en local | [`ejecutar.md`](ejecutar.md): uvicorn con `--reload` + `python -m http.server` |
| **CI** | Verificación automática de cada PR | GitHub Actions ([`ci.yml`](../../.github/workflows/ci.yml)) |
| **UAT** (aceptación) | Que los *stakeholders* prueben el flujo completo | Una computadora del equipo en la red del aula: `uvicorn main:app --host 0.0.0.0` y `python -m http.server 5500 --bind 0.0.0.0`; se abre desde los celulares en `http://<ip>:5500` ([`ejecutar.md`](ejecutar.md#2-abrir-el-frontend), opción c). Lista de aceptación en [`validacion-ux.md`](validacion-ux.md#4-lista-para-la-validación-en-dispositivos-reales-pendiente) |
| **Producción** | — | Fuera del alcance de la v1 académica |

## Configuración que debe hacer un administrador del repositorio

Para que GitHub **impida** fusionar algo que no cumpla la DoD, hay que crear una regla en
*Settings → Branches → Add branch protection rule* (o *Rulesets*) para `main`:

- ☑ *Require a pull request before merging* → *Require approvals*: **1**.
- ☑ *Require status checks to pass before merging* → seleccionar los trabajos de la CI: `Backend, evaluación del OCR y reglas de la interfaz`, `Interfaz (Playwright, API simulada)`, `Integración (interfaz + FastAPI + OCR reales) y scripts` y `Docker (construcción y prueba de humo)`. Aparecen en la lista después de la primera ejecución.
- ☑ *Require branches to be up to date before merging*.
- ☑ *Do not allow bypassing the above settings*.

Es un ajuste del repositorio, no un archivo: no se puede incluir en un commit.

## Estado de la entrega actual frente a la DoD

| Condición | Estado | Detalle |
|-----------|--------|---------|
| 1. Rama correcta | ✅ | Una rama por issue (`back-02-carga-validacion`, …), fusionadas en orden en los PR I-Yane-I/ApuntIA#1–#30 |
| 2. Criterios de aceptación | ✅ / ⏳ | 30 de 30 implementados; las tareas humanas, pendientes ([`alcance.md`](alcance.md)) |
| 3. Pruebas | ✅ | 74 + 20 + 19 en verde, ejecutadas en local. **La CI se añade ahora**: su primera ejecución será en este PR |
| 4. Vulnerabilidades | ✅ | `pip-audit`: *No known vulnerabilities found* |
| 5. Revisión por pares | ❌ **No cumplida** | Los 30 PR se fusionaron sin la aprobación de otro integrante. A partir de ahora, la regla de protección de `main` la hace obligatoria. Se recomienda que el equipo revise a posteriori los PR #1–#30 y deje sus comentarios |
| 6–8 | ✅ | Contrato, documentación y commits vinculados a issues. Para el formato de los commits, ver el punto 6 de la rúbrica ([`historial-git.md`](historial-git.md)) |
| 9. Listo para UAT | ✅ / ⏳ | Se levanta con dos comandos; la sesión de UAT con *stakeholders* está pendiente |
