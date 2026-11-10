# Gestión de dependencias y licencias (rúbrica, punto 8)

Auditoría de todas las librerías de terceros: si están **mantenidas y al día**, si tienen **vulnerabilidades conocidas** y si sus **licencias son compatibles** entre sí y con el uso del proyecto.

## 1. Resumen

| Comprobación | Herramienta | Resultado (noviembre de 2026) |
|--------------|-------------|-------------------------------|
| Vulnerabilidades conocidas | `pip-audit` sobre `requirements.txt` y `requirements-dev.txt` | ✅ *No known vulnerabilities found* |
| Versiones obsoletas | `pip index versions` / `pip list --outdated` | ✅ Las 8 dependencias directas de Python están en su **última versión** publicada |
| Licencias | `pip-licenses` y metadatos de cada paquete (39 paquetes en total, incluidas las transitivas) | ✅ **Todas permisivas** (MIT, BSD, Apache-2.0, PSF, MIT-CMU) más una MPL-2.0. **Ninguna GPL** |
| Mantenimiento continuo | Dependabot (`.github/dependabot.yml`) | ✅ PR semanales de actualización, verificados por la CI |
| Repetibilidad | `constraints.txt` con las versiones exactas probadas | ✅ Instalación limpia en un venv → 74 passed |

## 2. Cambios aplicados

| Cambio | Motivo |
|--------|--------|
| `opencv-python` → **`opencv-python-headless`** | El servidor no abre ventanas: la variante *headless* no incluye la interfaz gráfica de Qt (LGPL) ni necesita `libGL`. Es la recomendada por OpenCV para servidores; el código no usa ninguna función gráfica (`imshow`, `waitKey`…). Elimina el error frecuente `ImportError: libGL.so.1` |
| Versiones **acotadas por versión mayor** (`fastapi>=0.110,<1.0`, `numpy>=1.26,<3`…) | Antes eran solo mínimos (`>=`): una versión mayor futura con cambios incompatibles se habría instalado sin aviso |
| **`constraints.txt`** con las versiones exactas probadas | Permite reproducir exactamente el entorno que pasó las pruebas (`pip install … -c constraints.txt`); la CI lo usa |
| **Dependabot** para pip, npm y GitHub Actions | Evita que las dependencias queden obsoletas: cada semana propone las actualizaciones en un PR que la CI comprueba |
| **`pip-audit` en la CI** | Cada PR falla si se introduce una dependencia con una vulnerabilidad conocida |

## 3. Inventario de Python

Versiones probadas. Las dependencias «transitivas» son las que traen las directas.

### Ejecución

| Paquete | Versión | Licencia | Directa |
|---|---|---|---|
| annotated-doc | 0.0.5 | MIT | transitiva |
| annotated-types | 0.8.0 | MIT | transitiva |
| anyio | 4.16.0 | MIT | transitiva |
| certifi | 2026.10.23 | MPL-2.0 | transitiva |
| click | 8.5.0 | BSD-3-Clause | transitiva |
| fastapi | 0.162.0 | MIT | sí |
| h11 | 0.16.0 | MIT | transitiva |
| httpcore | 1.0.9 | BSD-3-Clause | transitiva |
| httptools | 0.9.0 | MIT | transitiva |
| httpx | 0.28.1 | BSD-3-Clause | transitiva |
| idna | 3.20 | BSD-3-Clause | transitiva |
| numpy | 2.5.4 | BSD-3-Clause (+ 0BSD, MIT, Zlib, CC0 en componentes) | sí |
| opencv-python-headless | 5.0.0.93 | Apache-2.0 | sí |
| opentelemetry-api | 1.45.2 | Apache-2.0 | transitiva |
| pillow | 13.0.0 | MIT-CMU | sí |
| pydantic | 2.14.2 | MIT | transitiva |
| pydantic-core | 2.50.2 | MIT | transitiva |
| python-dotenv | 1.2.4 | BSD-3-Clause | transitiva |
| python-multipart | 0.0.33 | Apache-2.0 | sí |
| pyyaml | 6.0.3 | MIT | transitiva |
| starlette | 1.10.0 | BSD-3-Clause | transitiva |
| typing-extensions | 4.16.0 | PSF-2.0 | transitiva |
| typing-inspection | 0.4.4 | MIT | transitiva |
| uvicorn | 0.54.0 | BSD-3-Clause | sí |
| uvloop | 0.23.0 | MIT | transitiva |
| watchfiles | 1.3.0 | MIT | transitiva |
| websockets | 17.4 | BSD-3-Clause | transitiva |

### Desarrollo

