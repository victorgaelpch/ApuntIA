# Evidencia: instalación desde un clon limpio (FULL-22)

**Fecha:** 2026-11-10 · **Commit:** el de esta versión (rama `v2-ocr-pdf-cuentas`) · **Equipo:** contenedor
Linux Ubuntu 24.04, x86-64, 4 núcleos, Python 3.13.18, Tesseract 5.3.4, **sin caché de pip**
(`PIP_NO_CACHE_DIR=1`) y sin entorno virtual previo.

Se siguió solo el README: clonar, `./iniciar.sh`, usarla, detener, y el modo demostración. La prueba
de humo es la misma de `npm run test:entrega` (salud y versión, dependencias listas, interfaz, cuenta
nueva, apunte con la foto real de pizarrón, OCR y PDF).

## Qué encontró esta prueba (y se corrigió antes de la versión)

1. **El clon limpio no arrancaba:** `ModuleNotFoundError: No module named 'app.datos'`. La regla
   `datos/` del `.gitignore` excluía también el paquete de código `back/motori_magenes/app/datos/`, que
   nunca había llegado al repositorio (en el equipo de desarrollo existía y todas las pruebas pasaban).
   Corregido en el commit `9ff37ce`.
2. **La demostración tardaba 3 min 8 s** porque dos análisis simultáneos se estorbaban (hilos OpenMP de
   Tesseract). Con `OMP_THREAD_LIMIT=1` (commit `4ad4fea`): 5 s.

## Transcripción (salida real, sin colores)

```text
$ git clone … && cd ApuntIA
$ ./iniciar.sh --sin-navegador
✔ Creada la configuración local fullstack/config/.env (puedes editarla).
▶ Comprobando requisitos
✔ Python 3.13.18
✔ Tesseract 5.3.4 (idiomas: eng osd spa )
✔ Sin backend Spring Boot en el repositorio: no hace falta Java.
✔ Puerto 8783 libre
▶ Creando el entorno virtual back/motori_magenes/.venv
▶ Instalando dependencias de Python (puede tardar unos minutos la primera vez)
✔ Dependencias listas
▶ Iniciando ApuntIA en http://localhost:8783
✔ ApuntIA está lista

  Mejorar una foto (sin cuenta):  http://localhost:8783/inicio
  Apuntes con cuenta:             http://localhost:8783/front/apuntes.html
  Documentación de la API:        http://localhost:8783/docs
  Registro del servidor:          fullstack/.estado/backend.log
  Para detenerla:                 ./detener.sh

real	0m44.013s
user	0m11.480s
sys	0m1.022s
$ npm run test:entrega (prueba de humo principal contra esta instalación)
humo OK en 1.0 s: cuenta, apunte con OCR y PDF
$ ./detener.sh
✔ backend detenido.
$ ./iniciar.sh --demo --sin-navegador
▶ Comprobando requisitos
✔ Python 3.13.18
✔ Tesseract 5.3.4 (idiomas: eng osd spa )
✔ Sin backend Spring Boot en el repositorio: no hace falta Java.
✔ Puerto 8783 libre
✔ Dependencias listas
▶ Iniciando ApuntIA en http://localhost:8783
✔ ApuntIA está lista
▶ Preparando la demostración (datos sintéticos, aparte de los reales)
▶ Analizando «Demostración: pizarrón» (3 fotos sintéticas)…
▶ Analizando «Demostración: cuaderno» (3 fotos sintéticas)…
✔ «Demostración: pizarrón»: completado
✔ «Demostración: cuaderno»: completado
Demostración lista. Entra en http://localhost:8783/front/cuenta.html con demo@example.com / «[contraseña omitida en esta transcripción]».
real	0m5.144s
user	0m2.514s
sys	0m0.341s
$ git status --short --ignored (lo creado por la instalación queda fuera de Git)
!! back/motori_magenes/.venv/
!! back/motori_magenes/datos/
!! fullstack/.demo/
!! fullstack/.estado/
!! fullstack/config/.env
```

Las URL con el puerto 8783 se deben a que la prueba usó `--puerto 8783` para no chocar con otra
instancia; con `./iniciar.sh` a secas es el 8000.

## Validación rápida en el mismo clon

`fullstack/scripts/validar.sh --rapido` en el clon limpio (con el commit `9ff37ce`): **todo en verde en
1 min 9 s** (pytest 368 passed, evaluación 12 passed, banco de evaluación 9/9 sin regresiones, sin
secretos, enlaces correctos, reglas de la interfaz y sintaxis de scripts, workflows y `compose.yaml`).

## Lo que esta evidencia NO cubre

- **Windows y macOS:** no se ha podido ejecutar (sin esos sistemas en el entorno de pruebas). Ver la
  matriz de [entrega.md](../entrega.md#2-matriz-de-compatibilidad).
- **Docker desde cero:** la prueba de entrega de Docker (`compose up` → humo → `down` → `up` →
  persistencia) pasó con imágenes construidas en este entorno, que necesita confiar en el certificado
  de su proxy; la construcción sin proxy la hace la CI de GitHub en cada pull request.
