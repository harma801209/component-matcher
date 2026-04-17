@echo off
setlocal
set "ROOT=%~dp0"
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%sync_local_and_public.ps1"
if errorlevel 1 pause
