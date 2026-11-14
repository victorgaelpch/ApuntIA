# Servidor IA y conexión de ApuntIA en Windows (FULL-30). Lo usan el menú de iniciar.bat y
# iniciar.bat -Modo …; también se puede llamar directamente:
#   powershell -ExecutionPolicy Bypass -File fullstack\scripts\ia.ps1 -Accion instalar [-AceptarDescarga] [-ConRespaldo]
#   … -Accion iniciar | detener | diagnostico
#   … -Accion configurar -Url https://ia.ejemplo.org   (en la laptop; -Url "" la quita)
# Códigos de salida: 0 bien · 1 requisito ausente · 2 dependencias · 3 puerto ocupado ·
#                    4 no arrancó · 5 falta un paso manual (Ollama o modelo) · 6 diagnóstico con fallos
# Guías: fullstack/docs/instalacion-servidor-ia.md y fullstack/docs/instalacion-clientes.md
param(
    [ValidateSet("instalar", "iniciar", "detener", "diagnostico", "configurar")]
    [Parameter(Mandatory = $true)][string]$Accion,
    [switch]$AceptarDescarga,   # descargar el modelo sin preguntar (automatizaciones)
    [switch]$ConRespaldo,       # descargar también el modelo de respaldo (4B)
    [switch]$SinInstalarOllama, # no ofrecer instalar Ollama con winget (solo guiar)
    [string]$Url = $null        # para -Accion configurar
)
$ErrorActionPreference = "Stop"
$UrlDada = $PSBoundParameters.ContainsKey("Url")
Import-Module (Join-Path $PSScriptRoot "ApuntIA.Comun.psm1") -Force -DisableNameChecking

$Raiz = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$IA = Join-Path $Raiz "ia_servidor"
$Venv = Join-Path $IA ".venv"
$PyVenv = Join-Path $Venv "Scripts\python.exe"
$Estado = Join-Path $Raiz "fullstack\.estado"
$EnvIA = Join-Path $IA ".env"
$EnvCliente = Join-Path $Raiz "fullstack\config\.env"
$OllamaApi = "http://127.0.0.1:11434"
$OLLAMA_MINIMA = @(0, 12, 7)        # Qwen3-VL lo exige (ollama.com/library/qwen3-vl)
$DRIVER_MINIMO = @(551, 61)         # docs.ollama.com/windows
$TAMANOS = @{ "qwen3-vl:8b-instruct" = "6,2 GB"; "qwen3-vl:4b-instruct" = "3,3 GB"; "qwen3-vl:8b" = "6,2 GB"; "qwen3-vl:4b" = "3,3 GB" }
New-Item -ItemType Directory -Force -Path $Estado | Out-Null

