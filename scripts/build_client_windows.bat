@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo === HeartBeat Windows client build ===

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtualenv...
  python -m venv .venv
  if errorlevel 1 exit /b 1
)

set PY=.venv\Scripts\python.exe
set PIP=.venv\Scripts\pip.exe

echo === Installing project and packaging tools ===
"%PIP%" install -e ".[client]"
if errorlevel 1 exit /b 1
"%PIP%" install pyside6-deploy nuitka ordered-set zstandard
if errorlevel 1 exit /b 1

echo === Generating icons ===
"%PY%" scripts\generate_icons.py
if errorlevel 1 exit /b 1

echo === Building frontend (optional) ===
if exist "frontend\package.json" (
  pushd frontend
  if not exist "node_modules" call npm install --registry=https://registry.npmmirror.com
  if errorlevel 1 (
    popd
    echo Frontend install failed, continue without frontend assets.
  ) else (
    call npm run build
    popd
  )
)

echo === pyside6-deploy ===
set DEPLOY=.venv\Scripts\pyside6-deploy.exe
if not exist "%DEPLOY%" set DEPLOY=.venv\Scripts\python.exe -m pyside6_deploy
"%DEPLOY%" --force --name HeartBeat --mode standalone --extra-ignore-dirs=frontend,data,docs,tests,resources,scripts,.idea,.venv,assets heartbeat\client\main.py
if errorlevel 1 (
  echo Deploy failed. Try running: pyside6-deploy heartbeat\client\main.py
  exit /b 1
)

echo === Done ===
echo Look for HeartBeat.exe / HeartBeat folder under:
echo   %CD%\heartbeat\client\
echo   %CD%\deployment\
echo
echo Optional: wrap the standalone folder with Inno Setup for a Start Menu installer.
echo Note: nowplaying-cli is macOS only; Windows media uses winrt-Windows.Media.Control.
endlocal
