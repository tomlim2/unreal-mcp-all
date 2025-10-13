# MegaMelange Standalone App 빌드 가이드

## 완료된 작업 ✅

### Phase 1: Python 백엔드 패키징
- ✅ `Python/build_backend.spec` - PyInstaller 설정
- ✅ `Python/build_backend.bat` - 빌드 스크립트
- ✅ `Python/dist/MegaMelangeBackend.exe` - 49.6MB 실행파일 생성
- ✅ `.gitignore` 업데이트

### Phase 2: Tauri 데스크톱 앱 설정
- ✅ `Frontend/next.config.ts` - Static export 설정
- ✅ `Frontend/package.json` - Tauri 스크립트 추가
- ✅ `Frontend/src-tauri/Cargo.toml` - Rust 종속성
- ✅ `Frontend/src-tauri/tauri.conf.json` - Tauri 설정
- ✅ `Frontend/src-tauri/src/main.rs` - 백엔드 자동 시작 로직
- ✅ `Frontend/src-tauri/icons/icon.png` - 앱 아이콘
- ✅ `RUST_INSTALL_GUIDE.md` - Rust 설치 가이드

---

## 빌드 방법

### 필수 사전 조건
1. **Rust 설치** (Phase 2 필수)
   - `RUST_INSTALL_GUIDE.md` 참고
   - 설치 후 터미널 재시작

2. **Node.js & Python 환경**
   - Node.js 18+
   - Python 3.10+
   - `npm install` 완료

---

## 빌드 단계

### 1. Python 백엔드 빌드

```cmd
cd Python
build_backend.bat
```

**결과**: `Python/dist/MegaMelangeBackend.exe` 생성 (49.6MB)

---

### 2. Tauri 앱 빌드

```cmd
cd Frontend

# 1) Tauri CLI 설치 (처음 한 번만)
npm install --save-dev @tauri-apps/cli

# 2) 빌드
npm run tauri:build
```

**결과**:
- `Frontend/src-tauri/target/release/megamelange-desktop.exe`
- `Frontend/src-tauri/target/release/bundle/msi/` (Windows Installer)

---

### 3. 백엔드 Sidecar 복사 (수동)

Tauri가 백엔드를 자동으로 시작하도록 하려면:

```cmd
# Backend를 Tauri 리소스 폴더에 복사
copy Python\dist\MegaMelangeBackend.exe Frontend\src-tauri\target\release\
```

또는 `tauri.conf.json`에 sidecar 설정 추가:

```json
"bundle": {
  "resources": [
    "../../Python/dist/MegaMelangeBackend.exe"
  ]
}
```

---

## 개발 모드 테스트

```cmd
cd Frontend

# 1) 백엔드 수동 시작 (별도 터미널)
cd ../Python/dist
MegaMelangeBackend.exe

# 2) Tauri 개발 모드
cd ../../Frontend
npm run tauri:dev
```

---

## 다음 단계: Phase 3 & 4

### Phase 3: GUI 설정 페이지 (예정)
- [ ] Settings Modal 컴포넌트
- [ ] API 키 입력 폼 (Google 필수, Anthropic/OpenAI 옵션)
- [ ] Tauri Store를 사용한 안전한 저장

### Phase 4: 통합 빌드 스크립트 (예정)
- [ ] `build-standalone.bat` - 모든 단계 자동화
- [ ] 배포 패키지 생성 (ZIP)
- [ ] UnrealMCP 플러그인 포함

---

## 현재 상태

**완료된 Phase**: 1, 2
**남은 Phase**: 3, 4

**수동 빌드 가능**: ✅ 예 (위의 단계 따라하기)
**자동 빌드 스크립트**: ❌ 아직 없음 (Phase 4에서 생성 예정)

---

## 문제 해결

### Rust 관련
→ `RUST_INSTALL_GUIDE.md` 참고

### PyInstaller 에러
```cmd
pip install --upgrade pyinstaller
```

### Tauri 빌드 에러
```cmd
cd Frontend/src-tauri
cargo clean
cd ../..
npm run tauri:build
```

### "Backend not found" 에러
→ `MegaMelangeBackend.exe`가 올바른 위치에 있는지 확인
→ Sidecar 설정 확인

---

## 참고 문서

- **Tauri 공식 문서**: https://tauri.app/
- **PyInstaller 문서**: https://pyinstaller.org/
- **프로젝트 README**: `README.md`
