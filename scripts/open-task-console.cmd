@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0open-task-console.ps1" %*
if errorlevel 1 (
  echo.
  echo Failed to open VKP task console.
  pause
)
