@echo off
rem MuscleSense Lab - doble clic para preparar el entorno en Windows.
rem Crea .venv, instala requirements.txt, instala extensiones de VS Code y ejecuta las pruebas.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\preparar_windows.ps1" %*
echo.
pause
