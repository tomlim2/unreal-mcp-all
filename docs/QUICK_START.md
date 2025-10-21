# MegaMelange Standalone App - Quick Start Guide

## 현재 상태 ✅

모든 설정 파일이 준비되었습니다! 이제 Rust만 설치하면 빌드할 수 있습니다.

### 완료된 작업
- ✅ Python 백엔드 빌드 시스템 (PyInstaller)
- ✅ Tauri 데스크톱 앱 설정
- ✅ Next.js Static Export 설정
- ✅ 백엔드 자동 시작 로직
- ✅ 앱 아이콘 설정
- ✅ 통합 빌드 스크립트
- ✅ Tauri CLI 설치

### 남은 작업
- ⏳ **Rust 설치** (사용자 직접 설치 필요)

---

## Rust 설치 (10-15분)

### Step 1: Rust 다운로드 및 설치

1. **웹사이트 열기**:
   ```
   https://rustup.rs/
   ```

2. **rustup-init.exe 다운로드**
   - 웹사이트에서 자동으로 Windows용 설치 파일 제공
   - 클릭하여 다운로드

3. **실행 및 설치**
   ```
   rustup-init.exe 실행
   → 화면에 나오는 옵션 선택:

   1) Proceed with standard installation (default - just press enter)

   → Enter 키 또는 1 입력
   ```

4. **설치 완료 대기**
   - Visual Studio C++ Build Tools 설치 (자동)
   - 약 5-10분 소요

5. **터미널 재시작** ⚠️ 중요!
   - 모든 PowerShell/CMD 창 닫기
   - 새로운 터미널 열기

### Step 2: 설치 확인

새 터미널에서:
```cmd
rustc --version
cargo --version
```

버전이 표시되면 성공! ✅

---

## 빌드 실행 (자동)

Rust 설치 후:

```cmd
cd D:\vs\unreal-mcp\unreal-mcp
INSTALL_AND_BUILD.bat
```

이 스크립트는 자동으로:
1. Rust 설치 확인
2. Python 백엔드 빌드 (`MegaMelangeBackend.exe`)
3. Next.js 프론트엔드 빌드
4. Tauri 데스크톱 앱 빌드
5. Windows Installer (MSI) 생성

**예상 소요 시간**: 15-25분 (첫 빌드)

---

## 빌드 결과물

성공하면:

```
✅ Frontend\src-tauri\target\release\megamelange-desktop.exe
   → 실행 파일 (~10-15 MB)

✅ Frontend\src-tauri\target\release\bundle\msi\
   → Windows 설치 프로그램 (MSI)
```

---

## 수동 빌드 (단계별)

자동 스크립트 대신 단계별로 빌드하려면:

### 1. Python 백엔드
```cmd
cd Python
build_backend.bat
```

### 2. Frontend 빌드
```cmd
cd ..\Frontend
npm run build
```

### 3. Tauri 앱 빌드
```cmd
npm run tauri:build
```

---

## 개발 모드 테스트

빌드 전에 테스트하려면:

```cmd
# 터미널 1: 백엔드 실행
cd Python\dist
MegaMelangeBackend.exe

# 터미널 2: Tauri 개발 모드
cd Frontend
npm run tauri:dev
```

---

## 문제 해결

### "rustc: command not found"
→ 터미널을 재시작하지 않았습니다
→ 모든 터미널 창을 닫고 새로 열기

### Visual Studio Build Tools 에러
→ Build Tools for Visual Studio 2022 설치 필요
→ https://visualstudio.microsoft.com/downloads/
→ "Desktop development with C++" 워크로드 선택

### PyInstaller 에러
```cmd
pip install --upgrade pyinstaller
```

### Tauri 빌드 에러
```cmd
cd Frontend\src-tauri
cargo clean
cd ..\..
```
그 다음 다시 빌드 시도

### "Backend not found" 런타임 에러
→ `MegaMelangeBackend.exe`가 빌드되었는지 확인
→ `Python\dist\` 폴더 확인

---

## 다음 단계

빌드가 성공하면:

1. **테스트**:
   ```cmd
   Frontend\src-tauri\target\release\megamelange-desktop.exe
   ```

2. **설치 프로그램 사용**:
   ```cmd
   Frontend\src-tauri\target\release\bundle\msi\
   ```
   → MSI 파일 실행하여 설치

3. **배포**:
   - `.exe` 파일과 UnrealMCP 플러그인을 ZIP으로 패키징
   - 사용자에게 배포

---

## 도움이 필요하면

- **Rust 설치 문제**: `RUST_INSTALL_GUIDE.md` 참고
- **전체 빌드 가이드**: `BUILD_STANDALONE_APP.md` 참고
- **GitHub Issues**: https://github.com/chongdashu/unreal-mcp/issues

---

## 요약

```
1. Rust 설치 (https://rustup.rs/)
2. 터미널 재시작
3. INSTALL_AND_BUILD.bat 실행
4. 15-25분 대기
5. 완료! 🎉
```
