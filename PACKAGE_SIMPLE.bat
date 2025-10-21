@echo off
title MegaMelange - Simple Package Build
color 0B

echo ========================================
echo MegaMelange Simple Package Build
echo ========================================
echo.
echo This script will:
echo  1. Build Python Backend
echo  2. Build Next.js Frontend
echo  3. Create distribution package
echo  4. Create ZIP file
echo.
echo Estimated time: 5-10 minutes
echo.
pause

REM ===========================================
REM Step 1: Build Python Backend
REM ===========================================
echo.
echo ========================================
echo [1/4] Building Python Backend...
echo ========================================
echo.

cd Python

if not exist "build_backend.bat" (
    echo [ERROR] build_backend.bat not found in Python folder!
    cd ..
    pause
    exit /b 1
)

call build_backend.bat

if errorlevel 1 (
    echo.
    echo [ERROR] Backend build failed!
    cd ..
    pause
    exit /b 1
)

if not exist "dist\MegaMelangeBackend.exe" (
    echo.
    echo [ERROR] MegaMelangeBackend.exe was not created!
    cd ..
    pause
    exit /b 1
)

echo.
echo Backend build successful!
cd ..

REM ===========================================
REM Step 2: Build Next.js Frontend
REM ===========================================
echo.
echo ========================================
echo [2/4] Building Next.js Frontend...
echo ========================================
echo.

cd Frontend

if not exist "package.json" (
    echo [ERROR] package.json not found in Frontend folder!
    cd ..
    pause
    exit /b 1
)

call npm run build

if errorlevel 1 (
    echo.
    echo [ERROR] Frontend build failed!
    cd ..
    pause
    exit /b 1
)

if not exist ".next\standalone\server.js" (
    echo.
    echo [ERROR] Frontend standalone build was not created!
    cd ..
    pause
    exit /b 1
)

echo.
echo Frontend build successful!
cd ..

REM ===========================================
REM Step 3: Create Distribution Package
REM ===========================================
echo.
echo ========================================
echo [3/4] Creating Distribution Package...
echo ========================================
echo.

REM Clean and create distribution folder
if exist "dist-package" (
    echo Cleaning old distribution...
    rd /s /q dist-package
)

mkdir dist-package

echo Copying backend...
copy Python\dist\MegaMelangeBackend.exe dist-package\ >nul

echo Copying frontend...
xcopy /E /I /Q Frontend\.next\standalone dist-package\frontend >nul
xcopy /E /I /Q Frontend\.next\static dist-package\frontend\.next\static >nul

echo Copying launcher and configuration files...
copy START.bat dist-package\ >nul
copy README.txt dist-package\ >nul

REM Create config.json template in distribution
echo Creating config.json template...
(
echo {
echo   "GOOGLE_API_KEY": "",
echo   "BLENDER_PATH": "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe",
echo   "ANTHROPIC_API_KEY": "",
echo   "OPENAI_API_KEY": "",
echo   "UNREAL_PROJECT_PATH": ""
echo }
) > dist-package\config.json

REM Create empty data_storage directory structure
echo Creating data_storage directory structure...
mkdir dist-package\data_storage\assets\images\generated >nul 2>&1
mkdir dist-package\data_storage\assets\images\references >nul 2>&1
mkdir dist-package\data_storage\assets\objects3d\obj >nul 2>&1
mkdir dist-package\data_storage\assets\objects3d\fbx >nul 2>&1
mkdir dist-package\data_storage\assets\videos >nul 2>&1
mkdir dist-package\data_storage\sessions\active >nul 2>&1
mkdir dist-package\data_storage\sessions\archived >nul 2>&1
mkdir dist-package\data_storage\sessions\metadata >nul 2>&1
mkdir dist-package\data_storage\uid >nul 2>&1
mkdir dist-package\data_storage\temp\processing >nul 2>&1
mkdir dist-package\data_storage\logs >nul 2>&1

echo.
echo Distribution package created successfully!

REM ===========================================
REM Step 4: Create ZIP Archive
REM ===========================================
echo.
echo ========================================
echo [4/4] Creating ZIP Archive...
echo ========================================
echo.

REM Get version from git tag or use default
set VERSION=1.0.0
set ZIP_NAME=MegaMelange-v%VERSION%.zip

echo Creating %ZIP_NAME%...

if exist "%ZIP_NAME%" (
    echo Removing old ZIP file...
    del "%ZIP_NAME%"
)

powershell -NoProfile -Command "Compress-Archive -Path dist-package\* -DestinationPath '%ZIP_NAME%' -CompressionLevel Optimal"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create ZIP file!
    pause
    exit /b 1
)

REM Get file size
for %%A in ("%ZIP_NAME%") do set SIZE=%%~zA
set /a SIZE_MB=%SIZE% / 1048576

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo Package created: %ZIP_NAME%
echo Size: %SIZE_MB% MB
echo.
echo Distribution folder: dist-package\
echo.
echo ========================================
echo   Next Steps
echo ========================================
echo.
echo 1. Test the package:
echo    - Extract %ZIP_NAME%
echo    - Edit config.json
echo    - Run START.bat
echo.
echo 2. Distribute:
echo    - Upload %ZIP_NAME% to GitHub Releases
echo    - Share download link with users
echo.
pause
