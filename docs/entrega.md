# Entrega reproducible, versión y demostración (FULL-22)

Cómo instalar ApuntIA desde cero en otro equipo, demostrarla al profesor, publicar una versión y
actualizar sin perder datos. Todo lo que aquí se afirma como «probado» tiene su prueba automática o
su evidencia enlazada; lo que no se ha podido probar se dice.

## 1. Versiones validadas

| Componente | Mínima declarada | Validada (probada de verdad) | Dónde |
|------------|------------------|------------------------------|-------|
| Python | 3.10 | **3.12** (CI y Docker) y **3.13** (instalación con scripts) | `iniciar.sh` exige ≥ 3.10; 3.10 y 3.11 **no** se han probado |
| Tesseract | 5.x con `spa` | **5.3.4** (Ubuntu 24.04, local y Docker) | Paquetes `tesseract-ocr`, `tesseract-ocr-spa` |
| Dependencias de Python | rangos en `requirements.txt` | Versiones exactas de [`constraints.txt`](../back/motori_magenes/constraints.txt): FastAPI 0.162.0, Uvicorn 0.54.0, OpenCV 5.0.0.93, NumPy 2.5.4, Pillow 13.0.0, ReportLab 5.0.1, Matplotlib 3.11.2, pytesseract 0.3.13 | `pip install -c constraints.txt` (los scripts y Docker lo hacen) |
| Docker / Compose | Compose v2 | Docker 29.9.2 + Compose v5.6.1 | Imágenes `ubuntu:24.04` y `nginxinc/nginx-unprivileged:1.27-alpine` |
| Node.js (solo pruebas) | 22 | 22.23.4 | Playwright `^1.50` con Chromium |

Licencias de todo lo anterior: [dependencias.md](dependencias.md) (todas libres). **No hay modelos
que descargar en tiempo de ejecución:** los datos de idioma de Tesseract vienen en los paquetes del
sistema (Linux), en Homebrew (macOS) o en el instalador (Windows), y la integridad de los paquetes de
Python la verifica pip contra PyPI. Las migraciones de la base de datos llevan su propia suma SHA-256.

## 2. Matriz de compatibilidad

| Plataforma | Scripts | Docker | Estado |
|------------|---------|--------|--------|
| Linux (Ubuntu 24.04, x86-64) | ✅ `iniciar.sh` / `detener.sh` | ✅ `compose.yaml` | **Probado** automáticamente (CI y [evidencia de clon limpio](evidencias/full-22-clon-limpio.md)) |
| macOS | ⚠️ mismo `iniciar.sh` | ⚠️ Docker Desktop | **No probado** en un Mac: no se promete |
| Windows 10/11 | ⚠️ `iniciar.bat` → `iniciar.ps1` | ⚠️ Docker Desktop (WSL 2) | **No probado** en Windows: los `.ps1` no se han ejecutado nunca |
| Navegadores | Chromium (pruebas de punta a punta) | | Firefox, Safari y móviles reales: **pendientes** |

Antes de la entrega alguien del equipo debe repetir la sección 3 en un Windows real y anotar el
resultado en esta tabla; hasta entonces, para la demostración, usa Linux o Docker.

## 3. Primera ejecución en un equipo nuevo

Desde la carpeta raíz del repositorio (un clon limpio de la versión):

```bash
./iniciar.sh
```

| Aspecto | Qué esperar |
|---------|-------------|
| Tiempo | Medido en un clon limpio (Linux, 4 núcleos, sin caché de pip): **~40 s** la primera vez (descarga de PyPI; depende de la conexión); **~16 s** las siguientes. Docker: **~1,5 min** de construcción con las imágenes base ya descargadas, más la descarga de esas imágenes la primera vez (depende de la conexión) |
| Espacio | Entorno de Python 383 MB; imágenes Docker 856 MB (backend) + 75 MB (web); Chromium para las pruebas 660 MB; los datos crecen con cada foto (máx. 10 MB por foto) |
| Conectividad | Solo para instalar (PyPI, o los registros de imágenes con Docker) y, si cada persona lo permite, para buscar en Wikipedia. Sin Internet, todo lo demás funciona |
| Puertos | 8000 por defecto, solo en este equipo (`127.0.0.1`). Ocupado → el script lo dice y sale con código 3: usa `--puerto 8080`. `--red` lo abre a la red local (para el móvil) |
| Permisos | No necesita administrador. Escribe solo dentro del repositorio: `back/motori_magenes/.venv`, `back/motori_magenes/datos/` (privado), `fullstack/config/.env` y `fullstack/.estado/` |
| Si falla la descarga | `pip` falla → «Falló la instalación de dependencias», código 2; se reintenta con `./iniciar.sh --reinstalar`. Docker: el error de `compose build` indica el paso; se repite el mismo comando |
| Si falta Tesseract | El script lo avisa; «Mejorar una foto» funciona, pero los apuntes no se analizan y `/api/v2/listo` lo indica |

