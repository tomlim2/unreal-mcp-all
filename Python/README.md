# Unreal MCP

Python bridge for interacting with Unreal Engine 5.5 using the Model Context Protocol (MCP).

## Setup

1. Make sure Python 3.10+ is installed
2. Install `uv` if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```
4. Install dependencies:
   ```bash
   uv pip install -e .
   ```

At this point, you can configure your MCP Client (Claude Desktop, Cursor, Windsurf) to use the Unreal MCP Server as per the [Configuring your MCP Client](README.md#configuring-your-mcp-client).

## Testing Scripts

테스트 스크립트들이 `scripts` 폴더에 카테고리별로 정리되어 있습니다. 이 스크립트들은 도구와 Unreal Bridge를 직접 연결을 통해 테스트하는 데 유용합니다. 즉, MCP 서버를 실행할 필요가 없습니다.

### 테스트 카테고리 구조

```
scripts/
├── actors/          # 액터 관련 테스트
├── blueprints/      # 블루프린트 관련 테스트
├── sky/            # 스카이/날씨 관련 테스트
├── node/           # 노드/컴포넌트 관련 테스트
└── tests/          # 기타 통합 테스트
```

### 테스트 관리 사용법

테스트는 `scripts` 폴더에 카테고리별로 정리되어 있으며, Python으로 직접 실행할 수 있습니다:

```bash
# 특정 테스트 실행
cd scripts/actors
python test_get_actors.py

# 카테고리별 테스트 실행
cd scripts/sky  
python test_time_of_day.py
```

### MCP 서버를 통한 테스트 도구

MCP 서버가 실행 중일 때 다음 도구들을 사용할 수 있습니다:

- `list_test_categories()` - 사용 가능한 테스트 카테고리 목록
- `list_tests_in_category(category)` - 특정 카테고리의 테스트 목록
- `run_test_file(test_path)` - 특정 테스트 파일 실행
- `run_category_tests(category)` - 카테고리의 모든 테스트 실행
- `get_test_summary()` - 전체 테스트 구조 요약
- `create_test_file(category, test_name, template)` - 새 테스트 파일 생성

### 새 테스트 만들기

새 테스트를 만들려면:

1. 적절한 카테고리 폴더에 `test_*.py` 파일 생성
2. 또는 MCP 서버를 통해 `create_test_file()` 도구 사용

테스트 파일은 표준 Python 스크립트 형태이며, 성공 시 exit code 0, 실패 시 1을 반환해야 합니다.

**중요**: 스크립트가 작동하려면 의존성을 설치하고/또는 `uv` 가상 환경에서 실행해야 합니다.


## Troubleshooting

- Make sure Unreal Engine editor is loaded loaded and running before running the server.
- Check logs in `unreal_mcp.log` for detailed error information

## Development

To add new tools, modify the `UnrealMCPBridge.py` file to add new command handlers, and update the `unreal_mcp_server.py` file to expose them through the HTTP API. 