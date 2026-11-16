# Instalar ApuntIA en la laptop (cliente) (FULL-30)

La laptop del profesor ejecuta ApuntIA completa (interfaz, cuentas, historial, editor y PDF) con
las dependencias ligeras de siempre. **Nunca** instala Ollama, CUDA, PyTorch ni modelos: eso solo
ocurre en la PC del servidor IA ([instalacion-servidor-ia.md](instalacion-servidor-ia.md)).

## 1. Arrancar

| Forma | Qué pasa |
|-------|----------|
| Doble clic en `iniciar.bat` o `iniciar.bat` en una consola | Menú; la opción 1 inicia ApuntIA |
| `iniciar.bat -Modo app` | Inicia ApuntIA directamente, sin menú |
| `iniciar.bat -Puerto 8080`, `-Red`, `-SinNavegador`, `-Comprobar`… | Igual que siempre ([arranque.md](arranque.md)) |
| Sin consola (tarea programada, CI) o con `APUNTIA_SIN_MENU=1` | Arranque clásico, sin esperar al teclado |
| `docker compose -f fullstack/compose.yaml up --build -d` | Igual que siempre ([docker.md](docker.md)) |

Los parámetros, los códigos de salida 0–4 y el modo demo no cambian. Los modos de IA añaden el 5
(falta un paso manual) y el 6 (diagnóstico con fallos).

## 2. Conexión con el servidor IA

```bat
iniciar.bat -Modo configurar
```

Pide la URL pública del servidor IA (por ejemplo `https://ia.<dominio-del-proyecto>`) y la guarda
en `fullstack\config\.env` como `APUNTIA_IA_URL` (antes deja una copia en `.env.bak`).

- Solo acepta `https://<nombre>` o `http://127.0.0.1:<puerto>`. Rechaza usuario y contraseña,
  parámetros (`?token=…`) y otros esquemas. La URL no es un secreto: la autorización de la
  laptop llegará con la vinculación de FULL-31 y nunca irá en la URL.
- `-Url ""` (o dejarla vacía en el menú) vuelve al modo local.
- Al iniciar, ApuntIA comprueba en 3 s si el servidor responde y lo **informa**. Si no responde
  (PC apagada, túnel caído, sin Internet), arranca igual en modo local con Tesseract.
- Tras guardar la URL ofrece **vincular** el equipo: aparece un código que el administrador aprueba
  en la PC de casa ([conexion-remota.md](conexion-remota.md#2-vinculación-una-vez-por-laptop)).
- La integración del análisis remoto en el flujo de apuntes llega con la cola de BACK-37; hoy se
  prueba con `python -m herramientas.vincular_ia --probar foto.png`.

## 3. Diagnóstico

```bat
iniciar.bat -Modo diagnostico
```

Lista Windows, Python, disco y GPU (si hay), y el estado de la IA remota configurada (responde,
sin respuesta o HTTP con código), con la solución de cada fallo. No muestra secretos.

## 4. Errores frecuentes

| Síntoma | Solución |
|---------|----------|
| El menú aparece y quiero el arranque directo | `iniciar.bat -Modo app`, o define `APUNTIA_SIN_MENU=1` |
| «APUNTIA_IA_URL no es válida» | `iniciar.bat -Modo configurar` |
| «Servidor IA remoto sin respuesta» | Comprobar con quien administra la PC de casa; mientras tanto, modo local |
| `fullstack\config\.env` dañado | Restaurar `fullstack\config\.env.bak` o borrar el archivo (se regenera desde `.env.example`) |
| Puerto ocupado, Python o Tesseract ausentes | Ver [arranque.md](arranque.md#6-problemas-frecuentes) |