Las pruebas de estos casos (puerto ocupado, opciones inválidas, PID reutilizado, arranque desde otra
carpeta) están en [`fullstack/tests/scripts`](../fullstack/tests/scripts/scripts.test.js); los códigos de
salida, en [arranque.md](arranque.md).

## 4. Prueba de humo de la entrega

La **misma** prueba principal se ejecuta con los dos métodos de arranque: salud y versión, dependencias
listas, interfaz, `/` de la v1, cuenta nueva, apunte con la foto real de pizarrón (OCR de verdad), PDF;
después se detiene, se vuelve a arrancar y se comprueba que la cuenta, el apunte y el PDF siguen.

```bash
npm run test:entrega
```

| Prueba | Qué hace | Resultado registrado (2026-11-10) |
|--------|----------|-----------------------------------|
| Scripts | `iniciar.sh` → humo → `detener.sh` → `iniciar.sh` → persistencia | ✅ |
| Demostración | `--demo` con datos aparte; los datos reales no se tocan; `--demo-nueva` no borra una carpeta ajena | ✅ |
| Docker | `compose up --build` → humo → `down` → `up` → persistencia | ✅ (con Docker disponible; si no, se omite y lo dice) |

`APUNTIA_DOCKER_SIN_BUILD=1` reutiliza las imágenes ya construidas. El código está en
[`fullstack/tests/entrega`](../fullstack/tests/entrega/).

## 5. Guía de demostración (≈ 10 minutos)

### Preparación (antes de la clase, una vez)

```bash
./iniciar.sh --demo
```

Arranca ApuntIA con los datos en **`fullstack/.demo/`**, separados de los reales, y crea la cuenta
**`demo@example.com`** (la contraseña la muestra el script al terminar) con dos apuntes hechos a partir de fotos
**sintéticas** del banco de evaluación: «Demostración: pizarrón» (texto, ruido y fórmulas) y
«Demostración: cuaderno» (renglones, sombra y un diagrama). Tarda unos 5 s una vez instalado.
Ningún dato de una persona real.

### Recorrido

| Min. | Paso | Qué mostrar | Limitación que conviene decir |
|------|------|-------------|------------------------------|
| 0–1 | `http://localhost:8000/inicio`: «Mejorar una foto» con `back/bd/img/image.png` | Enderezado y contraste en ~1 s, sin cuenta | Devuelve una imagen, no texto |
| 1–2 | Entrar con la cuenta de demostración → «Mis apuntes» | Los dos apuntes, búsqueda y filtros | — |
| 2–5 | Abrir «Demostración: pizarrón» | Cada bloque junto a su región; lo dudoso marcado; fórmula con su LaTeX y vista previa; corregir una palabra y guardar (versión nueva) | Las fórmulas de dos pisos (fracciones apiladas, matrices) se guardan como imagen |
| 5–6 | Abrir «Demostración: cuaderno» | El diagrama se conserva como imagen; los renglones no se leen como texto | La letra manuscrita real se reconoce mal: se marca y se conserva la imagen |
| 6–7 | «Versiones» | Comparar y restaurar la versión anterior | — |
| 7–8 | «Complementos» (opcional) | Permiso, palabras clave, fuente citada | Necesita Internet; si no hay, mostrar el mensaje de «sin conexión» |
| 8–10 | Pestaña «PDF» → generar → descargar | Portada, índice, fórmulas, referencias, en unos segundos | — |
| Extra | Crear un apunte nuevo con una foto propia (pizarrón del aula) | Análisis en vivo: ~1 s por foto | Una foto movida o con reflejos da peor resultado: la ayuda explica cómo hacerla |

### Volver al estado inicial

```bash
./detener.sh
```

```bash
./iniciar.sh --demo-nueva
```

