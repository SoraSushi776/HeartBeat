@echo off
setlocal
cd /d "%~dp0.."
if exist ".venv-win\Scripts\python.exe" (
  set PY=.venv-win\Scripts\python.exe
) else (
  set PY=python
)
echo Using %PY%
"%PY%" scripts\diagnose_windows_media.py
echo.
echo --- done. Copy the output above if you need help ---
endlocal
