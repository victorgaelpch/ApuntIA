# Arranque sin Docker con un solo comando (FULL-11)

```bash
./iniciar.sh
```

En Windows: doble clic en `iniciar.bat` (o `iniciar.bat -Puerto 8080` desde una consola).
Para pararla: `./detener.sh` o `detener.bat`.

## 1. Qué hace `iniciar`

| Paso | Detalle |
|------|---------|
| Configuración | La primera vez copia `fullstack/config/.env.example` a `fullstack/config/.env` (no se sube al repositorio) y carga sus variables; las del entorno tienen prioridad |
| Requisitos | Python ≥ 3.10 (obligatorio). Tesseract con `spa` (recomendado: sin él «Mejorar una foto» funciona pero los apuntes no se analizan; se avisa con la orden de instalación). Java solo si existe un backend Spring Boot (ver §3) |
| Puerto | Comprueba que esté libre; si ya responde ApuntIA no arranca otra; si lo usa otro programa, sale con código 3 y propone `--puerto` |
| Entorno de Python | Crea `back/motori_magenes/.venv` e instala `requirements.txt` con `constraints.txt`; solo reinstala si cambian (huella en `fullstack/.estado/`) |
| Arranque | `uvicorn main:app` en segundo plano (PID y registro en `fullstack/.estado/`), en `127.0.0.1` (con `--red`, en toda la red local para el móvil) |
| Espera | Consulta `GET /salud` hasta que responde (máx. 60 s; sin esperas ciegas). Si el proceso muere, muestra las últimas líneas del registro y sale con código 4 |
| Final | Muestra las direcciones y abre el navegador en `/inicio` (salvo `--sin-navegador` o sin escritorio) |

**Un solo servicio:** el backend FastAPI también sirve la interfaz (`/inicio` y `/front/…`), en el
mismo origen que la API, que es lo que necesita la cookie de sesión. No hay que configurar la
comunicación entre servicios ni un servidor web aparte.

Opciones: `--puerto N`, `--red`, `--sin-navegador`, `--sin-venv` (usa el Python actual; CI),
`--reinstalar`, `--comprobar` (solo revisa requisitos y configuración). En Windows: `-Puerto N`,
`-Red`, `-SinNavegador`, `-SinVenv`, `-Reinstalar`, `-Comprobar`.

Códigos de salida: `0` bien · `1` falta un requisito u opción no válida · `2` dependencias ·
`3` puerto ocupado · `4` no arrancó.

## 2. `detener`

Lee los PID de `fullstack/.estado/` y termina **solo** procesos que sigan siendo de ApuntIA
(`uvicorn main:app` o Spring Boot): primero de forma ordenada y, si no terminan en 10 s, forzando.
Si el sistema reutilizó un PID para otro programa, no lo toca.

## 3. Discrepancia: Spring Boot

FULL-11 menciona un backend **Spring Boot**, pero el repositorio **no tiene ninguno**: el backend
es solo Python (FastAPI + OpenCV) en `back/motori_magenes/` (FULL-13 también lo advierte). Los
scripts no lo inventan: buscan `back/<carpeta>/pom.xml` o `build.gradle` y, **si algún día existe**,
comprueban Java y lo arrancan con su Maven/Gradle Wrapper (`mvnw`/`gradlew`), sin exigir Maven
instalado; si no tiene wrapper, lo explican. Hoy muestran «Sin backend Spring Boot en el
repositorio: no hace falta Java».

## 4. Puertos y variables

| Variable | Por defecto | Uso |
|----------|-------------|-----|
| `APUNTIA_PUERTO` | 8000 | Interfaz y API |
| `DATA_DIR` | `datos` (en `back/motori_magenes`) | Base de datos y archivos privados |
| `OCR_MOTOR`, `OCR_IDIOMAS` | `tesseract`, `spa+eng` | Reconocimiento de texto |
| `COOKIE_SEGURA` | `0` | `1` solo detrás de HTTPS |
| `INVESTIGACION_PROVEEDOR` | `wikipedia` | `ninguno` para trabajar sin Internet |

El resto está comentado en `fullstack/config/.env.example` y `back/motori_magenes/.env.example`.
No hay rutas absolutas: todo se calcula desde la ubicación del script, así que funciona desde
cualquier carpeta y en cualquier equipo.

## 5. Qué se probó

| Sistema | Resultado |
|---------|-----------|
| Linux (Python 3.13, Tesseract 5.3.4) | `iniciar.sh` desde cero: crea el entorno, instala y arranca en ~20 s; `detener.sh` lo para. Pruebas automáticas: `npm run test:scripts` (5 casos: ayuda y comprobación, opciones y puertos no válidos, puerto ocupado, arrancar desde otra carpeta + no duplicar + detener, no matar un PID ajeno, detección de Spring Boot) |
| macOS | Mismo `iniciar.sh` (bash, `open` para el navegador). **No probado** en un Mac |
| Windows | `iniciar.bat`/`detener.bat` → `iniciar.ps1`/`detener.ps1` (PowerShell 5.1+). **No se pudieron ejecutar en este entorno (sin Windows ni PowerShell)**: están escritos para ser equivalentes, pero falta probarlos en un equipo con Windows antes de la entrega |

## 6. Problemas frecuentes

| Mensaje | Solución |
|---------|----------|
| «Hace falta Python 3.10 o superior» | Instálalo (en Windows, marca «Add python.exe to PATH») |
| «No se pudo crear el entorno virtual» | Debian/Ubuntu: `sudo apt install python3-venv` |
| «Tesseract no está instalado» | Linux: `sudo apt install tesseract-ocr tesseract-ocr-spa`; macOS: `brew install tesseract tesseract-lang`; Windows: instalador de UB-Mannheim con el idioma Spanish |
| «El puerto 8000 está ocupado» | `./iniciar.sh --puerto 8080` |
| «ApuntIA no arrancó» | Revisa `fullstack/.estado/backend.log` |
