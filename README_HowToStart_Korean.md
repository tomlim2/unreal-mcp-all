# 🚀 MegaMelange 설치 가이드

MegaMelange는 웹 브라우저에서 언리얼 엔진을 조작할 수 있는 도구입니다.

## 📋 필요한 프로그램들

> ⚠️ **반드시 설치해야 하는 것들**

- [ ] **Python 3.10 이상** - [python.org](https://python.org)
- [ ] **Node.js 18 이상** - [nodejs.org](https://nodejs.org)
- [ ] **언리얼 엔진 5.3** - Epic Games Launcher에서 설치 (5.4, 5.5는 지원 안함)

### 설치 확인
```bash
python --version
node --version
```

## 🚀 자동 실행 (추천)

### 1단계: 자동 설치
```bash
# 프로젝트 폴더에서 실행
init-install-packages.bat
```

### 2단계: 언리얼 엔진 프로젝트 열기
**MCPGameProject/MCPGameProject.uproject** 파일을 더블클릭해서 열기

### 3단계: 자동 시작
```bash
# script 폴더에서 실행
script\script-init-ports.bat
```
✅ **성공**: 3개 명령창이 자동으로 열리고 브라우저에서 `http://localhost:3000` 접속

---

**자동 실행 실패시 수동 실행으로 진행하세요** ⬇️

## 🔧 수동 실행

### 1단계: 언리얼 엔진 프로젝트 열기
**MCPGameProject/MCPGameProject.uproject** 파일을 더블클릭해서 열기

### 2단계: Python 서버 실행
**첫 번째 명령창**에서:
```bash
cd Python
pip install uv
uv venv
.venv\Scripts\activate
uv pip install -e .
.venv\Scripts\python.exe unreal_mcp_server.py
```
✅ **성공**: `Starting MCP server` 메시지가 보이면 성공

### 3단계: 웹 브리지 실행
**두 번째 명령창**에서:
```bash
cd Python
.venv\Scripts\activate
.venv\Scripts\python.exe http_bridge.py
```
✅ **성공**: `started on http://127.0.0.1:8080` 메시지가 보이면 성공

### 4단계: 웹사이트 실행
**세 번째 명령창**에서:
```bash
cd Frontend
npm install
npm run dev
```
✅ **성공**: 브라우저에서 `http://localhost:3000` 접속해서 채팅창이 보이면 완료

## 🎉 테스트하기

모든 단계가 성공했다면:
- ✅ 언리얼 엔진 열려있음
- ✅ 명령창 3개 실행중
- ✅ 웹 브라우저에 채팅창 보임

**테스트 명령어:**
- "스크린샷 찍어줘" ✅
- "시간을 저녁으로 바꿔줘" ✅
- "조명을 따뜻하게 만들어줘" ✅
- "지도를 도쿄로 이동해줘" ✅

## 🔧 문제해결

### Python 서버 문제
```bash
# Python이 없다고 나올 때
python --version
# 안되면 Microsoft Store에서 Python 설치

# uv가 없다고 나올 때
pip install uv

# 포트가 사용중이라고 나올 때
taskkill /F /IM python.exe
```

### 웹사이트 문제
```bash
# Node.js가 없다고 나올 때
# nodejs.org에서 다시 설치

# 포트 3000이 사용중일 때
npm run dev -- --port 3001
# 그리고 http://localhost:3001 접속

# "MCP Bridge error" 나올 때
# 3단계 웹 브리지가 실행되지 않은 것
```

### 언리얼 엔진 문제
- **가장 흔한 실수**: 언리얼 엔진 프로젝트를 열지 않고 시작
- **해결방법**: MCPGameProject.uproject 파일을 먼저 열기
- **플러그인 확인**: 편집 → 플러그인 → UnrealMCP 체크

## 🛑 종료하기

1. 웹 브라우저 닫기
2. 명령창 3개에서 각각 `Ctrl + C` 누르기
3. 언리얼 엔진 닫기

**강제 종료:**
```bash
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```