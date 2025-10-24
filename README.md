<div align="center">

# MegaMelange
<span style="color: #555555">AI-Powered Creative API Hub</span>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12%2B-yellow)](https://www.python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15.4%2B-green)](https://nextjs.org)
[![Status](https://img.shields.io/badge/Status-Experimental-red)](https://github.com/tomlim2/unreal-mcp-all)
[![Download](https://img.shields.io/badge/Download-v1.0.0-brightgreen)](https://github.com/tomlim2/unreal-mcp-all/releases/latest)

</div>

## 🎯 Vision: Natural Language for Creative Tools

**MegaMelange** is a universal creative platform that transforms how professionals interact with creative software. Using natural language powered by LLMs (Claude, Gemini), creators can control Unreal Engine, generate AI images, edit videos, and compose multi-tool workflows—all through simple conversation.

### The Creative Hub Manifesto

**From Tool-Specific Commands → To Natural Language Intent**

Traditional creative software requires memorizing hundreds of commands, shortcuts, and UI locations. MegaMelange inverts this: **you describe what you want, AI figures out how to do it**.

```
Instead of:  "File > Import > FBX, navigate to folder, select options..."
You say:    "Import the character model and place it in the scene"

Instead of:  Opening Photoshop, selecting tools, adjusting parameters...
You say:    "Make this image look like a watercolor painting"

Instead of:  Switching between Unreal, Blender, image editors...
You say:    "Create a 3D scene from this sketch and render it at sunset"
```

**Core Principles:**

1. **Plugin-Based Architecture** - Each creative tool (Unreal Engine, Nano Banana, Blender) is a self-contained plugin
2. **Capability-Based Routing** - AI routes commands based on *what you want to do*, not which tool to use
3. **Unified Resource Management** - Images, videos, and 3D assets flow seamlessly between tools
4. **Multi-Tool Workflows** - Chain operations across tools: "Screenshot in Unreal → Style transfer in Nano Banana → Export as video"
5. **Natural Language First** - Creative intent expressed in plain English, not technical commands

## ⚠️ Experimental Status

This project is currently in an **EXPERIMENTAL** state. The API, functionality, and implementation details are subject to significant changes. While we encourage testing and feedback, please be aware that:

- Breaking changes may occur without notice
- Features may be incomplete or unstable
- Documentation may be outdated or missing
- Production use is not recommended at this time

## 🚀 Get Started in 3 Steps

1. **[Download MegaMelange v1.0.0](https://github.com/tomlim2/unreal-mcp-all/releases/latest)** - Pre-built, ready to run
2. **Configure** - Add your Google API key to `config.json`
3. **Run** - Double-click `START.bat` and open http://localhost:34115

Full installation instructions available in the [Installation](#-installation) section below.

## 🌟 What Can You Create?

MegaMelange bridges the gap between creative vision and technical execution through AI-powered natural language control.

### Real-World Use Cases

| Use Case | Natural Language | Commands Executed | Result |
|----------|------------------|-------------------|--------|
| **Geospatial Positioning** | *"Move the map to Tokyo"* | `set_cesium_latitude_longitude(35.68, 139.69)` | Map positioned at Tokyo coordinates |
| **Actor Creation** | *"Create a red cube at the origin and take a screenshot"* | `create_actor("Cube")` + `take_screenshot(4.0)` | New cube actor + 4K screenshot with UID |
| **Cinematic Lighting** | *"Create a warm key light above the scene"* | `create_mm_control_light("KeyLight", intensity=5000, color={255,240,200})` | Tagged point light with warm temperature |
| **4K Screenshot** | *"Take a high-resolution screenshot"* | `take_screenshot(resolution_multiplier=4.0)` | 4K screenshot saved with UID |
| **AI Style Transfer** | *"Make this screenshot look like a Van Gogh painting"* | `take_screenshot()` → `style_transfer(uid, "impressionist")` | Screenshot transformed with artistic style |
| **3D Character Import** | *"Import Roblox avatar for builderman"* | `download_roblox_avatar()` → `convert_to_fbx()` → `import_object3d_by_uid()` | R6 avatar rigged and imported to Unreal |
| **Scene Query** | *"List all actors in the level"* | `get_actors_in_level()` | Array of all actors with names and types |

### Natural Language → Actual Commands

MegaMelange's LLM layer converts your creative intent into precise tool commands:

**Example 1: Geospatial Setup**
```
User: "Move the map to Tokyo and create a key light"

AI Processing:
  1. Recognizes geospatial intent → Cesium
  2. Recognizes lighting intent → MM Control Light
  3. Generates commands:
     - set_cesium_latitude_longitude(35.6804, 139.6917)
     - create_mm_control_light("KeyLight", location={0,0,200}, intensity=5000)

Result: Map positioned at Tokyo + cinematic lighting setup
```

**Example 2: Multi-Tool Workflow**
```
User: "Take a 4K screenshot and make it look like anime"

AI Processing:
  1. Screenshot command → Unreal Engine handler
  2. Style transfer → Nano Banana handler
  3. Workflow orchestration:
     - take_screenshot(resolution_multiplier=4.0) → img_042
     - style_transfer(target_uid="img_042", style="anime") → img_043

Result: Original 4K screenshot + AI-styled anime version
```

**Example 3: 3D Asset Pipeline**
```
User: "Import Roblox avatar for builderman"

AI Processing:
  1. Recognizes Roblox pipeline → Roblox handler
  2. Multi-step workflow:
     - download_roblox_avatar(username="builderman") → OBJ + textures
     - convert_obj_to_fbx(avatar_type="R6") → fbx_001
     - import_object3d_by_uid(uid="fbx_001") → Imported to Unreal

Result: R6 avatar rigged and ready to use in Unreal Engine
```

### Integrated Creative Tools

| Tool | Capabilities | Status |
|------|-------------|--------|
| **🍌 Nano Banana** | AI image generation, editing, style transfer, upscaling | ✅ Active |
| **🎮 Unreal Engine** | Real-time 3D, rendering, lighting, camera control | ✅ Active |
| **🎭 Roblox Pipeline** | Avatar download, OBJ→FBX conversion, auto-rigging | ✅ Active |
| **🎬 Veo-3 Video** | Text-to-video, video editing, scene generation | 🚧 Planned |
| **🔧 Blender** | 3D modeling, rigging, procedural workflows | 🚧 Planned |

## 🧩 Architecture: Plugin-Based Creativity

MegaMelange uses a **capability-based plugin system** where creative tools register their abilities and AI routes commands intelligently.

### System Flow

```
User Input (Natural Language)
    ↓
LLM Processing (Claude/Gemini)
    ↓
Intent Recognition → Command Generation
    ↓
Tool Registry (Capability Matching)
    ↓
Plugin Execution (Unreal/Nano Banana/etc)
    ↓
Unified Resource Management
    ↓
Results (Images/Videos/3D Assets)
```

### Key Components

**1. AI Layer** (`Python/tools/ai/`)
- **NLP Processing**: Claude/Gemini converts natural language to structured commands
- **Orchestrator**: Coordinates multi-tool workflows with dependency management
- **Command Handlers**: Modular handlers for actor, rendering, image, video operations

**2. Plugin System** (`Python/core/`)
- **Base Plugin Interface**: Standardized API for all creative tools
- **Tool Registry**: Auto-discovery and capability-based routing
- **Resource Management**: Unified handling of images, videos, 3D objects

**3. Creative Tools** (`Python/tools/`)
- **Nano Banana**: Google Gemini-powered image generation and editing
- **Unreal Engine**: C++ plugin with TCP bridge (port 55557)
- **Roblox Pipeline**: Avatar processing with Blender integration

**4. Web Interface** (`Frontend/`)
- **Next.js App**: Modern React UI with tool selector
- **Real-time Preview**: Image, video, and 3D object display
- **OpenAI Integration**: Alternative LLM option

## 📦 Installation

### Recommended: Download Pre-built Release

The easiest way to get started is to download the pre-built release:

1. **Download** the latest release from [GitHub Releases](https://github.com/tomlim2/unreal-mcp-all/releases)
   - Download `MegaMelange-v1.0.0.zip`
   - Extract to your preferred location

2. **Configure API Keys**
   - Open `config.json` in a text editor
   - Add your **Google API Key** (REQUIRED - get from https://aistudio.google.com/apikey)
   - Add your Unreal Engine project path (REQUIRED for Unreal features)
   - Optional: Add Anthropic/OpenAI API keys

3. **Run the Application**
   - Double-click `START.bat`
   - Browser will open automatically at http://localhost:34115
   - Start controlling creative tools with natural language!

**Requirements:**
- Windows 10/11
- Node.js 18+ (for frontend server)
- Unreal Engine 5.3+ (for Unreal features)
- Google API Key (REQUIRED)

### Alternative: Build from Source

For developers who want to modify or contribute to the project:

## 🛠️ Developer Setup

### Prerequisites

- **Python 3.12+** with `uv` package manager
- **Node.js 18+** and npm
- **Unreal Engine 5.3+** (tested on 5.5.4)
- **Visual Studio 2022** (for C++ plugin compilation)
- **Google API Key** (REQUIRED - for NLP and image generation)

### Option A: Automated Setup (Windows - Recommended)

1. **Install Dependencies**
   ```cmd
   script\script-install-packages.bat
   ```

2. **Configure Ports** (optional)
   ```cmd
   script\script-set-ports.bat
   ```

3. **Start All Services**
   ```cmd
   script\script-init-ports.bat
   ```

4. **Setup Unreal Project**
   - Open `MCPGameProject/MCPGameProject.uproject`
   - Build the project (includes UnrealMCP plugin)
   - Start creating at http://localhost:3000

### Option B: Web Frontend (Manual)

1. **Setup Frontend**
   ```bash
   cd Frontend
   npm install
   cp .env.example .env.local  # Optional: Add OPENAI_API_KEY
   npm run dev
   ```

2. **Setup Backend**
   ```bash
   cd Python
   uv venv && source .venv/bin/activate
   uv pip install -e .
   cp .env.example .env  # Add GOOGLE_API_KEY (REQUIRED)
   python http_bridge.py
   ```

3. **Setup Unreal Project**
   - Open `MCPGameProject/MCPGameProject.uproject`
   - Right-click .uproject → Generate VS project files
   - Build in Development Editor configuration

### Option C: MCP Protocol (For AI Assistants)

Use MegaMelange from Claude Desktop, Cursor, or Windsurf:

1. **Setup Python Server**
   ```bash
   cd Python
   uv venv && source .venv/bin/activate
   uv pip install -e .
   ```

2. **Configure MCP Client**

   **Claude Desktop** (`~/.config/claude-desktop/mcp.json`):
   ```json
   {
     "mcpServers": {
       "megamelange": {
         "command": "uv",
         "args": ["--directory", "/path/to/MegaMelange/Python", "run", "unreal_mcp_server.py"]
       }
     }
   }
   ```

   **Cursor** (`.cursor/mcp.json` in project root):
   ```json
   {
     "mcpServers": {
       "megamelange": {
         "command": "mcp-proxy",
         "args": ["uv", "--directory", "D:\\path\\to\\MegaMelange\\Python", "run", "unreal_mcp_server.py"]
       }
     }
   }
   ```

### Option D: Plugin Integration (Existing Projects)

Add MegaMelange to your existing Unreal Engine project:

1. **Copy Plugin**
   - Copy `MCPGameProject/Plugins/UnrealMCP` to your project's `Plugins/` folder

2. **Enable Plugin**
   - Edit > Plugins > Find "UnrealMCP" > Enable > Restart Editor

3. **Build Plugin**
   - Generate VS project files and build

## 📂 Project Structure

```
MegaMelange/
├── Frontend/                    # Next.js web application
│   ├── src/app/                # React components and pages
│   ├── src/app/api/            # API routes (OpenAI integration)
│   └── src/app/components/     # Creative Hub UI
│
├── MCPGameProject/             # Unreal Engine 5.3 sample project
│   ├── Plugins/UnrealMCP/      # C++ plugin with TCP server
│   │   ├── Source/UnrealMCP/   # Plugin source code
│   │   └── UnrealMCP.uplugin   # Plugin definition
│   ├── Source/                 # Project source files
│   └── Config/                 # UE configuration
│
├── Python/                     # Creative Hub backend
│   ├── core/                   # Plugin system core
│   │   ├── plugin_base.py      # BasePlugin interface
│   │   ├── registry/           # Tool registry & discovery
│   │   └── resources/          # Image/video/3D management
│   ├── tools/                  # Creative tool plugins
│   │   ├── image_generation/   # Nano Banana plugin
│   │   ├── unreal_engine/      # Unreal Engine plugin
│   │   └── ai/                 # NLP & orchestration
│   ├── unreal_mcp_server.py    # MCP server
│   └── http_bridge.py          # HTTP API server
│
└── script/                     # Windows automation scripts
    ├── script-init-ports.bat   # Start all services
    ├── script-install-packages.bat
    └── script-stop-ports.bat
```

## 🎨 Usage Examples

### Natural Language Commands

**Unreal Engine - Geospatial Control:**
```bash
"Move the map to Tokyo"
→ Commands: set_cesium_latitude_longitude(35.6804, 139.6917)

"Show New York City"
→ Commands: set_cesium_latitude_longitude(40.7128, -74.0060)

"Get current map coordinates"
→ Commands: get_cesium_properties()
```

**Unreal Engine - Actor & Scene Control:**
```bash
"Create a red cube at the origin and take a 4K screenshot"
→ Commands: create_actor("RedCube", "StaticMeshActor", location={0,0,100}), take_screenshot(resolution_multiplier=4.0)

"List all actors in the level"
→ Commands: get_actors_in_level()

"Delete the actor named 'OldCube'"
→ Commands: delete_actor("OldCube")

"Move 'MyCube' to coordinates (100, 200, 50)"
→ Commands: set_actor_transform("MyCube", location={100, 200, 50})
```

**Unreal Engine - Cinematic Lighting:**
```bash
"Create a warm key light above the scene"
→ Commands: create_mm_control_light("KeyLight", location={0,0,200}, intensity=5000, color={255,240,200})

"Update KeyLight to be cooler and brighter"
→ Commands: update_mm_control_light("KeyLight", intensity=8000, color={200,220,255})

"List all cinematic lights"
→ Commands: get_mm_control_lights()

"Remove the fill light"
→ Commands: delete_mm_control_light("FillLight")
```

**Unreal Engine - Screenshot & Capture:**
```bash
"Take a 4K screenshot"
→ Commands: take_screenshot(resolution_multiplier=4.0)

"Capture a high-res image at 8x resolution"
→ Commands: take_screenshot(resolution_multiplier=8.0)
```

**AI Image Generation (Nano Banana):**
```bash
"Generate a cyberpunk cityscape with neon lights"
→ Commands: generate_image(prompt="cyberpunk cityscape neon lights", style="photorealistic")

"Make this screenshot look like a watercolor painting"
→ Commands: take_screenshot() → style_transfer(target_uid="img_042", style="watercolor")

"Transform img_001 into anime style"
→ Commands: style_transfer(target_uid="img_001", style="anime")
```

**Multi-Tool Workflows:**
```bash
"Take a 4K screenshot and apply Van Gogh style transfer"
→ Workflow:
  1. take_screenshot(resolution_multiplier=4.0) → img_042
  2. style_transfer(target_uid="img_042", style="impressionist") → img_043

"Download Roblox avatar for user 'builderman' and import to Unreal"
→ Workflow:
  1. download_roblox_avatar(username="builderman") → OBJ files
  2. convert_obj_to_fbx(avatar_type="R6") → fbx_001
  3. import_object3d_by_uid(uid="fbx_001") → Imported to Unreal

"Set up scene in San Francisco with cinematic lighting and capture"
→ Workflow:
  1. set_cesium_latitude_longitude(37.7749, -122.4194)
  2. create_mm_control_light("KeyLight", location={200,100,300}, intensity=6000, color={255,230,180})
  3. create_mm_control_light("FillLight", location={-100,150,200}, intensity=3000, color={200,210,255})
  4. take_screenshot(resolution_multiplier=4.0) → img_050

"Create scene with actor, lighting, and AI-styled output"
→ Workflow:
  1. set_cesium_latitude_longitude(35.6804, 139.6917)  # Tokyo
  2. create_actor("Landmark", "StaticMeshActor", location={0,0,100})
  3. create_mm_control_light("Spotlight", location={0,0,500}, intensity=10000)
  4. take_screenshot(resolution_multiplier=4.0) → img_051
  5. style_transfer(target_uid="img_051", style="anime") → img_052
```

### API Example (Python)

```python
from core import get_registry

# Get tool registry
registry = get_registry()

# Route command to appropriate tool
result = registry.execute_command('style_transfer', {
    'target_image_uid': 'img_042',
    'style': 'anime'
})

print(result.result['image']['uid'])  # img_043
```

### Multi-Tool Workflow

```python
from tools.ai.orchestrator import get_orchestrator, WorkflowStep

orchestrator = get_orchestrator()

# Workflow: Screenshot → Style Transfer → Export
workflow = [
    WorkflowStep('capture', 'unreal_engine', 'take_highresshot',
                 {'resolution': '1920x1080'}),
    WorkflowStep('stylize', 'nano_banana', 'style_transfer',
                 {'style': 'watercolor'}, depends_on=['capture'])
]

orchestrator.create_workflow('render_and_style', workflow)
results = orchestrator.execute_workflow('render_and_style')
```

## 🔌 Extending MegaMelange

### Adding New Creative Tools

The plugin architecture makes it easy to add new tools:

1. **Create Tool Directory**
   ```bash
   mkdir -p Python/tools/my_new_tool
   ```

2. **Define Metadata** (`metadata.json`)
   ```json
   {
     "tool_id": "my_new_tool",
     "display_name": "My Creative Tool",
     "capabilities": ["video_generation"],
     "supported_commands": ["generate_video"]
   }
   ```

3. **Implement Plugin** (`plugin.py`)
   ```python
   from core import BasePlugin, ToolCapability, CommandResult

   class Plugin(BasePlugin):
       def get_metadata(self) -> ToolMetadata:
           return ToolMetadata(
               tool_id="my_new_tool",
               capabilities=[ToolCapability.VIDEO_GENERATION]
           )

       def execute_command(self, command_type: str, params: Dict) -> CommandResult:
           # Your tool logic here
           pass
   ```

4. **Tool Auto-Discovered** - The registry automatically finds and loads your plugin!

See `CREATIVE_HUB_ARCHITECTURE.md` (in local docs) for complete plugin development guide.

## 🧪 Service Management

### Windows Scripts

```cmd
# Start all services (Python backend, HTTP bridge, Frontend)
script\script-init-ports.bat

# Stop all services
script\script-stop-ports.bat

# Configure ports
script\script-set-ports.bat
```

### Manual Control

```bash
# Python MCP Server
cd Python && uv run unreal_mcp_server.py

# HTTP Bridge (for web frontend)
cd Python && python http_bridge.py

# Web Frontend
cd Frontend && npm run dev
```

## 🎯 Target Users

**MegaMelange is designed for creative professionals in their 20s:**

- 🎬 **Film Directors & Cinematographers** - Natural language cinematic lighting and camera control
- 🎮 **Game Developers** - Rapid prototyping with AI-assisted asset creation
- 🎨 **Technical Artists** - Multi-tool workflows for procedural content generation
- 🏗️ **Virtual Production Artists** - Real-time Unreal Engine control for on-set visualization
- 📽️ **Content Creators** - Seamless workflow from concept to final render

## 📝 Configuration

### Environment Variables

**Python** (`.env`):
```bash
# Required
GOOGLE_API_KEY=your_google_key_here

# Optional
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Feature Flags
FEATURE_PLUGIN_SYSTEM=true
FEATURE_NANO_BANANA=true
FEATURE_UNREAL_ENGINE=true
```

**Frontend** (`.env.local`):
```bash
OPENAI_API_KEY=your_openai_api_key_here  # Optional
```

### MCP Client Configuration

| MCP Client | Configuration File |
|------------|-------------------|
| Claude Desktop | `~/.config/claude-desktop/mcp.json` |
| Cursor | `.cursor/mcp.json` (project root) |
| Windsurf | `~/.config/windsurf/mcp.json` |

## 🤝 Contributing

We welcome contributions! Whether you're:

- Adding new creative tool plugins
- Improving natural language processing
- Building multi-tool workflows
- Enhancing the web UI
- Writing documentation

See `CONTRIBUTING.md` (coming soon) for guidelines.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- **Claude** (Anthropic) - Natural language processing
- **Google Gemini** - Image generation and editing
- **Unreal Engine** - Real-time 3D platform
- **FastMCP** - Model Context Protocol implementation
- **Next.js** - Web framework

## 💬 Support & Community

- **GitHub Issues**: [Report bugs or request features](https://github.com/tomlim2/unreal-mcp-all/issues)
- **Documentation**: See `docs/` folder in your local installation

---

<div align="center">

**Built with ❤️ by creative developers, for creative professionals**

*MegaMelange: Where natural language meets creative power*

</div>
