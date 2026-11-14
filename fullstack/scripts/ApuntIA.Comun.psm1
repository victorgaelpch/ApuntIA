# Funciones comunes de los scripts de Windows de ApuntIA (FULL-30).
# Sin efectos al importarlo: solo define funciones. Pruebas: fullstack/tests/scripts/windows.pruebas.ps1

function Write-Paso($t)  { Write-Host "> $t" -ForegroundColor Cyan }
function Write-Bien($t)  { Write-Host "OK $t" -ForegroundColor Green }
function Write-Aviso($t) { Write-Host "! $t" -ForegroundColor Yellow }
function Write-Error2($t) { Write-Host "X $t" -ForegroundColor Red }

function Get-VersionTupla([string]$Texto) {
    # "ollama version is 0.12.10" → @(0,12,10)
    $m = [regex]::Matches($Texto, '\d+') | Select-Object -First 3 | ForEach-Object { [int]$_.Value }
    if (-not $m) { return @(0) }
    return @($m)
}

function Test-VersionMinima([string]$Actual, [int[]]$Minima) {
    $a = Get-VersionTupla $Actual
    for ($i = 0; $i -lt $Minima.Count; $i++) {
        $x = if ($i -lt $a.Count) { $a[$i] } else { 0 }
        if ($x -gt $Minima[$i]) { return $true }
        if ($x -lt $Minima[$i]) { return $false }
    }
    return $true
}

function Read-ArchivoEnv([string]$Ruta) {
    # KEY=VALOR por línea; ignora comentarios y líneas mal formadas. Nunca evalúa nada.
    $valores = [ordered]@{}
    if (-not (Test-Path -LiteralPath $Ruta)) { return $valores }
    foreach ($linea in Get-Content -LiteralPath $Ruta -Encoding UTF8) {
        if ($linea -match '^\s*([A-Z_][A-Z0-9_]*)=(.*)$') { $valores[$Matches[1]] = $Matches[2].Trim() }
    }
    return $valores
}

function Import-ArchivoEnv([string]$Ruta) {
    # Carga en el entorno del proceso las variables que no estén ya definidas (el entorno manda).
    $valores = Read-ArchivoEnv $Ruta
    foreach ($k in $valores.Keys) {
        if (-not [Environment]::GetEnvironmentVariable($k)) { [Environment]::SetEnvironmentVariable($k, $valores[$k]) }
    }
}

function Set-ValorEnv([string]$Ruta, [string]$Clave, [string]$Valor) {
    # Cambia o añade KEY=VALOR sin tocar el resto. Antes guarda una copia .bak (recuperación manual).
    if ($Clave -notmatch '^[A-Z_][A-Z0-9_]*$') { throw "Clave no válida: $Clave" }
    if ($Valor -match "[\r\n]") { throw "El valor no puede tener saltos de línea" }
    $lineas = @()
    if (Test-Path -LiteralPath $Ruta) {
        Copy-Item -LiteralPath $Ruta -Destination "$Ruta.bak" -Force
        $lineas = @(Get-Content -LiteralPath $Ruta -Encoding UTF8)
    }
    $hecho = $false
    $nuevas = foreach ($l in $lineas) {
        if (-not $hecho -and $l -match "^\s*#?\s*$([regex]::Escape($Clave))=") { "$Clave=$Valor"; $hecho = $true } else { $l }
    }
    if (-not $hecho) { $nuevas = @($nuevas) + "$Clave=$Valor" }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllLines($Ruta, [string[]]@($nuevas), $utf8)
}

function Test-UrlServidorIA([string]$Url) {
    # Devuelve $null si la URL es aceptable o el motivo si no. Solo HTTPS con nombre de equipo, o
    # http://127.0.0.1/localhost (túnel o pruebas locales). Sin usuario, contraseña ni parámetros:
    # la URL es pública; la autorización llega con la vinculación (FULL-31), nunca en la URL.
    if (-not $Url) { return "La URL está vacía." }
    try { $u = [Uri]$Url } catch { return "No es una URL válida." }
    if (-not $u.IsAbsoluteUri) { return "No es una URL absoluta." }
    if ($u.UserInfo) { return "La URL no puede llevar usuario ni contraseña." }
    if ($u.Query -or $u.Fragment) { return "La URL no puede llevar parámetros (?…) ni fragmentos (#…)." }
    $local = $u.Host -in @("127.0.0.1", "localhost", "[::1]", "::1")
    if ($u.Scheme -eq "https" -and $u.Host -and $u.Host -match '[a-zA-Z]') { return $null }
    if ($u.Scheme -eq "http" -and $local) { return $null }
    return "Usa https://<nombre-del-servidor> (o http://127.0.0.1:<puerto> en el mismo equipo)."
}

