@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0open-review.ps1" %*
if errorlevel 1 (
  echo.
  echo Failed to open VKP review page.
  pause
)
