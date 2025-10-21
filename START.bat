@echo off
title MegaMelange
color 0A
echo ========================================
echo MegaMelange - AI Creative Hub
echo ========================================
echo.

REM Check if config.json exists
if not exist "config.json" (
    echo [ERROR] config.json not found!
    echo.
    echo Please create config.json file with your API keys.
    echo See README.txt for instructions.
    echo.
    pause
    exit /b 1
)

echo [1/4] Loading configuration...
REM Read config.json using PowerShell
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Content config.json -Raw | ConvertFrom-Json).GOOGLE_API_KEY"') do set GOOGLE_API_KEY=%%i
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Content config.json -Raw | ConvertFrom-Json).BLENDER_PATH"') do set BLENDER_PATH=%%i
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Content config.json -Raw | ConvertFrom-Json).ANTHROPIC_API_KEY"') do set ANTHROPIC_API_KEY=%%i
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Content config.json -Raw | ConvertFrom-Json).OPENAI_API_KEY"') do set OPENAI_API_KEY=%%i
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Content config.json -Raw | ConvertFrom-Json).UNREAL_PROJECT_PATH"') do set UNREAL_PROJECT_PATH=%%i

REM Check required API key
if "%GOOGLE_API_KEY%"=="" (
    echo [ERROR] GOOGLE_API_KEY is required!
    echo.
    echo Please edit config.json and add your Google API Key.
    echo.
    pause
    exit /b 1
)

echo Configuration loaded successfully.
echo.

echo [2/4] Starting Python Backend...
REM Check if backend exists
if not exist "MegaMelangeBackend.exe" (
    echo [ERROR] MegaMelangeBackend.exe not found!
    echo.
    echo Please ensure you have the complete MegaMelange package.
    echo.
    pause
    exit /b 1
)

start "MegaMelange Backend" /MIN cmd /c "set GOOGLE_API_KEY=%GOOGLE_API_KEY% && set BLENDER_PATH=%BLENDER_PATH% && set ANTHROPIC_API_KEY=%ANTHROPIC_API_KEY% && set OPENAI_API_KEY=%OPENAI_API_KEY% && set UNREAL_PROJECT_PATH=%UNREAL_PROJECT_PATH% && MegaMelangeBackend.exe"
echo Backend started (running in background with API keys)
echo.

echo [3/4] Waiting for backend to initialize...
timeout /t 3 /nobreak >nul
echo.

echo [4/4] Starting Frontend Server...
REM Check if frontend folder exists
if not exist "frontend\server.js" (
    echo [ERROR] Frontend files not found!
    echo.
    echo Please ensure you have the complete MegaMelange package.
    echo.
    pause
    exit /b 1
)

cd frontend
start "MegaMelange Frontend" /MIN cmd /c "set PORT=34115 && node server.js"
cd ..
echo Frontend started (running in background on port 34115)
echo.

echo Waiting for frontend to initialize...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   MegaMelange is now running!
echo ========================================
echo.
echo   Web Interface: http://localhost:34115
echo.
echo   Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:34115

echo.
echo ========================================
echo.
echo Press any key to STOP MegaMelange...
echo.
pause >nul

echo.
echo Shutting down MegaMelange...
taskkill /FI "WINDOWTITLE eq MegaMelange*" /F >nul 2>&1
echo.
echo MegaMelange stopped.
timeout /t 2 /nobreak >nul