function Salir($codigo) { exit $codigo }
function Get-ConfigIA {
    $v = Read-ArchivoEnv $EnvIA
    $c = @{ Modelo = "qwen3-vl:8b-instruct"; Respaldo = "qwen3-vl:4b-instruct"; Puerto = 8100 }
    if ($v["IA_MODELO"]) { $c.Modelo = $v["IA_MODELO"] }
    if ($v.Contains("IA_MODELO_RESPALDO")) { $c.Respaldo = $v["IA_MODELO_RESPALDO"] }
    if ($v["IA_PUERTO"] -match '^\d+$') { $c.Puerto = [int]$v["IA_PUERTO"] }
    # Igual que el servidor: una variable de entorno ya definida manda sobre ia_servidor\.env.
    if ($env:IA_MODELO) { $c.Modelo = $env:IA_MODELO }
    if ($null -ne $env:IA_MODELO_RESPALDO) { $c.Respaldo = $env:IA_MODELO_RESPALDO }
    if ($env:IA_PUERTO -match '^\d+$') { $c.Puerto = [int]$env:IA_PUERTO }
    return $c
}
function Find-Ollama {
    $c = Get-Command ollama -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    $porDefecto = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path $porDefecto) { return $porDefecto }
    return $null
}
function Test-OllamaApi { return (Invoke-Json "$OllamaApi/api/version" 3).Estado -eq 200 }
function Get-ModelosInstalados {
    $r = Invoke-Json "$OllamaApi/api/tags" 5
    if ($r.Estado -ne 200 -or -not $r.Cuerpo) { return @() }
    return @($r.Cuerpo.models | ForEach-Object { $_.name })
}
function Preguntar([string]$Texto) {
    if (-not (Test-ConsolaInteractiva)) { return $false }
    $r = Read-Host "$Texto [s/N]"
    return $r -match '^(s|si|sí|y|yes)$'
}
function Start-OllamaSiHaceFalta([string]$Exe) {
    if (Test-OllamaApi) { return $true }
    if (-not $Exe) { return $false }
    Write-Paso "Iniciando Ollama (solo en 127.0.0.1:11434)"
    # OLLAMA_HOST explícito: aunque el usuario lo cambiara, este proceso escucha solo en loopback.
    $anterior = $env:OLLAMA_HOST; $env:OLLAMA_HOST = "127.0.0.1:11434"
    try {
        $p = Start-Process $Exe -ArgumentList "serve" -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $Estado "ollama.log") -RedirectStandardError (Join-Path $Estado "ollama.err.log")
    } finally { $env:OLLAMA_HOST = $anterior }
    Set-Content (Join-Path $Estado "ollama.pid") $p.Id
    $fin = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $fin -and -not $p.HasExited) { if (Test-OllamaApi) { return $true }; Start-Sleep -Milliseconds 500 }
    return (Test-OllamaApi)
}

