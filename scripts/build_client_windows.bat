@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo === HeartBeat Windows client build ===
echo Uses .venv-win so it will not clash with macOS .venv in the same folder.
echo.

echo Working directory: %CD%
echo Python:
python --version
echo.

echo === Step 0: environment checks ===
python -c "import platform,sys; print('arch=', platform.machine()); print('bits=', sys.maxsize > 2**32 and 64 or 32); print('ver=', sys.version)"
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
  echo.
  echo [WARN] This looks like Windows on ARM. PySide6 / pyside6-deploy may not have ARM64 wheels.
  echo        Prefer 64-bit Python x64 inside the VM if PySide6 install fails.
)
echo %CD% | findstr /I /C:"\\psf\\" >nul
if %errorlevel%==0 (
  echo.
  echo [WARN] You are building inside a Parallels shared folder ^(\\psf\...^).
  echo        Copy the project to a local disk first, e.g. C:\src\HeartBeat
  echo        Shared-folder compiles are slow and can fail.
)
echo.

if not exist ".venv-win\Scripts\python.exe" (
  echo === Creating virtualenv ===
  python -m venv .venv-win
  if errorlevel 1 (
    echo [FAIL] python -m venv failed.
    exit /b 1
  )
)

set PY=.venv-win\Scripts\python.exe
set PIP=.venv-win\Scripts\pip.exe

echo === Step 1: core runtime deps ===
"%PIP%" install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1

echo === Step 2: install heartbeat + PySide6 ===
"%PIP%" install -e ".[client]"
if errorlevel 1 (
  echo [FAIL] project deps failed. If PySide6 has no wheel for this Python/arch,
  echo        install 64-bit x64 Python 3.10-3.12 and recreate .venv-win.
  exit /b 1
)

"%PY%" -c "import PySide6,sys; print('PySide6', PySide6.__version__)"
if errorlevel 1 (
  echo [FAIL] PySide6 not importable after install.
  exit /b 1
)

echo === Step 3: packaging tools ===
"%PIP%" install pyside6-deploy nuitka ordered-set zstandard
if errorlevel 1 (
  echo [WARN] pyside6-deploy is not installable in this environment.
  echo        Trying fallback via PyInstaller...
  "%PIP%" install pyinstaller
  if errorlevel 1 (
    echo [FAIL] neither pyside6-deploy nor pyinstaller is available.
    exit /b 1
  )
  set USE_PYINSTALLER=1
)

echo === Step 4: icons ===
"%PY%" scripts\generate_icons.py
if errorlevel 1 exit /b 1

echo === Step 5: frontend (optional) ===
if exist "frontend\package.json" (
  where npm >nul 2>nul
  if not errorlevel 1 (
    pushd frontend
    if not exist "node_modules" call npm install --registry=https://registry.npmmirror.com
    if not errorlevel 1 call npm run build
    popd
  )
)

echo === Step 6: package ===
if defined USE_PYINSTALLER (
  "%PY%" -m PyInstaller --noconfirm --windowed --name HeartBeat ^
    --add-data "resources\icons;resources\icons" ^
    heartbeat\client\main.py
) else (
  set DEPLOY=.venv-win\Scripts\pyside6-deploy.exe
  if not exist "%DEPLOY%" (
    "%PY%" -m pyside6_deploy --force --name HeartBeat --mode standalone --extra-ignore-dirs=frontend,data,docs,tests,resources,scripts,.idea,.venv,.venv-win,assets heartbeat\client\main.py
  ) else (
    "%DEPLOY%" --force --name HeartBeat --mode standalone --extra-ignore-dirs=frontend,data,docs,tests,resources,scripts,.idea,.venv,.venv-win,assets heartbeat\client\main.py
  )
)

if errorlevel 1 (
  echo.
  echo [FAIL] packaging failed. See messages above.
  exit /b 1
)

echo.
echo === Done ===
echo Look for HeartBeat under:
echo   %CD%\heartbeat\client\
echo   %CD%\deployment\
echo   %CD%\dist\
endlocal
