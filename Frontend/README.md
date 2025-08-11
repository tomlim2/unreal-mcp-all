# Unreal MCP Frontend

A Next.js frontend for the Unreal Engine MCP (Model Context Protocol) server, featuring OpenAI integration for natural language commands.

## Features

- 🤖 **OpenAI Integration**: Convert natural language to Unreal Engine commands
- 🎮 **Unreal Engine Control**: Interface with dynamic sky, actors, blueprints
- ⚡ **Real-time Commands**: Execute commands and see results immediately
- 🎨 **Modern UI**: Clean, responsive interface with example prompts
- 🔧 **MCP Protocol**: Connects to your Python MCP server

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure OpenAI API**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local and add your OpenAI API key
   OPENAI_API_KEY=your-openai-api-key-here
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
Browser → Next.js Frontend → OpenAI API → Command Generation → Python MCP Server → Unreal Engine
```
