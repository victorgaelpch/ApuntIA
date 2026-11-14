# Pruebas de las funciones de los scripts de Windows (FULL-30). Sin Pester (no viene en todas
# las versiones de Windows): un mini-marco de aserciones. Funciona con Windows PowerShell 5.1 y pwsh.
#   powershell -NoProfile -ExecutionPolicy Bypass -File fullstack\tests\scripts\windows.pruebas.ps1
# Sale con 1 si falla alguna.
$ErrorActionPreference = "Stop"
$Scripts = Join-Path $PSScriptRoot "..\..\scripts"
Import-Module (Join-Path $Scripts "ApuntIA.Comun.psm1") -Force -DisableNameChecking
$script:fallos = 0; $script:total = 0
function Debe($nombre, [scriptblock]$prueba) {
    $script:total++
    try { if (& $prueba) { Write-Host "  ok  $nombre" } else { throw "resultado falso" } }
    catch { $script:fallos++; Write-Host "  MAL $nombre -> $_" -ForegroundColor Red }
}
$tmp = Join-Path ([IO.Path]::GetTempPath()) ("apuntia-pruebas-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null

Write-Host "Versiones"
Debe "0.12.10 >= 0.12.7" { Test-VersionMinima "ollama version is 0.12.10" @(0, 12, 7) }
Debe "0.12.6 < 0.12.7" { -not (Test-VersionMinima "0.12.6" @(0, 12, 7)) }
Debe "0.40.16 >= 0.12.7" { Test-VersionMinima "0.40.16" @(0, 12, 7) }
Debe "controlador 621.14 >= 551.61" { Test-VersionMinima "621.14" @(551, 61) }
Debe "controlador 546.33 < 551.61" { -not (Test-VersionMinima "546.33" @(551, 61)) }
Debe "texto sin números = 0" { -not (Test-VersionMinima "desconocida" @(0, 1)) }

Write-Host "URL del servidor IA"
Debe "https con nombre" { $null -eq (Test-UrlServidorIA "https://ia.ejemplo.org") }
Debe "http local" { $null -eq (Test-UrlServidorIA "http://127.0.0.1:8100") }
Debe "http externo no" { Test-UrlServidorIA "http://ia.ejemplo.org" }
Debe "https con IP no (sin certificado de nombre)" { Test-UrlServidorIA "https://203.0.113.5" }
Debe "credenciales no" { Test-UrlServidorIA "https://u:p@ia.ejemplo.org" }
Debe "parámetros no" { Test-UrlServidorIA "https://ia.ejemplo.org/?token=abc" }
Debe "fragmento no" { Test-UrlServidorIA "https://ia.ejemplo.org/#x" }
Debe "esquema raro no" { Test-UrlServidorIA "file:///C:/Windows" }
Debe "vacía no" { Test-UrlServidorIA "" }
Debe "relativa no" { Test-UrlServidorIA "ia.ejemplo.org" }

Write-Host "Archivos .env"
$env1 = Join-Path $tmp "a b ñ\.env"   # rutas con espacios y acentos
New-Item -ItemType Directory -Path (Split-Path $env1) | Out-Null
[IO.File]::WriteAllLines($env1, [string[]]@("# comentario", "APUNTIA_PUERTO=8000", "# APUNTIA_IA_URL=", "linea rara", "OTRA= con espacios "))
$v = Read-ArchivoEnv $env1
Debe "lee claves e ignora comentarios" { $v["APUNTIA_PUERTO"] -eq "8000" -and $v["OTRA"] -eq "con espacios" -and -not $v.Contains("APUNTIA_IA_URL") }
Set-ValorEnv $env1 "APUNTIA_IA_URL" "https://ia.ejemplo.org"
$lineas = Get-Content $env1
Debe "descomenta y fija la clave sin duplicarla" { ($lineas -match '^APUNTIA_IA_URL=').Count -eq 1 -and ($lineas -contains "APUNTIA_IA_URL=https://ia.ejemplo.org") }
Debe "conserva las demás líneas" { $lineas -contains "APUNTIA_PUERTO=8000" -and $lineas -contains "linea rara" }
Debe "deja copia .bak" { Test-Path "$env1.bak" }
Set-ValorEnv $env1 "NUEVA" "1"
Debe "añade claves nuevas al final" { (Get-Content $env1)[-1] -eq "NUEVA=1" }
Debe "rechaza saltos de línea (inyección)" { try { Set-ValorEnv $env1 "X" "a`nAPUNTIA_PUERTO=1"; $false } catch { $true } }
Debe "rechaza claves no válidas" { try { Set-ValorEnv $env1 "x;y" "1"; $false } catch { $true } }
Debe "archivo inexistente = vacío" { (Read-ArchivoEnv (Join-Path $tmp "no.env")).Count -eq 0 }

Write-Host "GPU"
$g = ConvertFrom-NvidiaSmi "NVIDIA GeForce RTX 3060, 621.14, 12288, 8471`r`n"
Debe "lee nvidia-smi" { $g.Count -eq 1 -and $g[0].VramTotalMB -eq 12288 -and $g[0].Controlador -eq "621.14" }
Debe "ignora salida no reconocida" { (ConvertFrom-NvidiaSmi "NVIDIA-SMI has failed").Count -eq 0 }
Debe "dos GPU" { (ConvertFrom-NvidiaSmi "A, 1.0, 100, 50`nB, 1.0, 200, 10").Count -eq 2 }

Write-Host "Procesos y consola"
Debe "PID ajeno no es propio" { -not (Test-ProcesoPropio $PID "ia_servidor") }
Debe "PID inexistente no es propio" { -not (Test-ProcesoPropio 999999 ".") }
$archivoPid = Join-Path $tmp "x.pid"; Set-Content $archivoPid $PID
Debe "no detiene un proceso ajeno que reutilizó el PID" { (Stop-ProcesoPropio $archivoPid "ia_servidor" "prueba") -and (Get-Process -Id $PID) -and -not (Test-Path $archivoPid) }
$env:APUNTIA_SIN_MENU = "1"
Debe "sin menú con APUNTIA_SIN_MENU" { -not (Test-ConsolaInteractiva) }
Remove-Item Env:APUNTIA_SIN_MENU
Debe "Invoke-Json sin servidor no lanza" { (Invoke-Json "http://127.0.0.1:9/salud" 1).Estado -eq 0 }

Write-Host "Sintaxis de todos los .ps1/.psm1"
foreach ($f in Get-ChildItem $Scripts -Include *.ps1, *.psm1 -Recurse) {
    $errores = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$null, [ref]$errores)
    Debe "sintaxis $($f.Name)" { $errores.Count -eq 0 }
}
Debe "iniciar.ps1 conserva los parámetros clásicos" {
    $ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $Scripts "iniciar.ps1"), [ref]$null, [ref]$null)
    $nombres = $ast.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath }
    -not (Compare-Object @("Modo", "Puerto", "Red", "SinNavegador", "SinVenv", "Reinstalar", "Comprobar") $nombres)
}

Remove-Item -Recurse -Force $tmp
Write-Host ""
if ($script:fallos) { Write-Host "$script:fallos de $script:total pruebas fallaron." -ForegroundColor Red; exit 1 }
Write-Host "$script:total pruebas correctas." -ForegroundColor Green
exit 0
