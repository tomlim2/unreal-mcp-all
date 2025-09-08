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

MegaMelange provides natural language control of Unreal Engine through multiple interfaces: web frontend, MCP protocol for AI assistants, and comprehensive Python automation tools.

| Category | Capabilities |
|----------|-------------|
| **Scene Management** | • Create and manipulate actors (cubes, spheres, lights, cameras)<br>• Set actor transforms (position, rotation, scale)<br>• Query and search actors by name or type<br>• List all actors in the current level |
| **Lighting & Environment** | • Ultra Dynamic Sky integration with time-of-day control<br>• Color temperature adjustment for cinematic lighting<br>• MM Control Lights system for professional lighting setups<br>• Environmental lighting and atmosphere control |
| **Geospatial Integration** | • Cesium integration for real-world coordinates<br>• Set latitude/longitude for accurate positioning<br>• Geographic data integration and mapping |
| **Rendering & Capture** | • High-resolution screenshot capture (4K+)<br>• Material parameter control and manipulation<br>• Camera positioning and viewport control<br>• Real-time rendering adjustments |
| **AI Image Processing** | • Nano Banana: AI-powered image style transformation<br>• Google Gemini integration for creative image editing<br>• Transform screenshots with artistic styles and effects<br>• Automated styled rendering workflows |
| **Blueprint Development** | • Create Blueprint classes with custom components<br>• Add and configure components (mesh, camera, light)<br>• Compile Blueprints and spawn Blueprint actors<br>• Component property and physics settings |
| **Editor Control** | • Focus viewport on specific actors or locations<br>• Camera orientation and distance control<br>• Level management and organization |

All capabilities are accessible through natural language commands, making professional Unreal Engine workflows intuitive and efficient for creative professionals.

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
  - **http_bridge.py** - HTTP bridge for web frontend integration

- **script/** - Windows batch scripts for easy setup and management
  - **script-init-ports.bat** - Initialize and start all services
  - **script-install-packages.bat** - Install Python and Node.js dependencies
  - **script-set-ports.bat** - Configure ports and environment variables
  - **script-stop-ports.bat** - Stop all running services

- **docs/** - Project documentation and schemas
- **tests/** - Integration and connection tests

## 🚀 Quick Start Guide

Choose your preferred interface for controlling Unreal Engine with AI:

### Option A: Automated Setup (Windows - Recommended)

1. **Prerequisites**
   - Python 3.12+ and `uv` package manager
   - Node.js 18+ and npm
   - OpenAI API key (for web frontend)
   - Anthropic API key (for MCP server)
   - Unreal Engine 5.3+

2. **One-Click Setup**
   ```cmd
   # Install all dependencies automatically
   script\script-install-packages.bat
   
   # Configure ports (optional - sets up .env files)
   script\script-set-ports.bat
   
   # Start all services
   script\script-init-ports.bat
   ```

3. **Setup Unreal Project**
   - Open `MCPGameProject/MCPGameProject.uproject`
   - Build the project (includes UnrealMCP plugin)
   - Start playing with natural language commands at http://localhost:3000

### Option B: Web Frontend (Manual setup)

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

### Option C: MCP Protocol (For AI assistants)

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

### Option D: Plugin Integration (For existing projects)

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

### Service Management (Windows)

Use the provided batch scripts for easy service management:

```cmd
# Start all services (Python MCP, HTTP Bridge, Frontend)
script\script-init-ports.bat

# Stop all services
script\script-stop-ports.bat

# Change port configuration
script\script-set-ports.bat
```

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