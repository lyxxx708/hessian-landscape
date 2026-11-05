@echo off
REM Safe default: inspect only. No experiment, pause, push or installation.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0START.ps1" -Mode Inspect
pause