# =============================================================================== diagnóstico
function Invoke-Diagnostico {
    $fallos = 0
    function Fila($ok, $que, $detalle, $solucion) {
        if ($ok -eq $true) { Write-Bien "$que — $detalle" }
        elseif ($ok -eq $null) { Write-Aviso "$que — $detalle" }
        else { Write-Error2 "$que — $detalle"; if ($solucion) { Write-Host "    Solución: $solucion" }; $script:fallosDiag++ }
    }
    $script:fallosDiag = 0
    Write-Paso "Diagnóstico de ApuntIA (sin datos sensibles)"
    $so = [Environment]::OSVersion.Version
    Fila ([Environment]::Is64BitOperatingSystem) "Windows" "$so, 64 bits: $([Environment]::Is64BitOperatingSystem)" "Ollama necesita Windows 10 22H2 o superior de 64 bits."
    $py = Find-Python
    Fila ([bool]$py) "Python ≥ 3.10" $(if ($py) { ($py -join " ") } else { "no encontrado" }) "Instala Python desde https://www.python.org/downloads/ (marca «Add python.exe to PATH»)."
    $mb = Get-MbLibres $Raiz
    Fila ($mb -ge 12288) "Espacio en disco" "$mb MB libres" "El servidor IA necesita ~12 GB (Ollama 4 GB + modelo 6,2 GB + entorno)."
    $gpus = Get-InfoGpu
    if ($gpus.Count -eq 0) { Fila $null "GPU NVIDIA" "no detectada (nvidia-smi no responde): en esta laptop es normal; en el servidor IA, el modelo iría por CPU y muy lento" $null }
    foreach ($g in $gpus) {
        $okDriver = Test-VersionMinima $g.Controlador $DRIVER_MINIMO
        Fila $okDriver "GPU" "$($g.Nombre), controlador $($g.Controlador), VRAM $($g.VramTotalMB) MB ($($g.VramLibreMB) MB libres)" "Actualiza el controlador NVIDIA a 551.61 o superior."
        if ($g.VramTotalMB -lt 8000) { Fila $null "VRAM" "menos de 8 GB: usa IA_MODELO=qwen3-vl:4b-instruct" $null }
    }
    $venvOk = (Test-Path $PyVenv)
    Fila $(if ($venvOk) { $true } else { $null }) "Entorno del servidor IA" $(if ($venvOk) { "ia_servidor\.venv" } else { "no instalado (solo hace falta en la PC del servidor IA)" }) $null
    $exe = Find-Ollama
    if ($exe) {
        $ver = (& $exe --version 2>$null | Out-String).Trim()
        Fila (Test-VersionMinima $ver $OLLAMA_MINIMA) "Ollama" "$ver" "Actualiza Ollama (0.12.7 o superior): winget upgrade --id Ollama.Ollama"
        $api = Test-OllamaApi
        Fila $(if ($api) { $true } else { $null }) "Ollama en 127.0.0.1:11434" $(if ($api) { "responde" } else { "apagado (iniciar.bat -Modo servidor-ia lo inicia)" }) $null
        if ($api) {
            $cfg = Get-ConfigIA
            $modelos = Get-ModelosInstalados
            Fila ($modelos -contains $cfg.Modelo) "Modelo $($cfg.Modelo)" $(if ($modelos -contains $cfg.Modelo) { "instalado" } else { "no instalado" }) "iniciar.bat -Modo instalar-ia (descarga $($TAMANOS[$cfg.Modelo]))."
        }
    } else {
        Fila $null "Ollama" "no instalado (solo hace falta en la PC del servidor IA)" $null
    }
    $cfg = Get-ConfigIA
    $s = Invoke-Json "http://127.0.0.1:$($cfg.Puerto)/salud" 2
    if ($s.Estado -eq 200 -and $s.Cuerpo.servicio -eq "apuntia-ia") {
        $l = Invoke-Json "http://127.0.0.1:$($cfg.Puerto)/listo" 10
        $listo = $l.Estado -eq 200
        Fila $listo "Servidor IA" "en marcha en 127.0.0.1:$($cfg.Puerto); listo: $listo" "Revisa los componentes con: curl http://127.0.0.1:$($cfg.Puerto)/listo"
    } else {
        Fila $null "Servidor IA" "no está en marcha en este equipo" $null
    }
    $remota = (Read-ArchivoEnv $EnvCliente)["APUNTIA_IA_URL"]
    if ($remota) {
        $motivo = Test-UrlServidorIA $remota
        if ($motivo) { Fila $false "IA remota configurada" $motivo "iniciar.bat -Modo configurar" }
        else {
            $r = Invoke-Json ($remota.TrimEnd("/") + "/salud") 5
            $ok = $r.Estado -eq 200 -and $r.Cuerpo.servicio -eq "apuntia-ia"
            $det = if ($ok) { "responde (api $($r.Cuerpo.api_version))" } elseif ($r.Estado -eq 0) { "sin respuesta (DNS, túnel, red o PC apagada)" } else { "HTTP $($r.Estado)" }
            Fila $(if ($ok) { $true } else { $false }) "IA remota $remota" $det "Comprueba que la PC del servidor esté encendida, con iniciar.bat -Modo servidor-ia, y el túnel activo. ApuntIA sigue funcionando en modo local."
        }
    } else { Fila $null "IA remota" "no configurada: ApuntIA funciona en modo local (Tesseract)" $null }
    return $script:fallosDiag
}

