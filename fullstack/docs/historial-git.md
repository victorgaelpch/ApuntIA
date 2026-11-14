# Calidad del historial de cambios (rúbrica, punto 6: *Git Health*)

## 1. Auditoría del historial de `main` (hasta el PR I-Yane-I/ApuntIA#30)

Resultado de pasar cada commit por [commitlint](../../commitlint.config.cjs) y buscar referencias a issues:

| Métrica | Resultado |
|---------|-----------|
| Commits (sin contar merges) | 35 |
| Vinculados a un issue de GitHub (`Refs victorgaelpch/ApuntIA#n`) | **30 de 35** (86 %) |
| Con mensaje descriptivo (qué, por qué y cómo se comprobó) | 30 de 35 |
| En formato Conventional Commits | **0 de 35**: usaban el prefijo `[AREA-NN]` |
| Commits de merge | 33 (uno por PR, con «Create a merge commit»; conservan el vínculo con cada PR) |

**Los 5 commits sin vínculo ni descripción** son los iniciales del equipo, anteriores al backlog:

| Commit | Autor | Mensaje |
|--------|-------|---------|
| `b2a03aa` | victor | Inicializar proyecto |
| `81bc7f4` | victor | Agregado README |
| `782e7bd` | victor | Add README for ApuntIA project setup and usage |
| `e5d29e8` | victor | agregado requeriments.txt |
| `590f832` | l-Yane-l | Add dependencies for FastAPI project |

## 2. Decisión: no reescribir el historial de `main`

Los commits ya están fusionados y compartidos. Reescribirlos con `rebase` + `push --force`:
- cambiaría los identificadores de todos los commits,
- rompería las copias locales de cada integrante,
- y desvincularía los PR I-Yane-I/ApuntIA#1–#30, que apuntan a esos commits.

Por eso se corrige **hacia adelante**:

| Medida | Archivo |
|--------|---------|
| Convención Conventional Commits con vínculo obligatorio al issue | [`CONTRIBUTING.md`](../../CONTRIBUTING.md) |
| Plantilla de mensaje en el editor (`git config commit.template .gitmessage`) | [`.gitmessage`](../../.gitmessage) |
| Validación automática: un formato incorrecto **falla** la CI; la falta de referencia a un issue da un **aviso** | [`commitlint.config.cjs`](../../commitlint.config.cjs) y el trabajo `commits` de [`ci.yml`](../../.github/workflows/ci.yml) |
| Comprobación local | `npm run lint:commits` |
| Lista en cada PR | [`.github/pull_request_template.md`](../../.github/pull_request_template.md) |

Los commits de esta rama (`rubrica-1-2-6-8`) ya siguen el formato: `docs(alcance): …`, `ci: …`, `chore(git): …`, `build(deps): …`.

## 3. Trazabilidad commit ↔ issue ↔ PR, con su equivalente en Conventional Commits

Cada issue tiene **un** commit, en **su** rama y **su** PR. Los números de issue son los de `victorgaelpch/ApuntIA`.

