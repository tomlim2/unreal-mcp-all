# 🚀 MegaMelange 시작 가이드

MegaMelange는 AI로 언리얼 엔진을 제어할 수 있는 도구입니다. 이 가이드를 따라하면 **웹 브라우저에서 자연어로 언리얼 엔진을 조작**할 수 있습니다.

## 📋 시작하기 전 확인사항

> ⚠️ **중요**: 아래 모든 항목이 설치되어 있어야 합니다!

- [ ] **Python 3.10 이상** - [python.org](https://python.org)에서 다운로드
- [ ] **Node.js 18 이상** - [nodejs.org](https://nodejs.org)에서 다운로드  
- [ ] **uv 패키지 매니저** - 터미널에서 `pip install uv` 실행
- [ ] **언리얼 엔진 5.3 이상** - Epic Games Launcher에서 설치
- [ ] **UnrealMCP 플러그인**이 활성화된 언리얼 프로젝트

### 설치 확인 방법
```bash
# 각각 실행해서 버전이 나오는지 확인
python --version    # Python 3.10.0 이상
node --version      # v18.0.0 이상  
npm --version       # 8.0.0 이상
uv --version        # 0.1.0 이상
```

## 🎯 4단계 빠른 시작

### 1단계: 언리얼 엔진 프로젝트 열기
1. **언리얼 엔진 5.3+** 프로젝트 열기 
2. **편집 → 플러그인 → UnrealMCP** 플러그인이 **체크되어 있는지** 확인
3. 프로젝트를 **열어둔 상태로** 다음 단계 진행

---

### 2단계: Python MCP 서버 실행
> 📂 **첫 번째 터미널** 창에서 실행

```bash
# 1️⃣ Python 폴더로 이동
cd Python

# 2️⃣ 가상환경 생성
uv venv

# 3️⃣ 가상환경 활성화 (Windows)
.venv\Scripts\activate
# Mac/Linux인 경우: source .venv/bin/activate

# 4️⃣ 필요한 라이브러리 설치
uv pip install -e .

# 5️⃣ 서버 시작 (이 명령어가 성공하면 2단계 완료!)
.venv\Scripts\python.exe unreal_mcp_server.py
```

✅ **성공 메시지**: `Starting MCP server with stdio transport` 가 보이면 성공!

---

### 3단계: HTTP 브리지 실행 (웹 인터페이스용 - 필수!)
> 📂 **두 번째 터미널** 창에서 실행 (첫 번째 터미널은 그대로 둡니다)

> ⚠️ **중요**: 이 단계를 빼먹으면 웹사이트에서 "MCP Bridge error" 가 나타납니다!

```bash
# 1️⃣ Python 폴더로 이동  
cd Python

# 2️⃣ 가상환경 활성화 (Windows)
.venv\Scripts\activate
# Mac/Linux인 경우: source .venv/bin/activate

# 3️⃣ HTTP 브리지 서버 시작
.venv\Scripts\python.exe http_bridge.py
```

✅ **성공 메시지**: `MCP HTTP Bridge started on http://127.0.0.1:8080` 이 보이면 성공!

---

### 4단계: 웹 프론트엔드 실행  
> 📂 **세 번째 터미널** 창에서 실행 (앞의 두 터미널은 그대로 둡니다)

```bash
# 1️⃣ Frontend 폴더로 이동
cd Frontend

# 2️⃣ Node.js 패키지 설치
npm install

# 3️⃣ 개발 서버 시작
npm run dev
```

✅ **성공 확인**: 브라우저에서 `http://localhost:3000` 접속해서 채팅창이 보이면 완료!

---

## 🎉 축하합니다! 설정 완료

모든 단계가 성공했다면:
- ✅ 언리얼 엔진이 열려있음
- ✅ Python MCP 서버가 실행중 (첫 번째 터미널)  
- ✅ HTTP 브리지가 실행중 (두 번째 터미널)
- ✅ 웹 프론트엔드가 실행중 (세 번째 터미널)
- ✅ 웹 브라우저에 채팅 인터페이스가 보임

이제 **"큐브 하나 만들어줘"** 같은 자연어 명령을 입력해보세요!

## 🔧 문제해결 가이드

### 😵 "Python 서버가 안 켜져요!"

**문제 1: `python: command not found`**
```bash
# 해결방법: Python이 제대로 설치되었는지 확인
python --version
# 안 되면 python3 시도
python3 --version
```

**문제 2: `uv: command not found`**
```bash
# 해결방법: uv 설치
pip install uv
# 또는
pip3 install uv
```

**문제 3: 포트 55557이 이미 사용중**
```bash
# Windows에서 기존 Python 프로세스 모두 종료
tasklist | findstr python
taskkill /F /IM python.exe
```

---

### 😵 "웹사이트가 안 열려요!"

**문제 1: `npm: command not found`**
- Node.js가 제대로 설치되지 않음
- [nodejs.org](https://nodejs.org)에서 다시 설치

**문제 2: 포트 3000이 사용중**
```bash
# 다른 포트로 실행
npm run dev -- --port 3001
# 그리고 http://localhost:3001 접속
# 그리고 언리얼 WB_Webinterface의 Web Browser 컴포넌트 Initial URL 변수 http://localhost:3001로 변경
```

**문제 3: "Cannot GET /" 에러**
- 브라우저에서 `http://localhost:3000` 정확히 입력했는지 확인
- `https://`가 아니라 `http://`임에 주의

**문제 4: "MCP Bridge error: fetch failed" 에러**
```bash
# 해결방법: HTTP 브리지가 실행되지 않음
cd Python
.venv\Scripts\activate
.venv\Scripts\python.exe http_bridge.py
# 8080 포트에서 HTTP 브리지가 실행되어야 함
```

---

### 😵 "언리얼 엔진과 연결이 안 되요!"

**가장 흔한 실수들:**
1. **언리얼 엔진 프로젝트를 안 열고 시작** → 먼저 프로젝트를 열어야 함
2. **UnrealMCP 플러그인 비활성화** → 편집→플러그인→UnrealMCP 체크 확인  
3. **방화벽 차단** → Windows 방화벽에서 Python 허용

**연결 상태 확인 방법:**
```bash
# 포트 55557이 열려있는지 확인
netstat -ano | findstr :55557
```

---

## 📚 심화

### 🤖 AI 명령어 예시들
웹 브라우저 채팅창에서 이런 명령들을 시도해보세요:

```
조명과 환경:
- "하늘을 저녁노을로 바꿔줘"
- "포인트 라이트를 추가해줘"
- "낮 시간을 오후 3시로 설정해줘"
```

### 🔍 시스템 구조 이해하기

이 프로젝트는 **3개의 프로그램**이 함께 작동합니다:

1. **언리얼 엔진** (포트 55557) - 실제 3D 작업을 하는 프로그램
2. **Python MCP 서버** - AI 명령을 언리얼 엔진이 이해할 수 있게 번역
3. **Next.js 웹 프론트엔드** (포트 3000) - 사용자가 명령을 입력하는 웹사이트

### 📁 프로젝트 구조
```
unreal-mcp/
├── Python/           # MCP 서버 코드
├── Frontend/         # 웹 인터페이스
├── MCPGameProject/   # 언리얼 엔진 프로젝트
└── README_HowToStart_Korean.md  # 이 파일
```

---

## 🛑 작업 종료하기

### 정상적으로 종료하기
1. **웹 브라우저** 탭 닫기
2. **두 번째 터미널** (Frontend): `Ctrl + C` 누르기  
3. **첫 번째 터미널** (Python): `Ctrl + C` 누르기
4. **언리얼 엔진** 프로젝트 닫기

### 강제로 모든 프로세스 종료 (문제가 생겼을 때)
```bash
# 모든 Python과 Node 프로세스를 한번에 종료
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

---

## 💡 팁

### 자주 하는 실수 Top 5:
1. **언리얼 엔진을 안 열고 시작** (가장 많음)
2. **터미널을 하나만 사용해서 명령어 충돌**
3. **가상환경 활성화를 깜빡함** 
4. **http://를 https://로 잘못 입력**
5. **방화벽으로 인한 포트 차단**

### 빠른 상태 점검 명령어:
```bash
# 모든 필요한 프로세스가 실행중인지 확인
tasklist | findstr "python.exe node.exe UnrealEditor.exe"

# 모든 필요한 포트가 열려있는지 확인  
netstat -ano | findstr "55557 3000"
```

---

## 📞 도움이 더 필요하다면

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **프로젝트 문서**: `CLAUDE.md` 파일 참조  
- **로그 파일**: `Python/unreal_mcp.log` 에러 메시지 확인