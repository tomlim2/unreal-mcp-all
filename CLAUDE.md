# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MegaMelange** (v2.0.0) is an AI-powered creative API hub that enables natural language control of creative tools (Unreal Engine, AI image generation, 3D assets) through a plugin-based architecture. Three components communicate together:

```
Frontend (Next.js :3000) → Python HTTP Bridge (:8080) → UE Plugin (TCP :55557)
```

## Development Commands

### Frontend (Next.js 15.4 + React 19)
```bash
cd Frontend && npm install
npm run dev          # Dev server with Turbopack on :3000
npm run build        # Production build
npm run lint         # ESLint
```

### Python Backend (FastAPI + uvicorn)
```bash
cd Python
uv venv && source .venv/bin/activate    # macOS/Linux
uv pip install -e .
python http_bridge.py                    # HTTP bridge on :8080
```

CLI entry points: `megamelange` or `mm` (defined in pyproject.toml `[project.scripts]`)

### Unreal Engine Plugin (C++ Editor module)
- Open `MCPGameProject/MCPGameProject.uproject`
- Right-click .uproject -> Generate VS project files
- Build in Development Editor configuration
- Plugin auto-starts TCP server on :55557 when editor launches

### Windows Automation
```cmd
script\script-install-packages.bat   # Install all dependencies
script\script-init-ports.bat         # Start all services
script\script-stop-ports.bat         # Kill all services
```

## Architecture

### Python Backend (`Python/`)

**Entry points:**
- `http_bridge.py` -> `api/http/server.py` (ThreadingHTTPServer with decorator-based routing)
- `cli/app.py` (Click CLI, entry: `megamelange`/`mm`)

**Plugin system (`core/`):**
- `plugin_base.py` - `BasePlugin` ABC with `execute_command()`, `ToolCapability` enum, `CommandResult` dataclass
- `registry/tool_registry.py` - Auto-discovers plugins by scanning `tools/` for `metadata.json`, routes commands by capability
- `config.py` - Feature flags loaded from `.env` (FEATURE_PLUGIN_SYSTEM, FEATURE_NANO_BANANA, etc.)
- `session/` - SessionManager for chat history persistence (Supabase or local via StorageFactory)
- `resources/uid_manager.py` - UID generation for images/videos/3D objects

**API layer (`api/http/`):**
- `router.py` - `@route()` decorator maps (method, path) to handlers
- `handlers/` - `nlp_handler.py` (`/api/mcp`), `session_handler.py` (`/api/sessions`), `asset_handler.py`, `tools_handler.py`
- `middleware/` - CORS, tracing, error handling

**Tool plugins (`tools/`):**
- `unreal_engine/` - TCP socket communication to UE plugin. Handlers: actor, light, cesium, screenshot, import_object3d, asset_rename
- `image_generation/nano_banana/` - Google Gemini-powered image gen/style transfer
- `ai/nlp.py` - Main NLP processing (Claude/Gemini parses natural language -> structured commands)
- `ai/orchestrator.py` - Multi-step workflow coordination with dependency resolution
- `ai/model_providers/` - LLM adapters (Claude, Gemini, OpenAI)

Each plugin has `metadata.json` + `plugin.py` implementing `BasePlugin`.

### Frontend (`Frontend/src/app/`)

- `api/` - Next.js API routes proxying to Python backend (`/api/mcp`, `/api/sessions`, `/api/tools`, `/api/screenshot/[file]`, `/api/3d-object/[uid]`)
- `app/[section-id]/` - Main app page with session sidebar + content area
- `services/ApiServiceContext.ts` - HTTP client factory wrapping all backend calls
- `stores/sessionImagesStore.ts` - Zustand state store
- `components/` - Chat, Sidebar, ToolSelector, Modal components

### UE Plugin (`MCPGameProject/Plugins/MegaMelange/`)

- `MegaMelangeBridge` (UEditorSubsystem) - TCP server + command dispatcher
- `MCPServerRunnable` - Separate thread for TCP listener
- `Commands/` - Modular command handlers: Actor, Light, Rendering, Asset, Blueprint, BlueprintNode, Object3D, CommonUtils
- Protocol: JSON over TCP. Request `{command_type, params}` -> Response `{success, result}`
- Build dependencies: Core, Sockets, Json, UnrealEd, EditorSubsystem, AssetRegistry, BlueprintGraph

## Request Lifecycle

1. User sends natural language -> Frontend `/api/mcp` -> Python `tools/ai/nlp.py`
2. LLM (Claude/Gemini) parses intent into structured command(s)
3. `ToolRegistry` routes command to matching plugin by capability
4. Plugin executes (e.g., UE plugin sends JSON over TCP to port 55557)
5. Response flows back through the chain; assets served via UID-based endpoints

## Environment Setup

**Required:** `GOOGLE_API_KEY` in `Python/.env`

Key env vars (see `Python/.env.example`):
- `ANTHROPIC_API_KEY` - Alternative LLM
- `HTTP_BRIDGE_PORT` - Backend port (default 8080)
- `UNREAL_PROJECT_PATH` - UE project directory
- `UNREAL_TCP_HOST/PORT` - TCP bridge (default 127.0.0.1:55557)
- `SUPABASE_URL/KEY` - Session storage

Frontend env (`Frontend/.env.local`):
- `MCP_HTTP_BRIDGE_URL` - Backend URL (default http://127.0.0.1:8080)

## Version Locations

When bumping versions, update all four files:
1. `MCPGameProject/Plugins/MegaMelange/MegaMelange.uplugin` - `Version` + `VersionName`
2. `Python/pyproject.toml` - `version`
3. `Python/cli/app.py` - `@click.version_option(version=...)`
4. `Frontend/package.json` - `version`
