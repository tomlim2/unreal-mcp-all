@echo off
echo 📦 MegaMelange 의존성 설치 스크립트
echo ====================================
echo.
echo 이 스크립트는 프로젝트에 필요한 모든 패키지를 설치합니다:
echo - Python 가상환경 생성 및 패키지 설치
echo - Node.js 패키지 설치 (Frontend)
echo - 환경 파일 설정
echo.
echo ⚠️  시작하기 전에 다음이 설치되어 있는지 확인하세요:
echo    - Python 3.10+
echo    - Node.js 18+
echo    - uv 패키지 매니저 (pip install uv)
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

REM 필수 도구 확인
echo 🔍 필수 도구 확인 중...
echo.

REM Python 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았거나 PATH에 없습니다.
    echo    https://python.org 에서 Python 3.10+ 을 설치해주세요.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo ✅ Python %%i 확인됨
)

REM Node.js 확인
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js가 설치되지 않았거나 PATH에 없습니다.
    echo    https://nodejs.org 에서 Node.js 18+ 을 설치해주세요.
    pause
    exit /b 1
) else (
    for /f %%i in ('node --version') do echo ✅ Node.js %%i 확인됨
)

REM uv 확인
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ uv 패키지 매니저가 설치되지 않았습니다.
    echo 📥 uv 설치 중...
    pip install uv
    if %errorlevel% neq 0 (
        echo ❌ uv 설치 실패. 수동으로 설치해주세요: pip install uv
        pause
        exit /b 1
    )
    echo ✅ uv 설치 완료
) else (
    for /f "tokens=2" %%i in ('uv --version') do echo ✅ uv %%i 확인됨
)

echo.
echo 🎉 모든 필수 도구가 확인되었습니다!
echo.

REM Python 환경 설정
echo 🐍 1/3: Python 환경 설정 중...
echo ================================
cd ../Python

echo 📦 가상환경 생성 중...
if exist ".venv" (
    echo ℹ️  기존 가상환경이 있습니다. 재생성 중...
    rmdir /s /q .venv
)

uv venv
if %errorlevel% neq 0 (
    echo ❌ 가상환경 생성 실패
    pause
    exit /b 1
)
echo ✅ 가상환경 생성 완료

echo 📥 Python 패키지 설치 중...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 가상환경 활성화 실패
    pause
    exit /b 1
)
uv pip install -e .
if %errorlevel% neq 0 (
    echo ❌ Python 패키지 설치 실패
    pause
    exit /b 1
)
echo ✅ Python 패키지 설치 완료

REM .env 파일 확인 및 생성
echo 📝 환경 파일 확인 중...
if not exist ".env" (
    echo 📄 .env 파일 생성 중...
    echo # MegaMelange 환경 변수 > .env
    echo # Anthropic API 키를 설정해주세요 >> .env
    echo ANTHROPIC_API_KEY=your-anthropic-api-key-here >> .env
    echo. >> .env
    echo ✅ .env 파일 생성됨
    echo.
    echo ⚠️  중요: .env 파일에 실제 Anthropic API 키를 설정해주세요!
    echo    편집기로 Python\.env 파일을 열어서 'your-anthropic-api-key-here'를 실제 키로 바꿔주세요.
) else (
    echo ✅ .env 파일 이미 존재함
)

cd ../..
echo.

REM Frontend 환경 설정
echo 🌐 2/3: Frontend 환경 설정 중...
echo =================================
cd ../Frontend

echo 📥 Node.js 패키지 설치 중...
npm install
if %errorlevel% neq 0 (
    echo ❌ Node.js 패키지 설치 실패
    pause
    exit /b 1
)
echo ✅ Node.js 패키지 설치 완료

cd ../..
echo.
echo 🎉 의존성 설치 완료!
echo ==================
echo.
echo 📋 설치된 구성요소:
echo    ✅ Python 가상환경 (.venv)
echo    ✅ Python MCP 패키지들 (FastMCP, Pydantic 등)
echo    ✅ Node.js 프론트엔드 패키지들 (Next.js, React 등)
echo    ✅ 환경 설정 파일 (.env)
echo.
echo 🚀 다음 단계:
echo    1. Python\.env 파일에서 ANTHROPIC_API_KEY 설정
echo    2. 언리얼 엔진 프로젝트 열기
echo    3. init-ports.bat 실행하여 모든 서비스 시작
echo.
echo 💡 문제가 있다면 README_HowToStart_Korean.md 파일을 참조하세요.
echo.
pause