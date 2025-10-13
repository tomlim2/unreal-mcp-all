@echo off
REM MegaMelange Backend Build Script
REM Builds the Python HTTP bridge into a standalone executable using PyInstaller

echo ========================================
echo MegaMelange Backend Builder
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller is not installed!
    echo.
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo [1/3] Cleaning previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
echo       Done!
echo.

echo [2/3] Building backend executable with PyInstaller...
echo       This may take 5-10 minutes...
echo.
python -m PyInstaller build_backend.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying build...

if not exist "dist\MegaMelangeBackend.exe" (
    echo [ERROR] MegaMelangeBackend.exe was not created!
    pause
    exit /b 1
)

echo       Build successful!
echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable location: dist\MegaMelangeBackend.exe
echo Size:
dir "dist\MegaMelangeBackend.exe" | find "MegaMelangeBackend.exe"
echo.
echo Test the executable with:
echo   cd dist
echo   MegaMelangeBackend.exe
echo.
echo Press any key to exit...
pause >nul
