# Validación de ApuntIA en Windows con un solo comando (FULL-32). Equivalente de validar.sh.
#
#   powershell -ExecutionPolicy Bypass -File fullstack\scripts\validar.ps1 [-Completo] [-Gpu] [-Remoto URL] [-Python RUTA]
#
#   (sin opciones)  rápido, sin GPU ni red: pytest del backend y del servidor IA (Ollama simulado),
#                   secretos, enlaces, tickets, catálogo de la interfaz y funciones de los scripts.
#   -Completo       además: integración con el backend real y Playwright (v1, v2, accesibilidad).
#   -Gpu            además: servidor IA REAL en esta PC (127.0.0.1:8100): salud, listo y el medidor
#                   con el corpus sintético (tiempo y pico de VRAM por caso). Solo en la PC del servidor.
#   -Remoto URL     además: desde la laptop, comprueba el servidor IA por su URL pública (HTTPS del
#                   túnel o de Tailscale): TLS, /salud y latencia. La prueba entre dos redes es esta.
#   -SoloRemoto     con -Remoto: solo esa comprobación (para la laptop, que no tiene pytest ni Node).
#   -Python RUTA    intérprete con las dependencias de desarrollo (por defecto: $env:PYTHON, el .venv
#                   del backend o el Python del sistema).
#
# No descarga modelos ni usa credenciales. Sale con 1 si falla algún paso (y sigue con los demás).
param(
    [switch]$Completo,
    [switch]$Gpu,
    [string]$Remoto = "",
    [switch]$SoloRemoto,
    [string]$Python = ""
)
if ($SoloRemoto -and -not $Remoto) { Write-Host "-SoloRemoto necesita -Remoto URL" -ForegroundColor Red; exit 2 }
$ErrorActionPreference = "Continue"
$Raiz = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Import-Module (Join-Path $PSScriptRoot "ApuntIA.Comun.psm1") -Force -DisableNameChecking
Set-Location $Raiz
$env:PYTHONUTF8 = "1"

# ------------------------------------------------------------------ intérprete, Node y Tesseract
if (-not $Python) { $Python = $env:PYTHON }
if (-not $Python) {
    $venv = Join-Path $Raiz "back\motori_magenes\.venv\Scripts\python.exe"
    if (Test-Path $venv) { $Python = $venv } else { $p = Find-Python; if ($p) { $Python = $p[0] } }
}
if (-not $Python -and -not $SoloRemoto) { Write-Error2 "No hay Python 3.10+ (usa -Python RUTA)."; exit 2 }
$Node = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $Node -and (Test-Path "C:\Program Files\nodejs\node.exe")) { $Node = "C:\Program Files\nodejs\node.exe" }
$Tess = "C:\Program Files\Tesseract-OCR"
if (-not (Get-Command tesseract -ErrorAction SilentlyContinue) -and (Test-Path "$Tess\tesseract.exe")) {
    $env:PATH = "$Tess;$env:PATH"
    if (-not $env:TESSERACT_CMD) { $env:TESSERACT_CMD = "$Tess\tesseract.exe" }
}

$script:resumen = New-Object System.Collections.Generic.List[string]
$script:fallos = 0
function Paso([string]$Nombre, [scriptblock]$Accion) {
    Write-Paso $Nombre
    $inicio = Get-Date
    $global:LASTEXITCODE = 0
    $ok = $true
    try { & $Accion; if ($LASTEXITCODE -ne 0) { $ok = $false } } catch { Write-Error2 $_; $ok = $false }
    $s = [int]((Get-Date) - $inicio).TotalSeconds
    if ($ok) { $script:resumen.Add("OK  $Nombre ($s s)") } else { $script:resumen.Add("MAL $Nombre ($s s)"); $script:fallos++ }
}
function Nota([string]$Texto) { Write-Aviso $Texto; $script:resumen.Add("--  $Texto") }

