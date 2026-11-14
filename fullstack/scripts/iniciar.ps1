# Arranca ApuntIA sin Docker en Windows (FULL-11). Equivale a iniciar.sh.
# Uso: iniciar.bat [-Puerto N] [-Red] [-SinNavegador] [-SinVenv] [-Reinstalar] [-Comprobar]
# Códigos de salida: 0 bien · 1 requisito ausente · 2 dependencias · 3 puerto ocupado · 4 no arrancó
param(
    [int]$Puerto = 0,
    [switch]$Red,
    [switch]$SinNavegador,
    [switch]$SinVenv,
    [switch]$Reinstalar,
    [switch]$Comprobar
)
$ErrorActionPreference = "Stop"
$Raiz = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Backend = Join-Path $Raiz "back\motori_magenes"
$Estado = Join-Path $Raiz "fullstack\.estado"
$Config = Join-Path $Raiz "fullstack\config\.env"

function Azul($t) { Write-Host "> $t" -ForegroundColor Cyan }
function Bien($t) { Write-Host "OK $t" -ForegroundColor Green }
function Aviso($t) { Write-Host "! $t" -ForegroundColor Yellow }
function Fallo($t, $codigo) { Write-Host "X $t" -ForegroundColor Red; exit $codigo }

# ------------------------------------------------------------------ configuración
New-Item -ItemType Directory -Force -Path $Estado | Out-Null
if (-not (Test-Path $Config)) {
    Copy-Item (Join-Path $Raiz "fullstack\config\.env.example") $Config
    Bien "Creada la configuración local fullstack\config\.env (puedes editarla)."
}
foreach ($linea in Get-Content $Config) {
    if ($linea -match '^\s*([A-Z_][A-Z0-9_]*)=(.*)$') {
        if (-not [Environment]::GetEnvironmentVariable($Matches[1])) { [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim()) }
    }
}
if ($Puerto -eq 0) { $Puerto = if ($env:APUNTIA_PUERTO) { [int]$env:APUNTIA_PUERTO } else { 8000 } }
if ($Puerto -lt 1024 -or $Puerto -gt 65535) { Fallo "Puerto no válido: $Puerto (usa 1024-65535)." 1 }
$HostEscucha = if ($Red) { "0.0.0.0" } else { "127.0.0.1" }
$Url = "http://localhost:$Puerto"

# ------------------------------------------------------------------ requisitos
Azul "Comprobando requisitos"
$Py = $null
foreach ($c in @("py -3", "python", "python3")) {
    $partes = $c.Split(" ")
    try {
        & $partes[0] @($partes[1..9] | Where-Object { $_ }) -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $Py = $partes; break }
    } catch { }
}
if (-not $Py) { Fallo "Hace falta Python 3.10 o superior: https://www.python.org/downloads/ (marca «Add python.exe to PATH»)." 1 }
function Python { & $Py[0] @($Py[1..9] | Where-Object { $_ }) @args }
Bien ("Python " + (Python -c "import platform; print(platform.python_version())"))

if (Get-Command tesseract -ErrorAction SilentlyContinue) {
    $idiomas = (tesseract --list-langs 2>$null | Select-Object -Skip 1) -join " "
    Bien "Tesseract (idiomas: $idiomas)"
    if ($idiomas -notmatch '\bspa\b') { Aviso "Falta el idioma español de Tesseract: el texto en español se leerá peor." }
} else {
    Aviso "Tesseract no está instalado: «Mejorar una foto» funciona, pero los apuntes no se podrán analizar."
    Aviso "Instálalo desde https://github.com/UB-Mannheim/tesseract/wiki (incluye el idioma Spanish) o define TESSERACT_CMD."
}

# Backend Spring Boot: el repositorio NO tiene uno (ver fullstack/docs/arranque.md); si se añade, se detecta.
$Spring = Get-ChildItem (Join-Path $Raiz "back") -Directory | Where-Object {
    $_.FullName -ne $Backend -and ((Test-Path (Join-Path $_.FullName "pom.xml")) -or (Test-Path (Join-Path $_.FullName "build.gradle")))
} | Select-Object -First 1
if ($Spring) {
    if (-not (Get-Command java -ErrorAction SilentlyContinue)) { Fallo "Hay un backend Spring Boot en $($Spring.Name) pero falta Java 17 o superior." 1 }
    Bien "Spring Boot detectado en back\$($Spring.Name)"
} else { Bien "Sin backend Spring Boot en el repositorio: no hace falta Java." }