# =============================================================================== instalar (PC con GPU)
function Invoke-Instalar {
    Write-Paso "Instalación del servidor IA (solo en la PC con GPU; la laptop no lo necesita)"
    if (-not [Environment]::Is64BitOperatingSystem) { Write-Error2 "Hace falta Windows de 64 bits."; Salir 1 }
    $mb = Get-MbLibres $Raiz
    if ($mb -ge 0 -and $mb -lt 8192) { Write-Error2 "Solo hay $mb MB libres: hacen falta al menos 8 GB (recomendado 12 GB)."; Salir 1 }
    if ($mb -ge 0 -and $mb -lt 12288) { Write-Aviso "Hay $mb MB libres: justo. Se recomiendan 12 GB." }
    $gpus = Get-InfoGpu
    if ($gpus.Count -eq 0) { Write-Aviso "No se detecta GPU NVIDIA: el modelo funcionará por CPU y será muy lento. Considera IA_MODELO=qwen3-vl:4b-instruct." }
    foreach ($g in $gpus) {
        Write-Bien "GPU $($g.Nombre) · VRAM $($g.VramTotalMB) MB · controlador $($g.Controlador)"
        if (-not (Test-VersionMinima $g.Controlador $DRIVER_MINIMO)) { Write-Aviso "El controlador es anterior a 551.61: actualízalo desde nvidia.com antes de usar la GPU." }
    }

    # ---- entorno de Python del servidor IA (reanudable: solo reinstala si cambian los requisitos)
    $py = Find-Python
    if (-not $py) { Write-Error2 "Hace falta Python 3.10 o superior: https://www.python.org/downloads/"; Salir 1 }
    if (-not (Test-Path $PyVenv)) {
        Write-Paso "Creando el entorno ia_servidor\.venv"
        & $py[0] @($py[1..9] | Where-Object { $_ }) -m venv $Venv
        if ($LASTEXITCODE -ne 0) { Write-Error2 "No se pudo crear el entorno virtual."; Salir 2 }
    }
    $req = Join-Path $IA "requirements.txt"; $cons = Join-Path $Raiz "back\motori_magenes\constraints.txt"
    $texto = (Get-Content $req, $cons -Raw) -join ""
    $huella = (Get-FileHash -Algorithm SHA256 -InputStream ([IO.MemoryStream]::new([Text.Encoding]::UTF8.GetBytes($texto)))).Hash
    $marca = Join-Path $Estado "requisitos-ia.sha256"
    if (-not (Test-Path $marca) -or (Get-Content $marca) -ne $huella) {
        Write-Paso "Instalando dependencias del servidor IA (sin PyTorch ni CUDA: lo hace Ollama)"
        & $PyVenv -m pip install --disable-pip-version-check -q -r $req -c $cons
        if ($LASTEXITCODE -ne 0) { Write-Error2 "Falló pip. Revisa la conexión (o el proxy) y vuelve a ejecutar: se reanuda."; Salir 2 }
        Set-Content $marca $huella
    }
    Write-Bien "Dependencias del servidor IA listas"
    if (-not (Test-Path $EnvIA)) { Copy-Item (Join-Path $IA ".env.example") $EnvIA; Write-Bien "Creada la configuración ia_servidor\.env (sin secretos)." }
    $cfg = Get-ConfigIA

    # ---- Ollama: nunca se descarga un instalador de una fuente no oficial
    $exe = Find-Ollama
    if (-not $exe) {
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if ($winget -and -not $SinInstalarOllama -and (Preguntar "Ollama no está instalado. ¿Instalarlo con winget (paquete oficial Ollama.Ollama, no requiere administrador)?")) {
            winget install --id Ollama.Ollama --exact --source winget
            $exe = Find-Ollama
        }
        if (-not $exe) {
            Write-Aviso "Falta Ollama. Instálalo con UNA de estas vías oficiales y vuelve a ejecutar este paso:"
            Write-Host "    1) winget install --id Ollama.Ollama --exact --source winget"
            Write-Host "    2) Descarga OllamaSetup.exe de https://ollama.com/download/windows"
            Write-Host "    No necesita administrador. Después: iniciar.bat -Modo instalar-ia"
            Salir 5
        }
    }
    $ver = (& $exe --version 2>$null | Out-String).Trim()
    if (-not (Test-VersionMinima $ver $OLLAMA_MINIMA)) { Write-Error2 "Ollama $ver es antiguo: Qwen3-VL necesita 0.12.7+. Actualiza: winget upgrade --id Ollama.Ollama"; Salir 1 }
    Write-Bien "Ollama: $ver"
    if (-not (Start-OllamaSiHaceFalta $exe)) { Write-Error2 "Ollama no responde en 127.0.0.1:11434. Ábrelo desde el menú Inicio y reintenta."; Salir 4 }

    # ---- modelos: solo si faltan; ollama pull muestra el progreso y reanuda descargas cortadas
    $modelos = @($cfg.Modelo)
    if ($ConRespaldo -and $cfg.Respaldo) { $modelos += $cfg.Respaldo }
    foreach ($m in $modelos) {
        if ((Get-ModelosInstalados) -contains $m) { Write-Bien "Modelo $m ya instalado: no se descarga de nuevo."; continue }
        $tam = if ($TAMANOS[$m]) { $TAMANOS[$m] } else { "tamaño desconocido" }
        if (-not $AceptarDescarga -and -not (Preguntar "Falta el modelo $m ($tam). ¿Descargarlo ahora?")) {
            Write-Aviso "Modelo $m sin descargar. Hazlo cuando quieras con: ollama pull $m   (o iniciar.bat -Modo instalar-ia)"
            Salir 5
        }
        Write-Paso "Descargando $m ($tam). Si se corta, vuelve a ejecutar este paso: continúa donde se quedó."
        & $exe pull $m
        if ($LASTEXITCODE -ne 0) { Write-Error2 "La descarga de $m falló (red o disco). Vuelve a ejecutarlo para reanudar."; Salir 2 }
        Write-Bien "Modelo $m instalado"
    }
    Write-Bien "Servidor IA instalado. Inícialo con: iniciar.bat -Modo servidor-ia"
    Salir 0
}

