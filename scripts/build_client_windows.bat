@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo === HeartBeat Windows client build ===
echo Uses .venv-win so it will not clash with macOS .venv in the same folder.
echo.

echo Working directory: %CD%
python --version
echo.

echo === Step 0: environment checks ===
python -c "import platform,sys; print('arch=', platform.machine()); print('bits=', sys.maxsize > 2**32 and 64 or 32); print('ver=', sys.version)"
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
  echo.
  echo [WARN] This looks like Windows on ARM. Prefer 64-bit x64 Python in the VM.
)
echo %CD% | findstr /I /C:"\\psf\\" >nul
if not errorlevel 1 (
  echo [WARN] Building on a Parallels share. Copy to a local disk first, e.g. C:\src\HeartBeat
)
echo %CD% | findstr /I /C:"\\mac\\" >nul
if not errorlevel 1 (
  echo [WARN] Building on a Mac share. Copy to a local disk first, e.g. C:\src\HeartBeat
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

echo === Step 1: pip bootstrap ===
"%PY%" -m ensurepip --upgrade >nul 2>&1
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
  echo [FAIL] cannot bootstrap pip in .venv-win. Delete .venv-win and run again.
  exit /b 1
)

echo === Step 2: project + PySide6 + full winrt stack ===
"%PY%" -m pip install -e ".[client]"
if errorlevel 1 (
  echo [FAIL] project deps failed.
  echo        Use x64 Python 3.10-3.12 and a local disk path.
  exit /b 1
)

"%PY%" -m pip install --upgrade ^
  "winrt-runtime>=3.2.1" ^
  "winrt-Windows.Foundation>=3.2.1" ^
  "winrt-Windows.Foundation.Collections>=3.2.1" ^
  "winrt-Windows.Media.Control>=2.0.0"
if errorlevel 1 (
  echo [FAIL] winrt packages failed. Music capture cannot work in the packaged client.
  exit /b 1
)

"%PY%" -c "import PySide6; print('PySide6', PySide6.__version__)"
if errorlevel 1 exit /b 1

echo === Step 3: verify GSMTC works BEFORE packaging ===
"%PY%" scripts\diagnose_windows_media.py
if errorlevel 1 (
  echo.
  echo [FAIL] GSMTC check failed. Do NOT package until diagnose_windows_media.py succeeds.
  echo        Play a song in Media Player and run the diagnose script again.
  exit /b 1
)

echo === Step 4: packaging tools ===
"%PY%" -m pip install pyside6-deploy nuitka ordered-set zstandard
if errorlevel 1 (
  echo [WARN] pyside6-deploy unavailable, falling back to PyInstaller...
  "%PY%" -m pip install pyinstaller
  if errorlevel 1 (
    echo [FAIL] no packager available.
    exit /b 1
  )
  set USE_PYINSTALLER=1
)

echo === Step 5: icons ===
"%PY%" scripts\generate_icons.py
if errorlevel 1 exit /b 1

echo === Step 6: frontend (optional) ===
if exist "frontend\package.json" (
  where npm >nul 2>nul
  if not errorlevel 1 (
    pushd frontend
    if not exist "node_modules" call npm install --registry=https://registry.npmmirror.com
    if not errorlevel 1 call npm run build
    popd
  )
)

echo === Step 7: package with winrt included ===
if defined USE_PYINSTALLER (
  "%PY%" -m PyInstaller --noconfirm --windowed --name HeartBeat ^
    --add-data "resources\icons;resources\icons" ^
    --hidden-import winrt ^
    --hidden-import winrt.windows ^
    --hidden-import winrt.windows.foundation ^
    --hidden-import winrt.windows.foundation.collections ^
    --hidden-import winrt.windows.media.control ^
    --collect-all winrt ^
    heartbeat\client\main.py
) else (
  set DEPLOY=.venv-win\Scripts\pyside6-deploy.exe
  if not exist "%DEPLOY%" (
    "%PY%" -m pyside6_deploy --force --name HeartBeat --mode standalone --extra-modules=Network ^
      --extra-ignore-dirs=frontend,data,docs,tests,resources,scripts,.idea,.venv,.venv-win,assets ^
      heartbeat\client\main.py
  ) else (
    "%DEPLOY%" --force --name HeartBeat --mode standalone --extra-modules=Network ^
      --extra-ignore-dirs=frontend,data,docs,tests,resources,scripts,.idea,.venv,.venv-win,assets ^
      heartbeat\client\main.py
  )
)

if errorlevel 1 (
  echo.
  echo [FAIL] packaging failed.
  exit /b 1
)

echo.
echo === Done ===
echo Packaged client should now include the full winrt GSMTC stack and read Now Playing.
echo Output is under heartbeat\client\ or deployment\ or dist\
endlocal
