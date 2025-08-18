# Unreal MCP Frontend

A Next.js frontend for the Unreal Engine MCP (Model Context Protocol) server, featuring AI-powered natural language commands via MCP bridge.

## Features

- 🤖 **MCP Integration**: Convert natural language to Unreal Engine commands via Python MCP server
- 🎮 **Unreal Engine Control**: Interface with dynamic sky, actors, blueprints
- ⚡ **Real-time Commands**: Execute commands and see results immediately
- 🎨 **Modern UI**: Clean, responsive interface with example prompts
- 🔧 **HTTP Bridge**: Connects to your Python MCP HTTP bridge server

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start Python MCP HTTP Bridge** (required):
   Make sure the HTTP bridge is running on port 8080:
   ```bash
   cd ../Python
   python http_bridge.py
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open browser**: http://localhost:3000

## Usage

### Example Prompts
- "Set the time to sunrise (6 AM)"
- "Create a cube actor at position 0,0,100"
- "Show me all actors in the current level"
- "Set the sky to sunset time"
- "Delete the actor named 'TestCube'"

### Available Commands
The AI can generate these Unreal MCP commands:
- `get_time_of_day` - Get current time from Ultra Dynamic Sky
- `set_time_of_day` - Set time (0-24 hours)
- `get_actors_in_level` - List all actors
- `create_actor` - Create new actors
- `delete_actor` - Delete actors by name
- `set_actor_transform` - Move/rotate/scale actors

## Integration with Python MCP Server

Currently using **simulated responses** for development. To connect to your actual Python MCP server:

### Option 1: HTTP Wrapper (Recommended)
Add an HTTP endpoint to your Python MCP server:

```python
from fastapi import FastAPI
app = FastAPI()

@app.post("/execute")
async def execute_command(command: dict):
    # Forward to your existing MCP tools
    return await your_mcp_tool_handler(command)
```

### Option 2: Direct Socket Connection
Modify the API route to use TCP sockets (matches your current Python setup).

### Option 3: MCP Client Libraries
Use official MCP client libraries to connect via stdio protocol.

## Architecture

```
Browser → Next.js Frontend → HTTP Bridge (Port 8080) → Python MCP Server → Unreal Engine (Port 55557)
```