# =============================================================================== iniciar / detener
function Invoke-Iniciar {
    if (-not (Test-Path $PyVenv)) { Write-Error2 "El servidor IA no está instalado en este equipo. Ejecuta: iniciar.bat -Modo instalar-ia"; Salir 2 }
    if (-not (Test-Path $EnvIA)) { Copy-Item (Join-Path $IA ".env.example") $EnvIA }
    $cfg = Get-ConfigIA
    $s = Invoke-Json "http://127.0.0.1:$($cfg.Puerto)/salud" 2
    if ($s.Estado -eq 200 -and $s.Cuerpo.servicio -eq "apuntia-ia") { Write-Bien "El servidor IA ya está en marcha en 127.0.0.1:$($cfg.Puerto)"; Salir 0 }
    if (Get-NetTCPConnection -LocalPort $cfg.Puerto -State Listen -ErrorAction SilentlyContinue) {
        Write-Error2 "El puerto $($cfg.Puerto) está ocupado por otro programa. Cambia IA_PUERTO en ia_servidor\.env."; Salir 3
    }
    $exe = Find-Ollama
    if (-not (Start-OllamaSiHaceFalta $exe)) { Write-Aviso "Ollama no está disponible: el servidor arrancará, pero /listo dirá que no está listo." }
    Write-Paso "Iniciando el servidor IA en 127.0.0.1:$($cfg.Puerto)"
    Import-ArchivoEnv $EnvIA
    $p = Start-Process $PyVenv -ArgumentList @("-m", "ia_servidor") -WorkingDirectory $Raiz -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $Estado "ia-servidor.log") -RedirectStandardError (Join-Path $Estado "ia-servidor.err.log")
    Set-Content (Join-Path $Estado "ia-servidor.pid") $p.Id
    $fin = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $fin -and -not $p.HasExited) {
        if ((Invoke-Json "http://127.0.0.1:$($cfg.Puerto)/salud" 2).Estado -eq 200) { break }
        Start-Sleep -Milliseconds 500
    }
    if ((Invoke-Json "http://127.0.0.1:$($cfg.Puerto)/salud" 2).Estado -ne 200) {
        Write-Error2 "El servidor IA no arrancó. Últimas líneas del registro:"
        Get-Content (Join-Path $Estado "ia-servidor.err.log") -Tail 15 -ErrorAction SilentlyContinue
        Salir 4
    }
    $l = Invoke-Json "http://127.0.0.1:$($cfg.Puerto)/listo" 15
    if ($l.Estado -eq 200) { Write-Bien "Servidor IA listo (modelo $($cfg.Modelo))." }
    else {
        Write-Aviso "El servidor IA está en marcha pero NO listo:"
        if ($l.Cuerpo) { $l.Cuerpo.componentes.PSObject.Properties | Where-Object { $_.Value.ok -eq $false } | ForEach-Object { Write-Host "    $($_.Name): $($_.Value.detalle)" } }
    }
    Write-Host "  Registro: fullstack\.estado\ia-servidor.err.log · Detener: detener.bat"
    Salir 0
}

