@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run.ps1"
set "RUN_EXIT=%errorlevel%"
if not "%RUN_EXIT%"=="0" pause
exit /b %RUN_EXIT%
