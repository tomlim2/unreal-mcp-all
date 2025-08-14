<div align="center">

# MegaMelange
<span style="color: #555555">AI-Powered Unreal Engine Development Suite</span>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5.3%2B-orange)](https://www.unrealengine.com)
[![Python](https://img.shields.io/badge/Python-3.12%2B-yellow)](https://www.python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15.4%2B-green)](https://nextjs.org)
[![Status](https://img.shields.io/badge/Status-Experimental-red)](https://github.com/chongdashu/unreal-mcp)

</div>

MegaMelange is a comprehensive AI-powered development suite that enables natural language control of Unreal Engine through multiple interfaces: MCP protocol for AI assistants (Cursor, Windsurf, Claude Desktop), a modern web frontend with OpenAI integration, and extensive Python tooling for automation and testing.

## ⚠️ Experimental Status

This project is currently in an **EXPERIMENTAL** state. The API, functionality, and implementation details are subject to significant changes. While we encourage testing and feedback, please be aware that:

- Breaking changes may occur without notice
- Features may be incomplete or unstable
- Documentation may be outdated or missing
- Production use is not recommended at this time

## 🌟 Overview

The Unreal MCP integration provides comprehensive tools for controlling Unreal Engine through natural language:

| Category | Capabilities |
|----------|-------------|
| **Actor Management** | • Create and delete actors (cubes, spheres, lights, cameras, etc.)<br>• Set actor transforms (position, rotation, scale)<br>• Query actor properties and find actors by name<br>• List all actors in the current level |
| **Blueprint Development** | • Create new Blueprint classes with custom components<br>• Add and configure components (mesh, camera, light, etc.)<br>• Set component properties and physics settings<br>• Compile Blueprints and spawn Blueprint actors<br>• Create input mappings for player controls |
| **Blueprint Node Graph** | • Add event nodes (BeginPlay, Tick, etc.)<br>• Create function call nodes and connect them<br>• Add variables with custom types and default values<br>• Create component and self references<br>• Find and manage nodes in the graph |
| **Editor Control** | • Focus viewport on specific actors or locations<br>• Control viewport camera orientation and distance |

All these capabilities are accessible through natural language commands via AI assistants, making it easy to automate and control Unreal Engine workflows.

## 🧩 Components

### Web Frontend `Frontend/`
- **Next.js 15.4+ Application** with TypeScript and modern React
- **OpenAI Integration** for natural language to Unreal commands
- **Real-time Command Interface** with example prompts and immediate execution
- **Modern UI/UX** with responsive design and intuitive controls
- **API Bridge** connecting web interface to Python MCP server

### Sample Project (MCPGameProject) `MCPGameProject/`
- **UE 5.3 Blank Starter Project** with UnrealMCP plugin pre-configured
- **Complete Build Configuration** with Visual Studio project files
- **Plugin Integration** ready for immediate development and testing

### C++ Plugin (UnrealMCP) `MCPGameProject/Plugins/UnrealMCP/`
- **Native TCP Server** for MCP communication on port 55557
- **Unreal Editor Integration** with subsystem connectivity
- **Comprehensive Actor Tools** for creation, manipulation, and querying
- **Blueprint Management** with component handling and compilation
- **Command Execution Engine** with response handling and error management

### Python MCP Server `Python/`
- **FastMCP Implementation** providing Model Context Protocol server
- **TCP Socket Management** connecting to C++ plugin
- **Modular Tool System** with categorized command modules
- **Extensive Test Suite** with organized testing scripts
- **Development Tools** for automation and validation

## 📂 Directory Structure

- **Frontend/** - Next.js web application
  - **src/app/** - React components and pages
  - **src/app/api/** - API routes for OpenAI integration
  - **src/app/components/** - Unreal AI chat interface
  - **package.json** - Node.js dependencies and scripts

- **MCPGameProject/** - UE 5.3 sample project
  - **Plugins/UnrealMCP/** - C++ plugin source
    - **Source/UnrealMCP/** - Plugin source code with commands
    - **UnrealMCP.uplugin** - Plugin definition
  - **Source/** - Project source files
  - **Config/** - Unreal Engine configuration files

- **Python/** - MCP server and automation tools
  - **tools/** - Modular tool system (actor, blueprint, editor, NLP)
  - **scripts/** - Organized test scripts by category
  - **docs/** - Python-specific documentation
  - **unreal_mcp_server.py** - Main MCP server implementation

- **tests/** - Integration and connection tests

## 🚀 Quick Start Guide

Choose your preferred interface for controlling Unreal Engine with AI:

### Option A: Web Frontend (Recommended for beginners)

1. **Prerequisites**
   - Node.js 18+ and npm
   - OpenAI API key
   - Unreal Engine 5.3+

2. **Setup Frontend**
   ```bash
   cd Frontend
   npm install
   cp .env.example .env.local  # Add your OPENAI_API_KEY
   npm run dev
   ```

3. **Setup Unreal Project**
   - Open `MCPGameProject/MCPGameProject.uproject`
   - Build the project (includes UnrealMCP plugin)
   - Start playing with natural language commands at http://localhost:3000

### Option B: MCP Protocol (For AI assistants)

1. **Prerequisites**
   - Python 3.12+ and `uv`
   - MCP Client (Claude Desktop, Cursor, Windsurf)
   - Unreal Engine 5.3+

2. **Setup Python Server**
   ```bash
   cd Python
   uv venv && source .venv/bin/activate
   uv pip install -e .
   ```

3. **Setup Unreal Project**
   - Open `MCPGameProject/MCPGameProject.uproject`
   - Right-click .uproject file → Generate VS project files
   - Build in Development Editor configuration

4. **Configure MCP Client**
   ```json
   {
     "mcpServers": {
       "unrealMCP": {
         "command": "uv",
         "args": [
           "--directory", "/path/to/MegaMelange/Python",
           "run", "unreal_mcp_server.py"
         ]
       }
     }
   }
   ```

### Option C: Plugin Integration (For existing projects)

1. **Copy Plugin**
   - Copy `MCPGameProject/Plugins/UnrealMCP` to your project's Plugins folder

2. **Enable Plugin**
   - Edit > Plugins > Find "UnrealMCP" > Enable > Restart Editor

3. **Build Plugin**
   - Generate VS project files and build

### Testing Your Setup

Try these example commands:
- Web Frontend: "Set the time to sunrise" or "Create a cube at 0,0,100"
- MCP Protocol: Ask your AI assistant to "list all actors in the Unreal level"

### Configuration Locations

| MCP Client | Configuration File |
|------------|-------------------|
| Claude Desktop | `~/.config/claude-desktop/mcp.json` |
| Cursor | `.cursor/mcp.json` (project root) |
| Windsurf | `~/.config/windsurf/mcp.json` |


## License
MIT

## Questions

For questions, you can reach me on X/Twitter: [@chongdashu](https://www.x.com/chongdashu)