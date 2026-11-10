@echo off
REM Lanzador de ApuntIA en Windows: ver fullstack\scripts\iniciar.ps1 (opciones: -Puerto N -Red -SinNavegador ...)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fullstack\scripts\iniciar.ps1" %*
exit /b %ERRORLEVEL%
