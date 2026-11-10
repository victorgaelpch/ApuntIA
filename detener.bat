@echo off
REM Detiene ApuntIA en Windows: ver fullstack\scripts\detener.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fullstack\scripts\detener.ps1"
exit /b %ERRORLEVEL%