| PR | Issue | Commit | Mensaje actual | Equivalente en Conventional Commits |
|---|---|---|---|---|
| I-Yane-I/ApuntIA#1 | #2 | `98bce9e` | `[BACK-01] …` | `refactor(back): reorganiza el backend de FastAPI en módulos (core, routers, services)` + `Refs: #2` |
| I-Yane-I/ApuntIA#2 | #12 | `400e392` | `[FRONT-01] …` | `feat(front): diseña la interfaz principal de ApuntIA conectada a FastAPI` + `Refs: #12` |
| I-Yane-I/ApuntIA#3 | #22 | `42e15d5` | `[FULL-01] …` | `docs(full): documenta el flujo completo de la aplicación y el alcance de la v1` + `Refs: #22` |
| I-Yane-I/ApuntIA#4 | #24 | `71abcde` | `[FULL-03] …` | `docs(full): define y documenta el contrato de la API (v1.0)` + `Refs: #24` |
| I-Yane-I/ApuntIA#5 | #3 | `02fb493` | `[BACK-02] …` | `feat(back): implementa la carga y validación de imágenes en POST /analisis` + `Refs: #3` |
| I-Yane-I/ApuntIA#6 | #8 | `801eebf` | `[BACK-07] …` | `feat(back): unifica el manejo de errores de la API con códigos y JSON coherentes` + `Refs: #8` |
| I-Yane-I/ApuntIA#7 | #4 | `bc3c7fe` | `[BACK-03] …` | `feat(back): implementa el pipeline reutilizable de procesamiento con OpenCV` + `Refs: #4` |
| I-Yane-I/ApuntIA#8 | #5 | `c3be913` | `[BACK-04] …` | `feat(back): implementa la corrección de perspectiva del pizarrón` + `Refs: #5` |
| I-Yane-I/ApuntIA#9 | #6 | `63e8794` | `[BACK-05] …` | `feat(back): mejora la calidad y nitidez de las imágenes del pizarrón` + `Refs: #6` |
| I-Yane-I/ApuntIA#10 | #7 | `706c1dd` | `[BACK-06] …` | `feat(back): implementa la eliminación de ruido configurable en el pipeline` + `Refs: #7` |
| I-Yane-I/ApuntIA#11 | #10 | `81600f6` | `[BACK-09] …` | `perf(back): optimiza el tiempo de procesamiento: de 862 a 149 ms en fotos de 12 MP` + `Refs: #10` |
| I-Yane-I/ApuntIA#12 | #9 | `de0816a` | `[BACK-08] …` | `test(back): añade 70 pruebas con pytest de los endpoints y del pipeline` + `Refs: #9` |
| I-Yane-I/ApuntIA#13 | #16 | `da52e10` | `[FRONT-05] …` | `feat(front): crea el cliente de la API reutilizable, configurable y con mocks` + `Refs: #16` |
| I-Yane-I/ApuntIA#14 | #11 | `9c397cd` | `[BACK-10] …` | `docs(back): documenta la instalación, ejecución y uso del backend desde cero` + `Refs: #11` |
| I-Yane-I/ApuntIA#15 | #13 | `7151afd` | `[FRONT-02] …` | `feat(front): implementa la carga de imágenes desde el dispositivo con validación` + `Refs: #13` |
| I-Yane-I/ApuntIA#16 | #15 | `17d3586` | `[FRONT-04] …` | `feat(front): muestra la vista previa de la imagen con opciones de cambiar y quitar` + `Refs: #15` |
| I-Yane-I/ApuntIA#17 | #14 | `6d980be` | `[FRONT-03] …` | `feat(front): implementa la captura de fotos con cámara en vivo y alternativas` + `Refs: #14` |
| I-Yane-I/ApuntIA#18 | #17 | `72e1897` | `[FRONT-06] …` | `feat(front): muestra el resultado procesado con comparación, datos y descarga` + `Refs: #17` |
| I-Yane-I/ApuntIA#19 | #18 | `76e8846` | `[FRONT-07] …` | `feat(front): añade indicadores de carga accesibles, cancelación y bloqueo de contr…` + `Refs: #18` |
| I-Yane-I/ApuntIA#20 | #19 | `714621f` | `[FRONT-08] …` | `feat(front): centraliza los mensajes de error y validación con acciones de corrección` + `Refs: #19` |
| I-Yane-I/ApuntIA#21 | #20 | `b3a56cf` | `[FRONT-09] …` | `feat(front): adapta la interfaz a móviles, tabletas y escritorio y corrige el teclado` + `Refs: #20` |
| I-Yane-I/ApuntIA#22 | #21 | `1318849` | `[FRONT-10] …` | `test(front): añade 20 pruebas automatizadas de la interfaz con Playwright y su inf…` + `Refs: #21` |
| I-Yane-I/ApuntIA#23 | #23 | `06e7699` | `[FULL-02] …` | `docs(full): documenta el plan de integración: avances, ramas, bloqueos y decisiones` + `Refs: #23` |
| I-Yane-I/ApuntIA#24 | #25 | `e459d88` | `[FULL-04] …` | `feat(full): integra el frontend con FastAPI: CORS con cabeceras expuestas y guía …` + `Refs: #25` |
| I-Yane-I/ApuntIA#25 | #26 | `b97b3e7` | `[FULL-05] …` | `feat(full): completa el flujo de carga, procesamiento y visualización de extremo …` + `Refs: #26` |
| I-Yane-I/ApuntIA#26 | #27 | `ce7d7ed` | `[FULL-06] …` | `test(full): verifica la compatibilidad de datos entre capas y sincroniza los límites` + `Refs: #27` |
| I-Yane-I/ApuntIA#27 | #28 | `84ce104` | `[FULL-07] …` | `test(full): añade pruebas de integración de extremo a extremo y registra el defec…` + `Refs: #28` |
| I-Yane-I/ApuntIA#28 | #29 | `b6bfaad` | `[FULL-08] …` | `fix(full): corrige D1 (500 sin CORS mostrado como «sin conexión») y documenta la…` + `Refs: #29` |
| I-Yane-I/ApuntIA#29 | #30 | `ae2ce2e` | `[FULL-09] …` | `fix(full): valida la experiencia de usuario y corrige el resultado fuera de pant…` + `Refs: #30` |
| I-Yane-I/ApuntIA#30 | #31 | `8079d78` | `[FULL-10] …` | `docs(full): documenta la arquitectura, los flujos y la configuración, y reescribe…` + `Refs: #31` |

Para ver el historial con su vínculo a los issues:

```bash
git log --no-merges --format='%h %s' --grep='ApuntIA#'
```
