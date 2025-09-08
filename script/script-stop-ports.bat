@echo off

REM Load environment variables from .env file if it exists
if exist "../.env" (
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
echo 🛑 MegaMelange 서비스 중지 스크립트
echo ===================================
echo.
echo 설정된 포트에서 실행 중인 서비스들을 중지합니다...
echo.

REM 포트 기반 프로세스 중지
echo 🐍 MCP 서버 프로세스 중지 중... (포트 %UNREAL_TCP_PORT%)
netstat -ano | findstr ":%UNREAL_TCP_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%UNREAL_TCP_PORT% " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
    )
    echo ✅ MCP 서버 프로세스 중지됨
) else (
    echo ℹ️  포트 %UNREAL_TCP_PORT%에서 실행 중인 프로세스가 없습니다
)

echo.

echo 🌉 HTTP 브리지 프로세스 중지 중... (포트 %HTTP_BRIDGE_PORT%)
netstat -ano | findstr ":%HTTP_BRIDGE_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%HTTP_BRIDGE_PORT% " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
    )
    echo ✅ HTTP 브리지 프로세스 중지됨
) else (
    echo ℹ️  포트 %HTTP_BRIDGE_PORT%에서 실행 중인 프로세스가 없습니다
)

echo.

echo 🌐 프론트엔드 프로세스 중지 중... (포트 %FRONTEND_PORT%)
netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%FRONTEND_PORT% " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
    )
    echo ✅ 프론트엔드 프로세스 중지됨
) else (
    echo ℹ️  포트 %FRONTEND_PORT%에서 실행 중인 프로세스가 없습니다
)

echo.

REM 포트 상태 확인
echo 📊 포트 상태 확인:
echo.

netstat -ano | findstr :%UNREAL_TCP_PORT% >nul
if %errorlevel% == 0 (
    echo ❌ 포트 %UNREAL_TCP_PORT% (Unreal Engine): 아직 사용 중
) else (
    echo ✅ 포트 %UNREAL_TCP_PORT% (Unreal Engine): 해제됨
)

netstat -ano | findstr :%HTTP_BRIDGE_PORT% >nul
if %errorlevel% == 0 (
    echo ❌ 포트 %HTTP_BRIDGE_PORT% (HTTP Bridge): 아직 사용 중
) else (
    echo ✅ 포트 %HTTP_BRIDGE_PORT% (HTTP Bridge): 해제됨
)

netstat -ano | findstr :%FRONTEND_PORT% >nul
if %errorlevel% == 0 (
    echo ❌ 포트 %FRONTEND_PORT% (Frontend): 아직 사용 중
) else (
    echo ✅ 포트 %FRONTEND_PORT% (Frontend): 해제됨
)

echo.
echo 🎉 서비스 중지 완료!
echo.
echo 💡 참고: 언리얼 엔진은 수동으로 닫아야 합니다.
echo.
pause