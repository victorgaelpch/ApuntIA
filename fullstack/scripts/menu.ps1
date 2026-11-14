# Menú de ApuntIA para Windows (FULL-30). Aparece al ejecutar iniciar.bat SIN argumentos en una
# consola con una persona delante. Con argumentos, sin consola o en CI se usa el arranque clásico.
# Cada opción equivale a un comando no interactivo (se muestra para poder repetirlo o automatizarlo).
$Raiz = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Ps = Join-Path $PSHOME "powershell.exe"
if (-not (Test-Path $Ps)) { $Ps = "powershell" }

function Ejecutar([string]$Script, [string[]]$Argumentos) {
    & $Ps -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot $Script) @Argumentos
    $codigo = $LASTEXITCODE
    Write-Host ""
    Write-Host "(código de salida: $codigo)" -ForegroundColor DarkGray
    Read-Host "Pulsa Intro para volver al menú" | Out-Null
}

$opciones = @(
    @{ Texto = "Iniciar ApuntIA (esta laptop o PC)";                 Cmd = "iniciar.bat -Modo app";          Script = "iniciar.ps1"; Args = @("-Modo", "app") },
    @{ Texto = "Instalar o reparar el servidor IA (solo PC con GPU)"; Cmd = "iniciar.bat -Modo instalar-ia";  Script = "ia.ps1";      Args = @("-Accion", "instalar") },
    @{ Texto = "Iniciar el servidor IA (solo PC con GPU)";           Cmd = "iniciar.bat -Modo servidor-ia";  Script = "ia.ps1";      Args = @("-Accion", "iniciar") },
    @{ Texto = "Configurar la conexión con el servidor IA";          Cmd = "iniciar.bat -Modo configurar";   Script = "ia.ps1";      Args = @("-Accion", "configurar") },
    @{ Texto = "Aprobar o revocar equipos (solo PC con GPU)";       Cmd = "iniciar.bat -Modo dispositivos"; Script = "ia.ps1";      Args = @("-Accion", "dispositivos") },
    @{ Texto = "Diagnosticar";                                       Cmd = "iniciar.bat -Modo diagnostico";  Script = "ia.ps1";      Args = @("-Accion", "diagnostico") },
    @{ Texto = "Detener todo lo que inició ApuntIA";                 Cmd = "detener.bat";                   Script = "detener.ps1"; Args = @() }
)

while ($true) {
    Clear-Host
    Write-Host "=== ApuntIA ===" -ForegroundColor Cyan
    Write-Host ""
    for ($i = 0; $i -lt $opciones.Count; $i++) {
        Write-Host ("  {0}. {1}" -f ($i + 1), $opciones[$i].Texto)
        Write-Host ("       equivale a: {0}" -f $opciones[$i].Cmd) -ForegroundColor DarkGray
    }
    Write-Host "  0. Salir"
    Write-Host ""
    $eleccion = Read-Host "Elige una opción (0-$($opciones.Count))"
    if ($eleccion -eq "0" -or $eleccion -match '^(s|salir|q)$') { exit 0 }
    if ($eleccion -match '^\d+$' -and [int]$eleccion -ge 1 -and [int]$eleccion -le $opciones.Count) {
        $o = $opciones[[int]$eleccion - 1]
        Ejecutar $o.Script $o.Args
    } else {
        Write-Host "Opción no válida: escribe un número del 0 al $($opciones.Count)." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}