# ------------------------------------------------------------------ rápido
if (-not $SoloRemoto) {
Paso "Backend: pytest" { Push-Location back\motori_magenes; try { & $Python -m pytest -q -p no:cacheprovider } finally { Pop-Location } }
Paso "Servidor IA: pytest con Ollama simulado" { & $Python -m pytest -q -p no:cacheprovider ia_servidor\tests }
Paso "Seguridad: sin secretos en el árbol ni en el historial" { & $Python fullstack\scripts\buscar_secretos.py }
Paso "Documentación: enlaces y documentos huérfanos" { & $Python fullstack\scripts\comprobar_enlaces.py }
Paso "Tickets: comprobador y sincronizador" {
    & $Python -m unittest discover -s fullstack\tests\docs
    if ($LASTEXITCODE -eq 0) { & $Python -m unittest discover -s fullstack\tests\tickets }
}
Paso "Scripts de Windows: funciones y sintaxis" { powershell -NoProfile -ExecutionPolicy Bypass -File fullstack\tests\scripts\windows.pruebas.ps1 }
if ($Node) {
    Paso "Interfaz: catálogo de mensajes y reglas" { & $Node --test front/tests/catalogo.test.js }
} else { Nota "Node no está instalado: se omite el catálogo de la interfaz" }

# Tesseract sin español funciona, pero pierde tildes: las pruebas de calidad del OCR fallan.
if (Get-Command tesseract -ErrorAction SilentlyContinue) {
    $idiomas = (& tesseract --list-langs 2>$null | Select-Object -Skip 1) -join " "
    if ($idiomas -notmatch "\bspa\b") {
        Nota "Tesseract sin «spa» ($idiomas): copia spa.traineddata en tessdata; si no, fallan las pruebas de calidad del OCR"
    }
} else { Nota "Tesseract no está instalado: se omiten las pruebas que lo necesitan" }
}

# ------------------------------------------------------------------ completo
if ($Completo) {
    if ($Node) {
        $env:PYTHON = $Python
        Paso "Integración con el backend real y Playwright" { & $Node --test --test-concurrency=1 "fullstack/tests/integracion/*.test.js" }
    } else { Nota "Node no está instalado: se omite la integración" }
}

# ------------------------------------------------------------------ GPU real (PC del servidor)
if ($Gpu) {
    Paso "Servidor IA real: /salud y /listo en 127.0.0.1:8100" {
        $s = Invoke-Json "http://127.0.0.1:8100/salud" 5
        $l = Invoke-Json "http://127.0.0.1:8100/listo" 10
        Write-Host "  /salud $($s.Estado) · /listo $($l.Estado)"
        if ($s.Estado -ne 200 -or $l.Estado -ne 200) { throw "El servidor IA no está listo: iniciar.bat -Modo servidor-ia" }
    }
    if (Test-Path (Join-Path $Raiz "ia_servidor\.datos")) {
        # El corpus sintético se dibuja con las dependencias del backend: se usa el intérprete de desarrollo.
        Paso "Servidor IA real: medidor con el corpus sintético (usa la GPU)" {
            # El medidor imprime el tiempo y el pico de VRAM de cada caso (lo informa el servidor IA).
            & $Python -m ia_servidor.medir
        }
    } else { Nota "No existe ia_servidor\.datos: el medidor solo corre en la PC del servidor IA ya instalado" }
}

# ------------------------------------------------------------------ conexión remota (laptop)
if ($Remoto) {
    Paso "Conexión remota: $Remoto" {
        $motivo = Test-UrlServidorIA $Remoto
        if ($motivo) { throw $motivo }
        $base = $Remoto.TrimEnd("/")
        $t = [Diagnostics.Stopwatch]::StartNew()
        $s = Invoke-Json "$base/salud" 15
        $t.Stop()
        Write-Host "  /salud -> HTTP $($s.Estado) en $($t.ElapsedMilliseconds) ms"
        if ($s.Estado -ne 200 -or $s.Cuerpo.servicio -ne "apuntia-ia") {
            throw "No responde el servidor IA (¿PC apagada, túnel caído o DNS/TLS?). Ver fullstack\docs\recuperacion-conexion.md"
        }
        $l = Invoke-Json "$base/listo" 15
        Write-Host "  /listo -> HTTP $($l.Estado) (sin credencial solo dice si está listo; nada del equipo)"
    }
}

Write-Host ""
Write-Host "Resumen" -ForegroundColor White
$script:resumen | ForEach-Object { Write-Host "  $_" }
if ($script:fallos -eq 0) { Write-Bien "Todo correcto."; exit 0 }
Write-Error2 "$($script:fallos) paso(s) fallaron."
exit 1