function Invoke-Detener {
    $algo = $false
    $algo = (Stop-ProcesoPropio (Join-Path $Estado "ia-servidor.pid") "ia_servidor" "Servidor IA") -or $algo
    # Ollama solo si lo arrancó este script (si ya estaba abierto desde el menú Inicio, se respeta).
    $algo = (Stop-ProcesoPropio (Join-Path $Estado "ollama.pid") "ollama(\.exe)?`"?\s+serve" "Ollama") -or $algo
    if (-not $algo) { Write-Bien "El servidor IA no estaba en marcha." }
    Salir 0
}

# =============================================================================== configurar (laptop)
function Invoke-Configurar {
    if (-not (Test-Path $EnvCliente)) { Copy-Item (Join-Path $Raiz "fullstack\config\.env.example") $EnvCliente }
    if ($UrlDada -and -not $Url) {
        Set-ValorEnv $EnvCliente "APUNTIA_IA_URL" ""; Write-Bien "IA remota desactivada: ApuntIA usará el modo local."; Salir 0
    }
    if (-not $UrlDada) {
        if (-not (Test-ConsolaInteractiva)) { Write-Error2 "Indica la URL: -Url https://… (o -Url `"`" para quitarla)."; Salir 1 }
        $actual = (Read-ArchivoEnv $EnvCliente)["APUNTIA_IA_URL"]
        Write-Host "URL actual: $(if ($actual) { $actual } else { '(ninguna: modo local)' })"
        $Url = Read-Host "Nueva URL del servidor IA (vacío = modo local)"
        if (-not $Url) { Set-ValorEnv $EnvCliente "APUNTIA_IA_URL" ""; Write-Bien "Modo local."; Salir 0 }
    }
    $motivo = Test-UrlServidorIA $Url
    if ($motivo) { Write-Error2 $motivo; Salir 1 }
    Set-ValorEnv $EnvCliente "APUNTIA_IA_URL" $Url.TrimEnd("/")
    Write-Bien "Guardado en fullstack\config\.env (copia anterior en .env.bak). La URL no es un secreto."
    $r = Invoke-Json ($Url.TrimEnd("/") + "/salud") 5
    if ($r.Estado -eq 200 -and $r.Cuerpo.servicio -eq "apuntia-ia") { Write-Bien "El servidor responde (api $($r.Cuerpo.api_version))." }
    else { Write-Aviso "El servidor no responde ahora. No pasa nada: ApuntIA seguirá en modo local y se puede reintentar." }
    Write-Aviso "La vinculación autorizada de este equipo (FULL-31) todavía no está implementada: aún no se envían fotos al servidor."
    Salir 0
}

switch ($Accion) {
    "diagnostico" { $f = Invoke-Diagnostico; if ($f -gt 0) { Write-Error2 "$f comprobación(es) con fallos."; Salir 6 } else { Write-Bien "Sin fallos."; Salir 0 } }
    "instalar" { Invoke-Instalar }
    "iniciar" { Invoke-Iniciar }
    "detener" { Invoke-Detener }
    "configurar" { Invoke-Configurar }
}
