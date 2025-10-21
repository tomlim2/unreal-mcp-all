# Rust 설치 가이드 (Windows)

MegaMelange Standalone App 빌드를 위해서는 Rust가 필요합니다.

## 설치 단계

### 1. Rust 설치 (10-15분)

1. **Rust 공식 사이트** 방문:
   ```
   https://rustup.rs/
   ```

2. **rustup-init.exe 다운로드 & 실행**
   - 웹사이트에서 자동으로 Windows용 설치 파일 제공
   - 다운로드 후 실행

3. **설치 옵션 선택**
   ```
   1) Proceed with standard installation (default - just press 1)
   ```
   - 그냥 `1` 누르고 Enter (기본 설치 옵션)

4. **설치 완료 대기**
   - Visual Studio C++ Build Tools가 필요하다고 나오면 설치 진행
   - 약 5-10분 소요

5. **설치 확인**
   ```cmd
   rustc --version
   cargo --version
   ```
   - 버전이 표시되면 성공!

### 2. Visual Studio C++ Build Tools 설치 (필요 시)

Rust 설치 중에 요구되거나, 따로 설치가 필요할 수 있습니다.

1. **다운로드**:
   ```
   https://visualstudio.microsoft.com/downloads/
   ```
   - "Build Tools for Visual Studio 2022" 선택

2. **설치 옵션**:
   - ✅ "Desktop development with C++" 체크
   - 기본 옵션으로 설치

### 3. 터미널 재시작

설치 완료 후 **모든 터미널/PowerShell/CMD 창을 닫고 다시 열어야** PATH가 업데이트됩니다.

---

## 다음 단계: Tauri 초기화

Rust 설치가 완료되면:

```cmd
cd D:\vs\unreal-mcp\unreal-mcp\Frontend

# Tauri CLI 설치 (package.json에 이미 추가되어 있음)
npm install

# 개발 모드로 테스트
npm run tauri:dev

# 프로덕션 빌드
npm run tauri:build
```

---

## 문제 해결

### "rustc: command not found" 에러
→ 터미널을 재시작하지 않았거나, Rust가 제대로 설치되지 않음
→ PATH 확인: `echo %PATH%` (Windows)에서 `.cargo\bin` 경로 있는지 확인

### Visual Studio Build Tools 관련 에러
→ Build Tools for Visual Studio 2022 설치 필요
→ "Desktop development with C++" 워크로드 선택

### Tauri 빌드 실패
→ `cargo clean` 실행 후 다시 빌드
→ `rustup update` 로 Rust 최신 버전으로 업데이트

---

## 도움말

- **Rust 공식 문서**: https://www.rust-lang.org/learn/get-started
- **Tauri 문서**: https://tauri.app/start/
- **GitHub Issues**: https://github.com/chongdashu/unreal-mcp/issues
