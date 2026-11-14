# Pruebas y métricas de ApuntIA 3.0 (FULL-32)

Qué se prueba, con qué comando, **qué dio la última ejecución real** y qué falta. Fecha de las
cifras: 14/11/2026, PC Windows 11 Pro 10.0.26200 (Ryzen 7 5700X, 24 GB, RTX 3060 12 GB, controlador
621.14), Python 3.12, Node 26, rama `feature/FULL-32-cierre`. Nada de esta tabla es una estimación.

## 1. Niveles de validación

| Nivel | Linux / macOS / CI | Windows | GPU | Red |
|-------|--------------------|---------|-----|-----|
| Rápido: pytest backend y servidor IA (Ollama simulado), secretos, enlaces, tickets, catálogo, scripts | `fullstack/scripts/validar.sh` | `fullstack\scripts\validar.ps1` | no | no |
| Completo: + integración con backend real y Playwright | `validar.sh --completo` | `validar.ps1 -Completo` | no | no |
| Docker del cliente | `validar.sh --docker` | — (Docker Desktop) | no | para construir |
| Servidor IA real (salud, listo, medidor con corpus sintético) | — | `validar.ps1 -Gpu` (en la PC) | **sí** | no |
| Conexión entre redes (TLS, `/salud`, latencia) | — | `validar.ps1 -SoloRemoto -Remoto https://<nombre>` (en la laptop) | no | **sí** |

CI (`.github/workflows/ci.yml`) ejecuta los niveles sin GPU en Ubuntu y, en `windows-latest`, los
scripts de PowerShell, el servidor IA con Ollama simulado y, desde FULL-32, el respaldo, el PDF, la IA
remota, la investigación y la seguridad del backend. `pip-audit` revisa también `ia_servidor/requirements.txt`.
No descarga modelos ni usa credenciales reales.

## 2. Resultados de la última ejecución (14/11/2026, esta PC)

| Prueba | Resultado | Notas |
|--------|-----------|-------|
| Backend pytest | **471 OK**, 1 omitida, **6 fallan** | Las 6 son de calidad del OCR (tildes, regresión frente a la línea base) y fallan igual en el commit anterior: el Tesseract de esta PC no tiene `spa.traineddata` (`--list-langs`: eng, osd). En CI (Ubuntu con `tesseract-ocr-spa`) pasan. `/api/v2/listo` ya avisa de esto |
| Backend en Windows sin Tesseract (subconjunto de CI) | 220 OK, 1 omitida | `test_bomba_de_descompresion` usa `resource` (solo Unix): corre en CI Linux |
| Servidor IA pytest (Ollama simulado) | **129 OK** | |
| Interfaz: catálogo y reglas (`front/tests`) | 29/29 | |
| Integración v2 (Playwright + backend real) | 98/105 → tras los arreglos de FULL-32: los 3 que fallan dependen del OCR en español | `pdftotext` en Windows no escribía UTF-8 (4 casos) y un borrado temporal sin reintentos (1): corregidos |
| Secretos en el árbol y en todo el historial | limpio (513 rutas) | `buscar_secretos.py` |
| Dependencias vulnerables | 0 (pip-audit: backend + servidor IA) · 0 (npm audit) | |
| Puertos expuestos en la PC del servidor | solo 127.0.0.1:8100 (servidor IA) y 127.0.0.1:11434 (Ollama); sin reglas de firewall de ApuntIA ni de Ollama | `Get-NetTCPConnection` |
| Enlaces de la documentación | todos existen y todos los documentos son alcanzables | `comprobar_enlaces.py` |
| Servidor IA real, corpus sintético (11 casos) | 11/11 con CER 0; 2,3–7,0 s por caso; pico de VRAM 9 971 MB | `validar.ps1 -Gpu` |
| Foto real del pizarrón → servidor IA → editor → PDF | completado: 17 regiones → 35 bloques (23 de regiones divididas), 24 s (modelo cargado) / 70 s (en frío), PDF de 10 páginas | [generacion-pdf.md §7](generacion-pdf.md) |
| Backend matado a mitad de un análisis remoto | retoma el mismo trabajo, 1 sola inferencia en la GPU | [trabajos-remotos.md](trabajos-remotos.md) (BACK-37) |
| Vinculación, revocación y credencial cifrada (DPAPI) | probadas en la PC | [conexion-remota.md](conexion-remota.md) (FULL-31) |
| Servidor IA por Internet (Cloudflare Quick Tunnel, cliente en la misma PC) | `/salud` 200 en 521–562 ms; vinculación + diagnóstico 5/5; análisis real de una fórmula sintética con LaTeX exacto (21,7 s en frío) | [conexion-remota.md §4.3](conexion-remota.md) |
| `validar.ps1 -Remoto` sin `-Python` | el paso remoto pasa, pero las pruebas rápidas fallan si el intérprete por defecto no tiene pytest: en la laptop se usa `-SoloRemoto` | |

