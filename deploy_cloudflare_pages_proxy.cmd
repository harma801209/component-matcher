@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy_cloudflare_pages_proxy.ps1" %*
endlocal