try {
    $s = Invoke-RestMethod "$Url/salud" -TimeoutSec 2
    if ($s.estado -eq "ok") { Bien "ApuntIA ya está en marcha en $Url"; Write-Host "  Ábrela en: $Url/inicio"; exit 0 }
} catch { }
$ocupado = Get-NetTCPConnection -LocalPort $Puerto -State Listen -ErrorAction SilentlyContinue
if ($ocupado) { Fallo "El puerto $Puerto está ocupado por otro programa. Usa otro: iniciar.bat -Puerto 8080" 3 }
Bien "Puerto $Puerto libre"
if ($Comprobar) { Bien "Comprobación terminada: se puede arrancar."; exit 0 }

# ------------------------------------------------------------------ entorno de Python
Set-Location $Backend
if (-not $SinVenv) {
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        Azul "Creando el entorno virtual back\motori_magenes\.venv"
        Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { Fallo "No se pudo crear el entorno virtual." 2 }
    }
    $Py = @((Join-Path $Backend ".venv\Scripts\python.exe"))
}
$huella = (Get-FileHash -Algorithm SHA256 -InputStream ([IO.MemoryStream]::new([Text.Encoding]::UTF8.GetBytes((Get-Content requirements.txt, constraints.txt -Raw) -join "")))).Hash
$marca = Join-Path $Estado ("requisitos-" + $(if ($SinVenv) { "sistema" } else { "venv" }) + ".sha256")
if ($Reinstalar -or -not (Test-Path $marca) -or (Get-Content $marca) -ne $huella) {
    Azul "Instalando dependencias de Python (puede tardar unos minutos la primera vez)"
    Python -m pip install --disable-pip-version-check -q -r requirements.txt -c constraints.txt
    if ($LASTEXITCODE -ne 0) { Fallo "Falló la instalación de dependencias. Revisa la conexión y usa -Reinstalar." 2 }
    Set-Content $marca $huella
}
Python -c "import fastapi, uvicorn, cv2, reportlab" 2>$null
if ($LASTEXITCODE -ne 0) { Fallo "Faltan módulos (fastapi, uvicorn, opencv, reportlab). Usa -Reinstalar." 2 }
Bien "Dependencias listas"

# ------------------------------------------------------------------ arranque
if ($Spring) {
    Azul "Iniciando Spring Boot"
    $wrapper = if (Test-Path (Join-Path $Spring.FullName "mvnw.cmd")) { "mvnw.cmd spring-boot:run" } elseif (Test-Path (Join-Path $Spring.FullName "gradlew.bat")) { "gradlew.bat bootRun" } else { $null }
    if (-not $wrapper) { Fallo "Spring Boot sin Maven/Gradle Wrapper (mvnw.cmd o gradlew.bat)." 1 }
    $p = Start-Process cmd -ArgumentList "/c $wrapper" -WorkingDirectory $Spring.FullName -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $Estado "spring.log") -RedirectStandardError (Join-Path $Estado "spring.err.log")
    Set-Content (Join-Path $Estado "spring.pid") $p.Id
}

Azul "Iniciando ApuntIA en $Url"
$env:APUNTIA_PUERTO = "$Puerto"
$argumentos = @($Py[1..9] | Where-Object { $_ }) + @("-m", "uvicorn", "main:app", "--host", $HostEscucha, "--port", "$Puerto")
$p = Start-Process $Py[0] -ArgumentList $argumentos -WorkingDirectory $Backend -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $Estado "backend.log") -RedirectStandardError (Join-Path $Estado "backend.err.log")
Set-Content (Join-Path $Estado "backend.pid") $p.Id

$fin = (Get-Date).AddSeconds(60); $listo = $false
while ((Get-Date) -lt $fin -and -not $p.HasExited) {
    try { if ((Invoke-RestMethod "$Url/salud" -TimeoutSec 2).estado -eq "ok") { $listo = $true; break } } catch { Start-Sleep -Milliseconds 500 }
}
if (-not $listo) {
    Write-Host "X ApuntIA no arrancó. Últimas líneas del registro:" -ForegroundColor Red
    Get-Content (Join-Path $Estado "backend.err.log") -Tail 20 -ErrorAction SilentlyContinue
    exit 4
}
Bien "ApuntIA está lista"
Write-Host ""
Write-Host "  Mejorar una foto (sin cuenta):  $Url/inicio"
Write-Host "  Apuntes con cuenta:             $Url/front/apuntes.html"
Write-Host "  Registro del servidor:          fullstack\.estado\backend.err.log"
Write-Host "  Para detenerla:                 detener.bat"
if (-not $SinNavegador) { Start-Process "$Url/inicio" }
