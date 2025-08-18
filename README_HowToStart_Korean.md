# MegaMelange 시작 가이드

이 가이드는 MegaMelange AI 기반 언리얼 엔진 개발 도구의 Python MCP 서버와 Next.js 프론트엔드를 시작하는 방법을 안내합니다.

## 사전 요구사항

- **Python 3.10+** 설치
- **Node.js 18+** 및 npm 설치
- Python용 **uv** 패키지 매니저 (`pip install uv`)
- **언리얼 엔진 5.3+** 및 UnrealMCP 플러그인이 활성화된 프로젝트

## 빠른 시작 명령어

### 1. Python MCP 서버 설정

```bash
# Python 디렉토리로 이동
cd Python

# 가상환경 생성 및 활성화
uv venv
# Windows에서:
.venv\Scripts\activate
# Unix/Mac에서:
source .venv/bin/activate

# 개발 모드로 종속성 설치
uv pip install -e .

# MCP 서버 시작
python unreal_mcp_server.py
```

### 2. 프론트엔드 설정

```bash
# Frontend 디렉토리로 이동
cd Frontend

# 종속성 설치
npm install

# 개발 서버 시작
npm run dev
```

### 3. 선택사항: HTTP 브리지

추가 API 접근을 위해 HTTP 브리지가 필요한 경우:

```bash
# Python 디렉토리에서 (별도 터미널)
cd Python
.venv\Scripts\python.exe http_bridge.py
```

## 상세 시작 프로세스

### Python MCP 서버

Python MCP 서버는 언리얼 엔진 통신을 위한 Model Context Protocol 인터페이스를 제공합니다.

1. **환경 설정**
   ```bash
   cd Python
   uv venv                    # .venv 디렉토리 생성
   ```

1.5. **환경 구성**
   `.env` 파일 생성:
   ```
   ANTHROPIC_API_KEY=your_openai_api_key_here
   ```

2. **패키지 설치**
   ```bash
   uv pip install -e .       # FastMCP, Pydantic 등 모든 종속성 설치
   ```

3. **서버 시작**
   ```bash
   python unreal_mcp_server.py
   ```
   
   서버는 다음과 같은 작업을 수행합니다:
   - MCP 연결 대기
   - 포트 55557에서 언리얼 엔진과 TCP 연결 설정
   - 모든 도구 모듈 등록 (액터, 블루프린트, 에디터, 노드 도구)

### Next.js 프론트엔드

프론트엔드는 언리얼 엔진의 자연어 제어를 위한 웹 인터페이스를 제공합니다.

1. **설정**
   ```bash
   cd Frontend
   npm install               # Next.js 15.4+, React 19, TypeScript 설치
   ```

2. **개발 서버 시작**
   ```bash
   npm run dev              # http://localhost:3000에서 시작
   ```

## 서버 상태 확인

### Python 서버 실행 확인
```bash
# 포트 55557 사용 확인
netstat -ano | findstr :55557

# Python 프로세스 확인
tasklist | findstr python
```

### 프론트엔드 상태 확인
- 브라우저에서 `http://localhost:3000` 열기
- MegaMelange 채팅 인터페이스가 보여야 함

## 문제 해결

### Python 서버 문제

**포트 55557이 이미 사용 중:**
```bash
# 기존 프로세스 종료
powershell "Get-Process python | Stop-Process -Force"
```

**FastMCP 초기화 오류:**
- 최신 버전 사용 확인: `uv pip install --upgrade fastmcp`
- FastMCP 생성자에 지원되지 않는 매개변수가 전달되지 않는지 확인

**언리얼 엔진 연결 실패:**
- 언리얼 엔진 프로젝트가 열려있는지 확인
- UnrealMCP 플러그인이 프로젝트에서 활성화되어 있는지 확인
- 방화벽이 포트 55557을 차단하지 않는지 확인

### 프론트엔드 문제

**포트 3000이 이미 사용 중:**
```bash
npm run dev -- --port 3001  # 다른 포트 사용
```

**OpenAI API 오류:**
- `.env.local`에 `OPENAI_API_KEY`가 설정되어 있는지 확인
- API 키에 충분한 크레딧이 있는지 확인

**빌드 오류:**
```bash
npm run build              # TypeScript/빌드 문제 확인
npm run lint               # 린팅 문제 확인
```

## 프로덕션 배포

### Python 서버
```bash
# 프로덕션 종속성 설치
uv pip install --no-dev

# 프로덕션 설정으로 실행
python unreal_mcp_server.py --production
```

### 프론트엔드
```bash
# 프로덕션용 빌드
npm run build

# 프로덕션 서버 시작
npm run start
```

## 개발 워크플로우

1. **언리얼 엔진 시작** - 프로젝트와 UnrealMCP 플러그인 활성화
2. **Python MCP 서버 시작** - 하나의 터미널에서
3. **프론트엔드 시작** - 다른 터미널에서
4. **선택사항: HTTP 브리지 시작** - 필요시 세 번째 터미널에서
5. `http://localhost:3000`에서 웹 인터페이스 접속

## 사용 가능한 도구 카테고리

MCP 서버는 카테고리별로 구성된 도구들을 제공합니다:

- **액터 도구**: 언리얼 엔진에서 액터 생성, 조작, 쿼리
- **블루프린트 도구**: 블루프린트 생성, 컴포넌트 추가, 블루프린트 컴파일
- **노드 도구**: 블루프린트 노드 그래프 및 연결 조작
- **에디터 도구**: 뷰포트, 카메라, 에디터 설정 제어
- **다이나믹 스카이 도구**: 하늘과 조명 시스템을 위한 전문 도구

## 로그 및 디버깅

- **Python 서버 로그**: `Python/unreal_mcp.log` 확인
- **프론트엔드 로그**: 브라우저 콘솔 및 터미널 출력 확인
- **언리얼 엔진 로그**: UE 에디터의 Output Log 창 확인

## 서비스 중지

모든 서비스를 깔끔하게 종료하려면:

```bash
# 모든 Python 프로세스 종료
powershell "Get-Process python | Stop-Process -Force"

# 프론트엔드 중지 (터미널에서 Ctrl+C)
# 또는 Node 프로세스 종료
powershell "Get-Process node | Stop-Process -Force"
```