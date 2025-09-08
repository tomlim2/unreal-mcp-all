@echo off

REM Load environment variables from .env file if it exists
if exist "../.env" (
    echo 📄 Loading environment variables from .env file...
    for /f "usebackq tokens=1,2 delims==" %%a in ("../.env") do (
        if not "%%a"=="" if not "%%b"=="" (
            set "%%a=%%b"
        )
    )
)

REM Set default ports if not already set
if not defined UNREAL_TCP_PORT set UNREAL_TCP_PORT=55557
if not defined HTTP_BRIDGE_PORT set HTTP_BRIDGE_PORT=8080
if not defined FRONTEND_PORT set FRONTEND_PORT=3000

echo 🚀 MegaMelange 포트 초기화 스크립트
echo ====================================
echo.
echo 이 스크립트는 다음 서비스들을 자동으로 시작합니다:
echo - Python MCP 서버 (포트 %UNREAL_TCP_PORT%과 연결)
echo - HTTP 브리지 (포트 %HTTP_BRIDGE_PORT%)
echo - Next.js 프론트엔드 (포트 %FRONTEND_PORT%)
echo.
echo ⚠️  시작하기 전에 언리얼 엔진 프로젝트가 열려있는지 확인하세요!
echo.
pause

REM 현재 디렉토리 확인
if not exist "../Python" (
    echo ❌ 오류: Python 폴더를 찾을 수 없습니다.
    echo    프로젝트 루트 디렉토리에서 실행해주세요.
    pause
    exit /b 1
)

if not exist "../Frontend" (
    echo ❌ 오류: Frontend 폴더를 찾을 수 없습니다.
    echo    프로젝트 루트 디렉토리에서 실행해주세요.
    pause
    exit /b 1
)

echo 📂 작업 디렉토리 확인: OK
echo.

REM 기존 프로세스 정리 (포트 기반)
echo 🧹 기존 프로세스 정리 중...
netstat -ano | findstr ":%UNREAL_TCP_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%UNREAL_TCP_PORT% " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
    )
)
netstat -ano | findstr ":%HTTP_BRIDGE_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%HTTP_BRIDGE_PORT% " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
    )
)
netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%FRONTEND_PORT% " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
    )
)
timeout /t 2 >nul

echo ✅ 프로세스 정리 완료
echo.

REM 1. Python MCP 서버 시작
echo 🐍 1/3: Python MCP 서버 시작 중...
start "Python MCP 서버" cmd /k "cd ../Python && .venv\Scripts\activate && echo ✅ 가상환경 활성화됨 && echo 🚀 Python MCP 서버 시작 중... && .venv\Scripts\python.exe unreal_mcp_server.py"

REM 서버 시작 대기
timeout /t 3 >nul

REM 2. HTTP 브리지 시작  
echo 🌉 2/3: HTTP 브리지 시작 중...
start "HTTP 브리지" cmd /k "cd ../Python && .venv\Scripts\activate && echo ✅ 가상환경 활성화됨 && echo 🌉 HTTP 브리지 시작 중... && .venv\Scripts\python.exe http_bridge.py"

REM 브리지 시작 대기
timeout /t 3 >nul

REM 3. Next.js 프론트엔드 시작
echo 🌐 3/3: Next.js 프론트엔드 시작 중...
start "Next.js 프론트엔드" cmd /k "cd ../Frontend && echo 🌐 Next.js 프론트엔드 시작 중... && npm run dev -- --port %FRONTEND_PORT%"

echo.
echo 🎉 모든 서비스 시작 완료!
echo.
echo 📋 실행 중인 서비스:
echo    🐍 Python MCP 서버 (첫 번째 창) - 포트 %UNREAL_TCP_PORT%
echo    🌉 HTTP 브리지 (두 번째 창) - 포트 %HTTP_BRIDGE_PORT%
echo    🌐 Next.js 프론트엔드 (세 번째 창) - 포트 %FRONTEND_PORT%
echo.
echo 🌍 웹 인터페이스: http://localhost:%FRONTEND_PORT%
echo.
echo ⏹️  모든 서비스를 중지하려면 stop-ports.bat를 실행하세요.
echo.
echo 💡 팁: 각 터미널 창에서 Ctrl+C로 개별 서비스를 중지할 수 있습니다.
echo.
pause