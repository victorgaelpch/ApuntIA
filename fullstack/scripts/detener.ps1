# Detiene lo que arrancó iniciar.ps1 (FULL-11). Solo termina procesos cuyo PID está en
# fullstack\.estado\ y que siguen siendo de ApuntIA (python con uvicorn, o Spring Boot).
$Raiz = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Estado = Join-Path $Raiz "fullstack\.estado"

function Detener($nombre, $patron) {
    $archivo = Join-Path $Estado "$nombre.pid"
    if (-not (Test-Path $archivo)) { return }
    $id = [int](Get-Content $archivo)
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $id" -ErrorAction SilentlyContinue
    if (-not $proc) { Write-Host "! $nombre no estaba en marcha." -ForegroundColor Yellow }
    elseif ($proc.CommandLine -notmatch $patron) { Write-Host "! El proceso $id ya no es de ApuntIA: no se toca." -ForegroundColor Yellow }
    else {
        # taskkill /T termina también los procesos hijos (p. ej. Java bajo mvnw.cmd)
        taskkill /PID $id /T 2>&1 | Out-Null
        Start-Sleep -Seconds 2
        if (Get-Process -Id $id -ErrorAction SilentlyContinue) { taskkill /PID $id /T /F 2>&1 | Out-Null }
        Write-Host "OK $nombre detenido." -ForegroundColor Green
    }
    Remove-Item $archivo -Force
}

if (-not (Test-Path $Estado) -or -not (Get-ChildItem $Estado -Filter *.pid)) { Write-Host "OK ApuntIA no estaba en marcha." -ForegroundColor Green; exit 0 }
Detener "backend" "uvicorn main:app"
Detener "spring" "spring-boot|bootRun"
# Servidor IA y Ollama (FULL-30): solo si los arrancó ia.ps1 (PID registrado y línea de órdenes propia).
Detener "ia-servidor" "ia_servidor"
Detener "ollama" "ollama(\.exe)?`"?\s+serve"
exit 0
