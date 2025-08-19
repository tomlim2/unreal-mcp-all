# 🚀 MegaMelange 자동화 스크립트 가이드

이 프로젝트에는 설정과 실행을 쉽게 해주는 3개의 배치 파일이 있습니다.

## 📋 스크립트 개요

| 스크립트 | 용도 | 실행 시점 |
|---------|------|-----------|
| `script-install-packages.bat` | 모든 의존성 설치 | **최초 1회** (프로젝트 설정 시) |
| `script-init-ports.bat` | 모든 서비스 시작 | **매번** (개발 시작할 때) |
| `script-stop-ports.bat` | 모든 서비스 중지 | **매번** (개발 종료할 때) |

---

## 📦 1. script-install-packages.bat

### 🎯 목적
프로젝트를 처음 설정할 때 모든 의존성을 자동으로 설치합니다.

### 🔧 기능
- ✅ **필수 도구 확인** (Python, Node.js, uv)
- ✅ **Python 가상환경 생성** (`.venv` 폴더)
- ✅ **Python 패키지 설치** (FastMCP, Pydantic, anthropic 등)
- ✅ **Node.js 패키지 설치** (Next.js, React, TypeScript 등)
- ✅ **환경 파일 생성** (`.env` 파일 템플릿)
- ✅ **설치 상태 검증** 및 오류 검사

### 📝 사용법
```bash
# 프로젝트 루트 디렉토리에서 실행
script-install-packages.bat
```

### ⚠️ 실행 후 해야 할 일
1. `Python\.env` 파일을 열어서 실제 Anthropic API 키 설정
2. 언리얼 엔진 프로젝트 열기 및 플러그인 활성화

---

## 🚀 2. script-init-ports.bat

### 🎯 목적
개발할 때마다 모든 서비스를 한 번에 시작합니다.

### 🔧 기능
- ✅ **기존 프로세스 정리** (충돌 방지)
- ✅ **Python MCP 서버 시작** (포트 55557 연결)
- ✅ **HTTP 브리지 시작** (포트 8080)
- ✅ **Next.js 프론트엔드 시작** (포트 3000)
- ✅ **별도 터미널 창** 3개로 각각 실행
- ✅ **한국어 진행 상황** 표시

### 📝 사용법
```bash
# 언리얼 엔진을 먼저 열고, 프로젝트 루트에서 실행
script-init-ports.bat
```

### ⚠️ 사전 조건
- 언리얼 엔진 프로젝트가 열려있어야 함
- `script-install-packages.bat`을 먼저 실행했어야 함

---

## 🛑 3. script-stop-ports.bat

### 🎯 목적
개발을 마칠 때 모든 서비스를 깔끔하게 중지합니다.

### 🔧 기능
- ✅ **모든 Python 프로세스 종료**
- ✅ **모든 Node.js 프로세스 종료**
- ✅ **포트 상태 확인** (55557, 8080, 3000)
- ✅ **중지 결과 리포트**

### 📝 사용법
```bash
# 어디서든 실행 가능
script-stop-ports.bat
```

---

## 🎓 완전 가이드

### 🥇 첫 번째: 프로젝트 설정 (1회만)
1. **필수 도구 설치**
   - Python 3.10+ ([python.org](https://python.org))
   - Node.js 18+ ([nodejs.org](https://nodejs.org))

2. **의존성 자동 설치**
   ```bash
   script-install-packages.bat
   ```

3. **API 키 설정**
   - `Python\.env` 파일 열기
   - `your-anthropic-api-key-here`를 실제 키로 변경

### 🥈 두 번째: 매번 개발할 때
1. **언리얼 엔진 프로젝트 열기**
   - `MCPGameProject\MCPGameProject.uproject` 실행
   - UnrealMCP 플러그인 활성화 확인

2. **모든 서비스 시작**
   ```bash
   script-init-ports.bat
   ```

3. **웹 브라우저에서 개발**
   - http://localhost:3000 접속
   - 자연어 명령어 입력하여 언리얼 엔진 조작

### 🥉 세 번째: 개발 종료할 때
```bash
script-stop-ports.bat
```

---

## 🔧 문제 해결

### Q: 스크립트가 "경로를 찾을 수 없습니다" 오류?
**A:** 프로젝트 루트 디렉토리에서 실행하세요. (Python, Frontend 폴더가 보이는 곳)

### Q: "Python을 찾을 수 없습니다" 오류?
**A:** Python이 PATH에 추가되지 않았습니다. Python 재설치 시 "Add to PATH" 체크

### Q: "uv를 찾을 수 없습니다" 오류?
**A:** 스크립트가 자동으로 설치를 시도합니다. 수동 설치: `pip install uv`

### Q: 포트가 이미 사용 중?
**A:** `script-stop-ports.bat`을 먼저 실행하여 기존 프로세스를 정리하세요.

---

## 💡 고급 팁

### 개발자를 위한 수동 실행
자동화 스크립트 대신 수동으로 실행하려면 `README_HowToStart_Korean.md`의 수동 단계를 참조하세요.

### 로그 확인
각 서비스의 터미널 창에서 실시간 로그를 확인할 수 있습니다.

### 개별 서비스 재시작
특정 서비스만 재시작하려면 해당 터미널에서 `Ctrl+C` 후 명령어를 다시 실행하세요.

---

**🎉 이제 MegaMelange를 쉽게 사용할 수 있습니다!**