function Test-ConsolaInteractiva {
    # El menú solo aparece si hay una persona delante: nunca en CI, con la entrada redirigida o
    # con APUNTIA_SIN_MENU=1 (automatizaciones).
    if ($env:CI -or $env:APUNTIA_SIN_MENU) { return $false }
    try { return [Environment]::UserInteractive -and -not [Console]::IsInputRedirected } catch { return $false }
}

function ConvertFrom-NvidiaSmi([string]$Texto) {
    # Salida de: nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader,nounits
    $gpus = @()
    foreach ($linea in ($Texto -split "`r?`n")) {
        $p = $linea.Split(",") | ForEach-Object { $_.Trim() }
        if ($p.Count -eq 4 -and $p[2] -match '^\d+$' -and $p[3] -match '^\d+$') {
            $gpus += [pscustomobject]@{ Nombre = $p[0]; Controlador = $p[1]; VramTotalMB = [int]$p[2]; VramLibreMB = [int]$p[3] }
        }
    }
    return ,$gpus
}

function Get-InfoGpu {
    $smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if (-not $smi) { return ,@() }
    try {
        $salida = & $smi.Source "--query-gpu=name,driver_version,memory.total,memory.free" "--format=csv,noheader,nounits" 2>$null
        return ConvertFrom-NvidiaSmi (($salida | Out-String))
    } catch { return ,@() }
}

function Get-MbLibres([string]$Ruta) {
    try {
        $raiz = [IO.Path]::GetPathRoot((Resolve-Path -LiteralPath $Ruta).Path)
        return [math]::Floor((New-Object IO.DriveInfo($raiz)).AvailableFreeSpace / 1MB)
    } catch { return -1 }
}

function Find-Python {
    # Devuelve @(ejecutable, argumentos...) de un Python ≥ 3.10, o $null.
    foreach ($c in @("py -3", "python", "python3")) {
        $partes = $c.Split(" ")
        try {
            & $partes[0] @($partes[1..9] | Where-Object { $_ }) -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) { return ,$partes }
        } catch { }
    }
    return $null
}

function Test-ProcesoPropio([int]$Id, [string]$Patron) {
    # ¿El PID sigue siendo un proceso nuestro? Evita matar un programa ajeno que reutilizó el PID.
    $p = Get-CimInstance Win32_Process -Filter "ProcessId = $Id" -ErrorAction SilentlyContinue
    return [bool]($p -and $p.CommandLine -match $Patron)
}

function Stop-ProcesoPropio([string]$ArchivoPid, [string]$Patron, [string]$Nombre) {
    if (-not (Test-Path -LiteralPath $ArchivoPid)) { return $false }
    $id = [int](Get-Content -LiteralPath $ArchivoPid)
    if (-not (Get-Process -Id $id -ErrorAction SilentlyContinue)) { Write-Aviso "$Nombre no estaba en marcha." }
    elseif (-not (Test-ProcesoPropio $id $Patron)) { Write-Aviso "El proceso $id ya no es de ApuntIA: no se toca." }
    else {
        taskkill /PID $id /T 2>&1 | Out-Null
        Start-Sleep -Seconds 2
        if (Get-Process -Id $id -ErrorAction SilentlyContinue) { taskkill /PID $id /T /F 2>&1 | Out-Null }
        Write-Bien "$Nombre detenido."
    }
    Remove-Item -LiteralPath $ArchivoPid -Force
    return $true
}

function Invoke-Json([string]$Url, [int]$Segundos = 3, [hashtable]$Cabeceras = @{}) {
    # GET que devuelve @{ Estado = código HTTP o 0; Cuerpo = objeto o $null }. Nunca lanza.
    try {
        $r = Invoke-WebRequest -Uri $Url -TimeoutSec $Segundos -UseBasicParsing -Headers $Cabeceras -ErrorAction Stop
        return @{ Estado = [int]$r.StatusCode; Cuerpo = ($r.Content | ConvertFrom-Json) }
    } catch {
        $resp = $_.Exception.Response
        if ($resp) {
            $codigo = [int]$resp.StatusCode
            # PowerShell 5.1 ya consumió el cuerpo del error y lo deja en ErrorDetails.Message.
            if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
                try { return @{ Estado = $codigo; Cuerpo = ($_.ErrorDetails.Message | ConvertFrom-Json) } } catch { }
            }
            try {
                $lector = New-Object IO.StreamReader($resp.GetResponseStream())
                return @{ Estado = $codigo; Cuerpo = ($lector.ReadToEnd() | ConvertFrom-Json) }
            } catch { return @{ Estado = $codigo; Cuerpo = $null } }
        }
        return @{ Estado = 0; Cuerpo = $null }
    }
}

Export-ModuleMember -Function *