`--demo-nueva` borra **solo** la carpeta de demostración (comprueba antes la marca `.apuntia-demo` que
crea el modo demo; nunca borra una carpeta sin ella) y vuelve a crear la cuenta y los apuntes.
Los datos reales (`back/motori_magenes/datos/` o tu `DATA_DIR`) no se tocan en ningún caso. Para usar
ApuntIA con tus datos de nuevo: `./detener.sh` y `./iniciar.sh` sin `--demo`.

En Windows (sin probar), el equivalente manual es arrancar con `DATA_DIR` apuntando a otra carpeta y
ejecutar `python fullstack\scripts\demo.py http://localhost:8000` con el Python del entorno virtual.
Con Docker, `demo.py` también funciona contra `http://localhost:8000` (necesita el Python del backend en
el equipo, por OpenCV), pero los datos quedan en el volumen de Docker: arranca con un nombre de
proyecto aparte (`COMPOSE_PROJECT_NAME=apuntia-demo`) para que vayan a otro volumen. Este camino no
tiene prueba automática.

## 6. Lista de comprobación de la versión

- [ ] `fullstack/scripts/validar.sh --completo` en verde y `npm run test:entrega` en verde (scripts, demo y Docker)
- [ ] Instalación desde un **clon limpio** siguiendo solo el README ([evidencia](evidencias/full-22-clon-limpio.md))
- [ ] La CI de GitHub en verde en el commit de la versión
- [ ] Versión actualizada en `app/core/config.py`, `package.json`, `docs/api.md` (`/salud`) y [`CHANGELOG.md`](../CHANGELOG.md)
- [ ] Documentación al día: README, ayuda de la interfaz, matriz de compatibilidad (sección 2)
- [ ] Configuración: `fullstack/config/.env.example` sin valores reales; ningún `.env` en el repositorio
- [ ] Migraciones: las nuevas tienen número correlativo y se probaron sobre una base de la versión anterior ([respaldo.md](respaldo.md))
- [ ] Seguridad: lista de [seguridad.md §5](seguridad.md#5-lista-de-comprobación-de-seguridad-para-cada-versión), `buscar_secretos.py` sin hallazgos, `pip-audit` limpio
- [ ] Copia de seguridad probada: `respaldar.sh` → `restaurar.sh` en un entorno limpio
- [ ] Licencias revisadas ([dependencias.md](dependencias.md)); sin fotos reales ni datos de personas en el repositorio ni en las imágenes
- [ ] Etiqueta anotada y publicada (abajo)

### Etiquetar

Cuando la lista esté completa y la rama esté fusionada en `main`:

```bash
git tag -a v2.0.0 -m "ApuntIA 2.0.0: apuntes con cuenta, editor y PDF"
```

```bash
git push origin v2.0.0
```

**Estado de la 2.0.0:** preparada en la rama `v2-ocr-pdf-cuentas`, **sin etiqueta publicada**: falta
fusionarla en `main` y la prueba en Windows (sección 2). La 1.0.0 corresponde al commit `791290f`.

## 7. Actualizar, detener y recuperar

1. **Copia antes de nada:** `fullstack/scripts/respaldar.sh` (con Docker: `respaldar.sh --docker`).
   Además, el servidor hace una copia automática antes de aplicar migraciones nuevas.
2. **Detener:** `./detener.sh` (o `docker compose -f fullstack/compose.yaml down`, **sin** `-v`, que
   borraría el volumen de datos).
3. **Actualizar el código:** `git fetch` y `git checkout v2.0.0` (o la versión nueva).
4. **Arrancar:** `./iniciar.sh` reinstala las dependencias si cambiaron y aplica las migraciones; con
   Docker, `docker compose -f fullstack/compose.yaml up --build -d`.
5. **Comprobar:** `http://localhost:8000/api/v2/listo` debe decir `"listo": true` y la versión en
   `/salud` debe ser la nueva.

**Qué se conserva:** la base de datos y los archivos de `DATA_DIR` (o el volumen `apuntia_datos` de Docker), la
configuración `fullstack/config/.env` y los apuntes de cada cuenta. Nada de eso está en Git.

**Si la actualización falla** (no arranca o una migración da error): el error aparece en
`fullstack/.estado/backend.log` (o `docker compose logs`) y el servidor **no arranca a medias**.
Vuelve a la versión anterior (`git checkout` del commit o la etiqueta anterior; la 1.0.0 es `791290f`) y restaura la copia con
`fullstack/scripts/restaurar.sh <copia>`, que la verifica antes de tocar nada. Procedimiento completo
en [respaldo.md](respaldo.md).
