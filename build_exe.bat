@echo off
setlocal
cd /d "%~dp0"

echo ======================================================
echo Hand Game Controller - Windows EXE Builder
echo ======================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found. Install Python 3.11 or 3.12 and add it to PATH.
    pause
    exit /b 1
)

echo [1/4] Installing build requirements...
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

echo.
echo [2/4] Removing old build output...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist HandGameControllerCore.spec del /q HandGameControllerCore.spec
if exist HandGameController.spec del /q HandGameController.spec

echo.
echo [3/4] Building controller engine...
python -m PyInstaller --noconfirm --clean --onefile --name HandGameControllerCore --add-data "hand_landmarker.task;." --collect-all mediapipe --hidden-import=mediapipe.tasks.python.vision.hand_landmarker mian.py
if errorlevel 1 goto :error

echo.
echo [4/4] Building desktop control panel...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name HandGameController --add-data "theme_art;theme_art" launcher.py
if errorlevel 1 goto :error

echo.
echo BUILD COMPLETE
echo Output files:
echo   dist\HandGameController.exe
echo   dist\HandGameControllerCore.exe
echo.
echo Keep both EXE files in the same folder. The controller model is bundled into the core EXE.
echo User settings and logs are stored under %%LOCALAPPDATA%%\HandGameController.
pause
exit /b 0

:error
echo.
echo BUILD FAILED. Read the error messages above. If PyInstaller reports a missing module,
echo add its hidden-import or collect-all option to build_exe.bat and rebuild.
pause
exit /b 1
