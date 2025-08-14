# Refactored Architecture Setup

The LLM integration has been successfully moved from the Frontend to the Python MCP Server for better architecture and performance.

## Changes Made

### ✅ Python MCP Server
- Added `anthropic>=0.59.0` dependency to `pyproject.toml`
- Created `tools/nlp_tools.py` with `process_natural_language` tool
- Updated `unreal_mcp_server.py` to register NLP tools
- Enhanced `http_bridge.py` to handle natural language requests

### ✅ Frontend
- Simplified `api/openai/route.ts` to proxy requests to Python server
- Removed Anthropic SDK dependency from `package.json`
- Updated UI text to reflect new architecture

## Setup Instructions

### 1. Install Python Dependencies
```bash
cd Python
uv pip install -e .
```

### 2. Set Environment Variable
Set your Anthropic API key:
```bash
# Windows
set ANTHROPIC_API_KEY=your-api-key-here

# Linux/Mac
export ANTHROPIC_API_KEY=your-api-key-here
```

### 3. Start HTTP Bridge
```bash
cd Python
python http_bridge.py
```
*Runs on http://127.0.0.1:8080*

### 4. Install Frontend Dependencies
```bash
cd Frontend
npm install
```

### 5. Start Frontend
```bash
cd Frontend
npm run dev
```
*Runs on http://localhost:3000*

## Architecture Flow

```
Browser → Frontend → Python MCP Server (LLM) → Unreal Engine
```

**Before**: `Frontend (LLM) → Python MCP Server → Unreal Engine`
**After**: `Frontend → Python MCP Server (LLM) → Unreal Engine`

## Benefits

- ✅ Single LLM instance with direct access to Unreal tools
- ✅ Reduced API costs and network latency
- ✅ Centralized intelligence in MCP server
- ✅ Simpler frontend implementation
- ✅ Better context awareness for command generation

## Testing

Run the integration test:
```bash
cd Python
uv run python simple_test.py
```

## API Endpoints

### Frontend API
- `POST /api/openai` - Accepts `{prompt, context}` and forwards to Python server

### Python HTTP Bridge
- `POST http://127.0.0.1:8080` - Processes natural language via `{prompt, context}`
- Legacy support: `POST http://127.0.0.1:8080` - Direct commands via `{type, params}`

The refactoring is complete and maintains full backward compatibility while providing the improved architecture!