| Paquete | Versión | Licencia | Directa |
|---|---|---|---|
| anyio | 4.16.0 | MIT | transitiva |
| certifi | 2026.10.23 | MPL-2.0 | transitiva |
| h11 | 0.16.0 | MIT | transitiva |
| httpcore | 1.0.9 | BSD-3-Clause | transitiva |
| httpx | 0.28.1 | BSD-3-Clause | sí |
| idna | 3.20 | BSD-3-Clause | transitiva |
| iniconfig | 2.3.1 | MIT | transitiva |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | transitiva |
| pluggy | 1.7.0 | MIT | transitiva |
| pygments | 2.21.0 | BSD-2-Clause | transitiva |
| pytest | 9.2.0 | MIT | sí |
| tomli | 2.5.0 | MIT | transitiva |

### Añadidas en la v2

| Paquete | Licencia | Uso |
|---------|----------|-----|
| pytesseract | Apache-2.0 | OCR (BACK-13) |
| **Tesseract 5** (programa del sistema, no de pip) | Apache-2.0 | Motor de OCR; idiomas `spa`/`eng` de tessdata (Apache-2.0) |
| matplotlib (+ contourpy, cycler, fonttools, kiwisolver, pyparsing, python-dateutil, six) | Matplotlib License (tipo PSF), BSD, MIT | Dibujo seguro de fórmulas (mathtext) y fuentes DejaVu con Unicode completo (BACK-15, BACK-20) |
| reportlab (+ charset-normalizer) | BSD, MIT | Generación del PDF (BACK-20). Elegido frente a WeasyPrint: no interpreta HTML/CSS ni descarga recursos y no necesita Pango/Cairo |
| Fuentes DejaVu (incluidas en matplotlib) | Licencia Bitstream Vera / DejaVu (libre, permite incrustarlas) | Texto Unicode seleccionable en el PDF |
| pypdf (solo pruebas) | BSD-3-Clause | Abrir y leer los PDF generados en las pruebas |
| pytest-cov + coverage (solo pruebas) | MIT, Apache-2.0 | Informe de cobertura (BACK-25) |

## 4. Inventario de Node (solo para pruebas; no se distribuye con la aplicación)

| Paquete | Versión | Licencia | Uso |
|---------|---------|----------|-----|
| playwright | ^1.50 (probado con 1.63) | Apache-2.0 | Pruebas de interfaz e integración |
| @commitlint/cli | ^19.8 | MIT | Validación de mensajes de commit |
| @commitlint/config-conventional | ^19.8 | MIT | Reglas de Conventional Commits |

## 5. Recursos externos del frontend

El frontend no tiene dependencias de JavaScript. Solo carga **fuentes de Google Fonts** (Inter, Space Grotesk, Caveat y JetBrains Mono), todas con licencia **SIL Open Font License 1.1**, que permite usarlas en cualquier proyecto, también comercial. Si no cargan (sin Internet), la página usa las fuentes del sistema.

## 6. Compatibilidad de licencias

| Licencia | Paquetes | Obligaciones | ¿Compatible con un proyecto académico o comercial? |
|----------|----------|--------------|------------------------------------------|
| MIT, MIT-CMU, BSD-2/3-Clause, 0BSD, ISC, Zlib | La mayoría (FastAPI, Starlette, uvicorn, Pydantic, NumPy, Pillow, pytest…) | Conservar el aviso de copyright al redistribuir | ✅ Sí |
| Apache-2.0 | OpenCV, python-multipart, opentelemetry-api, Playwright | Conservar los avisos y el archivo NOTICE; incluye una concesión de patentes | ✅ Sí |
| PSF-2.0 | typing-extensions | Conservar el aviso | ✅ Sí |
| MPL-2.0 | certifi (lista de certificados) | Copyleft **por archivo**: solo si se modifican sus archivos hay que publicar esos cambios. Se usa sin modificar | ✅ Sí |
| GPL / AGPL | **Ninguno** | — | — |

**Nota sobre OpenCV:** las ruedas oficiales de `opencv-python-headless` incluyen FFmpeg (LGPL) para leer video. ApuntIA no usa video. Aun así, la LGPL con enlace dinámico (tal como viene en la rueda) es compatible; solo exigiría ofrecer el código de FFmpeg si se **redistribuyera** el binario.

**Pendiente de decisión del equipo:** el proyecto **no tiene archivo `LICENSE`**, así que legalmente nadie más puede reutilizar el código. Todas las dependencias son compatibles con una licencia permisiva (por ejemplo, MIT) o con mantener el código cerrado. Elegirla corresponde a los autores, no a la herramienta.

## 7. Cómo repetir la auditoría

Desde `back/motori_magenes`, con el entorno virtual activo:

```bash
pip install pip-audit pip-licenses
```

```bash
pip-audit -r requirements.txt -r requirements-dev.txt
```

```bash
pip-licenses --format=markdown --with-urls
```

```bash
pip list --outdated
```
