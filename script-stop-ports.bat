@echo off
echo 🛑 MegaMelange 서비스 중지 스크립트
echo ===================================
echo.
echo 모든 Python 및 Node.js 프로세스를 중지합니다...
echo.

REM Python 프로세스 중지
echo 🐍 Python 프로세스 중지 중...
tasklist | findstr python.exe >nul
if %errorlevel% == 0 (
    taskkill /F /IM python.exe
    echo ✅ Python 프로세스 중지됨
) else (
    echo ℹ️  실행 중인 Python 프로세스가 없습니다
)

echo.

REM Node.js 프로세스 중지
echo 🌐 Node.js 프로세스 중지 중...
tasklist | findstr node.exe >nul
if %errorlevel% == 0 (
    taskkill /F /IM node.exe
    echo ✅ Node.js 프로세스 중지됨
) else (
    echo ℹ️  실행 중인 Node.js 프로세스가 없습니다
)

echo.

REM 포트 상태 확인
echo 📊 포트 상태 확인:
echo.

netstat -ano | findstr :55557 >nul
if %errorlevel% == 0 (
    echo ❌ 포트 55557 (Unreal Engine): 아직 사용 중
) else (
    echo ✅ 포트 55557 (Unreal Engine): 해제됨
)

netstat -ano | findstr :8080 >nul
if %errorlevel% == 0 (
    echo ❌ 포트 8080 (HTTP Bridge): 아직 사용 중
) else (
    echo ✅ 포트 8080 (HTTP Bridge): 해제됨
)

netstat -ano | findstr :3000 >nul
if %errorlevel% == 0 (
    echo ❌ 포트 3000 (Frontend): 아직 사용 중
) else (
    echo ✅ 포트 3000 (Frontend): 해제됨
)

echo.
echo 🎉 서비스 중지 완료!
echo.
echo 💡 참고: 언리얼 엔진은 수동으로 닫아야 합니다.
echo.
pause