## 3. Matriz manual pendiente (necesita otra red o al dueño del proyecto)

| Caso | Estado | Qué hace falta |
|------|--------|----------------|
| Laptop en otra red → túnel HTTPS → PC de casa → análisis → editor → investigación → PDF | **pendiente** (el túnel ya se probó por Internet desde la propia PC) | la laptop fuera de la red de casa (basta el hotspot del celular); el Quick Tunnel no necesita cuenta. Pasos: [conexion-remota.md §6](conexion-remota.md); comprobar con `validar.ps1 -SoloRemoto -Remoto https://…` |
| Reconexión automática tras reiniciar la laptop; cambio de servidor; URL manual | pendiente en dos redes (probado en local) | ídem |
| Túnel caído, PC suspendida, DNS/TLS inválido, caída de Internet a mitad | pendiente en dos redes; cubiertos con simulación en `test_ia_remota.py` / `test_analisis_remoto.py` | ídem |
| `iniciar.bat` en una ruta con espacios y acentos, usuario sin administrador, segunda instancia | parcial: funciones probadas en `windows.pruebas.ps1`; sin prueba en otra cuenta de Windows | otra cuenta de usuario |
| Tres categorías de fotos reales (agrupamiento, vectorial, circuitos) | **pendiente**: solo hay una foto real con permiso (pizarrón de trigonometría) | fotos con permiso de su autor, guardadas en `fullstack/evaluacion/privado/` |
| Laptop real del profesor (otro equipo) | pendiente | el equipo |

Estos casos **no** se dan por cumplidos: FULL-32 no se cierra hasta tenerlos.

## 4. Métricas reales disponibles

| Métrica | Valor | Fuente |
|---------|-------|--------|
| CER del OCR local (corpus sintético, Linux) | 0,7 % | [evaluacion.md](evaluacion.md) |
| Servidor IA, foto real, por regiones manuales (cota superior) | 97 % de elementos; trampas 5/6 (8B) y 6/6 (4B) | [evaluacion-multimodal.md](evaluacion-multimodal.md) |
| Servidor IA, segmentación automática (`hueco` 0,2) | 95 % de elementos, 6/6 trampas | ídem §5.2 |
| Tiempo por página real | 24–70 s (con/sin modelo cargado) | §2 |
| VRAM máxima | 10,8 GB (8B) · 8,2 GB (4B), con ~2,9 GB del escritorio | [modelos-y-requisitos.md](modelos-y-requisitos.md) |
| Tamaño del PDF | 1,1 MB (foto real, con anexo de la foto) · 98 KB (ejemplo sintético de 4 páginas) | §2 |
| No determinismo | misma foto, dos pasadas: 0 y 4 bloques inciertos (temperature 0, seed 0) | §2 |

Con una sola foto real, ninguna tasa de error por tipo de contenido es generalizable.
