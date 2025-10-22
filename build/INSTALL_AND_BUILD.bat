@echo off

REM Change to project root directory (parent of build/)
cd /d "%~dp0\.."

echo ========================================
echo MegaMelange Standalone App - Installation and Build
echo ========================================
echo.

REM Check if Rust is installed
echo [Step 1/5] Checking Rust installation...
rustc --version
echo Rust is installed!
echo.

REM Check if cargo is installed
echo [Step 2/5] Checking Cargo...
cargo --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Cargo not found!
    exit /b 1
) else (
    cargo --version
    echo Cargo is installed!
)
echo.

REM Build Python backend
echo [Step 3/5] Building Python backend...
echo This may take 5-10 minutes...
cd Python
if not exist "build_backend.bat" (
    echo [ERROR] build_backend.bat not found!
    cd ..
    pause
    exit /b 1
)

call build_backend.bat
if errorlevel 1 (
    echo [ERROR] Backend build failed!
    cd ..
    pause
    exit /b 1
)
cd ..
echo Backend build complete!
echo.

REM Build Frontend with Next.js
echo [Step 4/5] Building Next.js frontend...
cd Frontend
call npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed!
    cd ..
    pause
    exit /b 1
)
cd ..
echo Frontend build complete!
echo.

REM Build Tauri app
echo [Step 5/5] Building Tauri desktop app...
echo This may take 10-20 minutes (first time)...
cd Frontend
call npm run tauri:build
if errorlevel 1 (
    echo [ERROR] Tauri build failed!
    cd ..
    pause
    exit /b 1
)
cd ..
echo.

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable location:
echo   Frontend\src-tauri\target\release\megamelange-desktop.exe
echo.
echo Installer location:
echo   Frontend\src-tauri\target\release\bundle\msi\
echo.
echo Press any key to exit...
pause >nul
