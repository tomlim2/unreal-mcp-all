@echo off
echo ========================================
echo MegaMelange Standalone App Builder
echo ========================================
echo.
echo IMPORTANT: You must have installed Rust from https://rustup.rs/
echo            and RESTARTED all terminal windows!
echo.
pause

echo.
echo Starting build process...
echo This will take 15-25 minutes.
echo.

REM Call INSTALL_AND_BUILD.bat from build/ folder
call "%~dp0INSTALL_AND_BUILD.bat"

if errorlevel 1 (
    echo.
    echo ========================================
    echo Build FAILED!
    echo ========================================
    echo.
    echo Common issues:
    echo   1. Rust not installed or terminal not restarted
    echo   2. Missing dependencies
    echo.
    echo Please check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build SUCCESS!
echo ========================================
echo.
echo Your app is ready at:
echo   Frontend\src-tauri\target\release\megamelange-desktop.exe
echo.
echo Windows Installer (MSI):
echo   Frontend\src-tauri\target\release\bundle\msi\
echo.
echo Press any key to open the release folder...
pause >nul
REM Open release folder (navigate from build/ to project root)
explorer "%~dp0..\Frontend\src-tauri\target\release"
