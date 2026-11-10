# Pruebas y CI de todo el proyecto (FULL-17)

## 1. Un solo comando

```bash
fullstack/scripts/validar.sh
```

| Modo | Qué ejecuta | Tiempo aprox. |
|------|-------------|---------------|
| `--rapido` (por defecto) | pytest del backend (370), evaluación real del OCR y las fórmulas y banco de evaluación contra la línea base (si hay Tesseract), búsqueda de secretos, enlaces de la documentación, catálogo y reglas de seguridad de la interfaz, sintaxis de scripts, workflows y `compose.yaml` | 1,5 min |
| `--completo` | además: interfaz con API simulada (Playwright), integración v1/v2 con el backend real (incluida accesibilidad), scripts de arranque y humo de entrega con reinicio y demostración | 6,5 min |
| `--docker` | además: construir las imágenes, la prueba de humo de Docker Compose y el humo de entrega con `down` + `up` | +3 min |

`--informes CARPETA` guarda informes JUnit (y capturas de la interfaz). El script ejecuta todos los
pasos aunque alguno falle, muestra un resumen y **sale con 1** si algo falló (comprobado
introduciendo un test roto a propósito). También detectó un error real al crearlo: un nombre de
paso del workflow con «: » sin comillas, que hacía inválido el YAML.

## 2. Clasificación de las pruebas

| Tipo | Dónde | Comando suelto |
|------|-------|----------------|
| Unitarias del backend | `back/motori_magenes/tests/` | `python -m pytest` |
| Contrato de la API (v1 congelado, IDOR por ruta, catálogo de errores) | `test_regresion.py`, `test_seguridad_api.py`, `front/tests/catalogo.test.js` | idem |
| Evaluación real (opt-in) | `tests/test_evaluacion.py` | `python -m pytest -m evaluacion` |
| Rendimiento (opt-in) | `tests/test_rendimiento.py` | `python -m pytest -m rendimiento -s` |
| Unitarias de la interfaz | `front/tests/catalogo.test.js` | `npm run test:front` |
| Interfaz con API simulada | `front/tests/interfaz.test.js` | `npm run test:front` |
| Integración y E2E con backend real | `fullstack/tests/integracion/` | `npm run test:integracion` |
| Scripts de arranque | `fullstack/tests/scripts/` | `npm run test:scripts` |
| Humo de despliegue (Docker) | `fullstack/tests/docker/` | `npm run test:docker` |
| Humo de entrega: el mismo en scripts y Docker, reinicio, demostración (FULL-22) | `fullstack/tests/entrega/` | `npm run test:entrega` |
| Mutaciones (¿detecta regresiones?) | `back/motori_magenes/herramientas/mutaciones.py` | `python herramientas/mutaciones.py` |

Detalle: [`docs/pruebas-backend.md`](pruebas-backend.md) y [`docs/pruebas-interfaz.md`](pruebas-interfaz.md).

## 3. GitHub Actions (`.github/workflows/ci.yml`)

En cada push a `main` y en cada pull request, en `ubuntu-24.04` (Tesseract 5.3.4, la versión con
la que se midió el OCR):

| Trabajo | Contenido | Artefactos |
|---------|-----------|------------|
| Mensajes de commit | commitlint (solo en PR) | — |
| Backend, evaluación del OCR y reglas de la interfaz | `validar.sh --rapido`, cobertura, `pip-audit` | JUnit, `cobertura.xml` |
| Interfaz (Playwright, API simulada) | `front/tests/*.test.js` | JUnit |
| Integración y scripts | Todas las suites de `fullstack/tests/integracion/` (una a una), `test:scripts` y el humo de entrega con scripts | JUnit y capturas |
| Docker | Construir, prueba de humo y humo de entrega (`down` + `up`) | Registros de los contenedores si falla |

- **Sin secretos ni servicios personales:** las cuentas son sintéticas (`@example.com`), las fotos se
  generan en el navegador o son del corpus sintético, la investigación usa una Wikipedia simulada
  y no se usa OCR en la nube.
- **Esperas reales, no ciegas:** los backends se dan por listos cuando `/salud` responde; los
  trabajos se consultan hasta su estado final.
- **Puertos:** cada suite pide un puerto libre al sistema; las de integración se ejecutan una a una
  porque varios OCR en paralelo saturaban la CPU y superaban los tiempos.
- **Cobertura** (95 % del backend) como informe, sin umbral obligatorio: la calidad la miden las
  mutaciones y las pruebas de regresión.
- **Bloquear la fusión:** la CI informa; para que GitHub impida fusionar con trabajos en rojo, el
  dueño del repositorio debe activar la protección de `main` con estos trabajos como *required
  status checks* (ver `docs/definicion-de-hecho.md`).

## 4. Reproducir un fallo de CI en local

1. Descarga el artefacto del trabajo (JUnit con el nombre de la prueba; capturas de la interfaz).
2. Ejecuta solo esa suite, p. ej. `node --test fullstack/tests/integracion/v2-pdf.test.js`, o
   `python -m pytest tests/test_pdf.py -k nombre`.
3. Con capturas: `CAPTURAS=capturas node --test fullstack/tests/integracion/v2-recorrido.test.js`.

## 5. Estado de la verificación

El workflow es YAML válido y cada paso se ejecutó en local con los mismos comandos (rápido: 5/5;
`--completo` en 6 min: integración 111 casos en verde, interfaz 29, scripts 5; Docker 2/2). La ejecución en GitHub
Actions se verá al abrir el pull request: desde este entorno no se puede lanzar.
