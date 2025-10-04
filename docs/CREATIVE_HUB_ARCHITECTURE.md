# Creative Hub Architecture

**Branch:** `feature/creative-hub-architecture`
**Status:** Phase 1-7 Complete (Backend + Frontend Integration)
**Created:** 2025-10-04
**Commits:** 2 (118ec71 backend, 9bc06f4 frontend)

---

## Overview

This document describes the Creative Hub architecture transformation, which evolves the project from a Unreal Engine-focused tool to a universal creative platform supporting multiple tools (Unreal Engine, Nano Banana, Blender, video generation, etc.).

## Core Principles

### 1. Plugin-Based Architecture
- **Modular Design**: Each tool (Unreal, Nano Banana, etc.) is a self-contained plugin
- **Auto-Discovery**: Tools are automatically discovered via `metadata.json` files
- **Lazy Loading**: Plugins load on-demand to conserve resources
- **Standardized Interface**: All tools implement `BasePlugin` for consistency

### 2. Capability-Based Routing
- Commands route to appropriate tools based on **capabilities**, not hardcoded tool names
- Example: `IMAGE_EDITING` → Nano Banana, `RENDERING` → Unreal Engine
- Enables intelligent fallback and multi-tool support

### 3. Resource Management
- **Centralized Processing**: Unified modules for images, videos, 3D objects
- **Copyright Safety**: User uploads processed in-memory only (no storage)
- **UID System**: Generated content tracked with persistent UIDs
- **Type-Specific Handling**: Dedicated processors for each resource type

### 4. Gradual Migration
- **Feature Flags**: Toggle between legacy and new architecture
- **Coexistence**: Both systems can run simultaneously during transition
- **Zero Downtime**: No breaking changes to existing workflows

---

## System Components

### Core Modules (`Python/core/`)

#### 1. Plugin System (`core/plugin_base.py`, `core/registry/`)
```python
from core import BasePlugin, get_registry, ToolCapability

# Get the global registry
registry = get_registry()

# Find tools by capability
image_tools = registry.get_tools_by_capability(ToolCapability.IMAGE_EDITING)

# Execute command (automatically routes to correct tool)
result = registry.execute_command('edit_image', params)
```

**Key Classes:**
- `BasePlugin`: Abstract base class all tools inherit from
- `ToolRegistry`: Central registry for tool discovery and routing
- `ToolCapability`: Enum of supported capabilities (IMAGE_EDITING, RENDERING, etc.)
- `ToolMetadata`: Describes tool capabilities and requirements
- `CommandResult`: Standardized command execution result

#### 2. Resource Management (`core/resources/`)

**Images** (`core/resources/images/`)
- `process_main_image()`: Handle UID or user upload (in-memory)
- `process_reference_images()`: Validate reference images
- `load_image_from_uid()`: Load generated images

**Videos** (`core/resources/videos/`)
- `process_video()`: Handle video uploads/UIDs
- `load_video_from_uid()`: Load generated videos

**3D Objects** (`core/resources/objects_3d/`)
- `process_3d_object()`: Handle 3D uploads/UIDs (FBX, OBJ, GLTF, etc.)
- `load_3d_object_from_uid()`: Load generated 3D assets

**Usage Example:**
```python
from core.resources import process_main_image, process_video

# Process image (supports both UID and upload)
uid, image_data = process_main_image(
    main_image_request={'data': 'base64...'},  # User upload (in-memory)
    target_image_uid='img_042'  # OR existing screenshot
)

# Process video
vid_uid, video_data = process_video(
    video_request={'data': 'base64...', 'mime_type': 'video/mp4'}
)
```

#### 3. Configuration & Feature Flags (`core/config.py`)

```python
from core import get_config

config = get_config()

# Check feature flags
if config.features.enable_plugin_system:
    # Use new plugin-based routing
    result = registry.execute_command(command, params)
else:
    # Use legacy handlers
    result = legacy_handler.execute(command, params)

# Get enabled tools
enabled_tools = config.get_enabled_tools()  # ['unreal_engine', 'nano_banana']
```

**Environment Variables** (`.env`):
```bash
# Core Features
FEATURE_PLUGIN_SYSTEM=false      # Enable new plugin system
FEATURE_ORCHESTRATOR=false       # Enable multi-tool workflows
FEATURE_LEGACY_HANDLERS=true     # Keep legacy system (recommended during migration)

# Tool Features
FEATURE_NANO_BANANA=true
FEATURE_UNREAL_ENGINE=true
FEATURE_BLENDER=false            # Future
FEATURE_VIDEO_GEN=false          # Future

# Resource Management
FEATURE_VIDEO_RESOURCES=true
FEATURE_3D_RESOURCES=true
```

#### 4. Multi-Tool Orchestrator (`tools/ai/orchestrator.py`)

Coordinates workflows spanning multiple tools with dependency management.

```python
from tools.ai.orchestrator import get_orchestrator, WorkflowStep

orchestrator = get_orchestrator()

# Simple command routing
result = orchestrator.route_command('edit_image', params, preferred_tool='nano_banana')

# Complex multi-step workflow
steps = [
    WorkflowStep('step1', 'unreal_engine', 'take_highresshot', {}),
    WorkflowStep('step2', 'nano_banana', 'style_transfer',
                 {'target_image_uid': 'img_001'}, depends_on=['step1'])
]

orchestrator.create_workflow('my_workflow', steps)
results = orchestrator.execute_workflow('my_workflow')
```

---

## Tool Implementation

### Directory Structure
```
Python/tools/
├── nano_banana/
│   ├── metadata.json    # Tool discovery metadata
│   ├── plugin.py        # Plugin implementation (class Plugin(BasePlugin))
│   └── __init__.py
├── unreal_engine/
│   ├── metadata.json
│   ├── plugin.py
│   └── __init__.py
└── ai/
    ├── command_handlers/  # Legacy handlers (still functional)
    └── orchestrator.py    # Multi-tool coordinator
```

### Tool Metadata Example (`tools/nano_banana/metadata.json`)
```json
{
  "tool_id": "nano_banana",
  "display_name": "Nano Banana",
  "version": "1.0.0",
  "description": "AI-powered image generation, editing, and style transfer",
  "author": "MegaMelange Team",
  "requires_connection": true,
  "icon": "🍌",
  "pricing_tier": "premium",
  "capabilities": [
    "image_generation",
    "image_editing",
    "image_style_transfer"
  ],
  "supported_commands": [
    "generate_image",
    "edit_image",
    "style_transfer",
    "upscale_image",
    "remove_background"
  ]
}
```

### Plugin Implementation (`tools/nano_banana/plugin.py`)
```python
from core import BasePlugin, ToolCapability, ToolStatus, ToolMetadata, CommandResult

class Plugin(BasePlugin):
    """Nano Banana plugin."""

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="nano_banana",
            display_name="Nano Banana",
            version="1.0.0",
            capabilities=[
                ToolCapability.IMAGE_GENERATION,
                ToolCapability.IMAGE_EDITING,
                ToolCapability.IMAGE_STYLE_TRANSFER
            ],
            description="AI-powered image API",
            author="MegaMelange Team",
            requires_connection=True
        )

    def initialize(self) -> bool:
        # Setup API client, load resources, etc.
        self.set_status(ToolStatus.AVAILABLE)
        return True

    def shutdown(self) -> bool:
        # Cleanup resources
        return True

    def health_check(self) -> ToolStatus:
        # Check API availability
        return ToolStatus.AVAILABLE

    def get_supported_commands(self) -> List[str]:
        return ["generate_image", "edit_image", "style_transfer"]

    def validate_command(self, command_type: str, params: Dict) -> Dict:
        # Validate parameters
        return {'valid': True, 'errors': []}

    def execute_command(self, command_type: str, params: Dict) -> CommandResult:
        # Execute command
        return CommandResult(success=True, result={...})
```

---

## Migration Strategy

### Phase 1: Core Infrastructure ✅ COMPLETE
- [x] Create `core/plugin_base.py` - Base plugin interface
- [x] Create `core/registry/tool_registry.py` - Tool discovery & loading
- [x] Add `metadata.json` to existing tools
- [x] Create `tools/nano_banana/plugin.py` wrapper
- [x] Create `tools/unreal_engine/plugin.py` wrapper

### Phase 2: Resource Management ✅ COMPLETE
- [x] Create `core/resources/videos/` module
- [x] Create `core/resources/objects_3d/` module
- [x] Update UID manager for video/3D prefixes (already done)
- [x] Update `core/resources/__init__.py` exports

### Phase 3: Orchestration ✅ COMPLETE
- [x] Create `tools/ai/orchestrator.py`
- [x] Implement workflow state management
- [x] Add capability-based routing
- [x] Support multi-step workflows with dependencies

### Phase 4: Configuration ✅ COMPLETE
- [x] Create `core/config.py` with feature flags
- [x] Create `.env.example` with all flags
- [x] Update `core/__init__.py` exports
- [x] Add configuration logging

### Phase 5: Testing ✅ COMPLETE
- [x] Create `test_plugin_system.py` integration test
- [x] Verify registry discovery
- [x] Test capability routing
- [x] Validate plugin loading

### Phase 6: Documentation ✅ COMPLETE
- [x] Create `CREATIVE_HUB_ARCHITECTURE.md` (this file)
- [x] Document plugin implementation guide
- [x] Document migration strategy
- [x] Add usage examples

### Phase 7: Frontend Integration ✅ COMPLETE
- [x] Rename `UnrealAIChat.module.css` → `CreativeHub.module.css`
- [x] Create `ToolSelector` component with dropdown UI
- [x] Create `MessageItem3DResult` component for 3D objects
- [x] Add API routes (`/api/tools`, `/api/3d-object/[uid]`)
- [x] Update `ExecutionResults` to display 3D objects
- [x] Add 3D object styles (cards, download buttons, previews)
- [ ] Add workflow builder UI (deferred to Phase 9)

### Phase 8: Production Rollout (PENDING)
- [ ] Enable plugin system in production (`FEATURE_PLUGIN_SYSTEM=true`)
- [ ] Monitor for issues
- [ ] Gradually disable legacy handlers
- [ ] Deprecate old command handler structure

---

## Testing

### Run Plugin System Tests
```bash
cd Python
python test_plugin_system.py
```

**Expected Output:**
```
Creative Hub Plugin System Test Suite
======================================
Testing Configuration
  ✓ Configuration loaded successfully
  - Enabled tools: ['unreal_engine', 'nano_banana']
  - Plugin mode: False
  - Legacy mode: True

Testing Tool Registry
  ✓ Discovered 2 tools:
  - nano_banana: Nano Banana v1.0.0
    Capabilities: ['image_generation', 'image_editing', ...]
  - unreal_engine: Unreal Engine v5.5.4
    Capabilities: ['mesh_3d_creation', 'rendering', ...]

Testing Capability Routing
  ✓ Tools with image_editing:
  - nano_banana
  ✓ Tools with rendering:
  - unreal_engine

✓ All tests completed successfully!
```

---

## Usage Examples

### Example 1: Simple Command Routing
```python
from core import get_registry

registry = get_registry()

# Automatically routes to Nano Banana
result = registry.execute_command('style_transfer', {
    'target_image_uid': 'img_042',
    'style': 'anime'
})

print(result.success)  # True
print(result.result)   # {'image': {'uid': 'img_043', ...}}
```

### Example 2: Multi-Tool Workflow
```python
from tools.ai.orchestrator import get_orchestrator, WorkflowStep

orchestrator = get_orchestrator()

# Workflow: Screenshot in Unreal → Style transfer in Nano Banana
workflow = [
    WorkflowStep(
        step_id='capture',
        tool_id='unreal_engine',
        command_type='take_highresshot',
        params={'resolution': '1920x1080'}
    ),
    WorkflowStep(
        step_id='stylize',
        tool_id='nano_banana',
        command_type='style_transfer',
        params={'style': 'watercolor'},
        depends_on=['capture']  # Wait for screenshot
    )
]

orchestrator.create_workflow('render_and_style', workflow)
results = orchestrator.execute_workflow('render_and_style')

# Results contain both steps' outputs
print(results['steps_completed'])  # 2
print(results['results'][1]['result'])  # Stylized image data
```

### Example 3: Resource Management
```python
from core.resources import process_main_image, process_video

# User uploads image for transformation
uid, image_data = process_main_image(
    main_image_request={
        'data': 'data:image/png;base64,iVBORw0...',
        'mime_type': 'image/png'
    }
)
# uid = None (not stored), image_data = {'mime_type': 'image/png', 'data': bytes}

# Load existing screenshot
uid, image_data = process_main_image(target_image_uid='img_042')
# uid = 'img_042', image_data = None (load from UID system)
```

---

## Adding New Tools

### 1. Create Tool Directory
```bash
mkdir -p Python/tools/my_new_tool
```

### 2. Create Metadata
`Python/tools/my_new_tool/metadata.json`:
```json
{
  "tool_id": "my_new_tool",
  "display_name": "My New Tool",
  "version": "1.0.0",
  "description": "Does amazing things",
  "author": "Your Name",
  "requires_connection": false,
  "capabilities": ["video_generation"],
  "supported_commands": ["generate_video"]
}
```

### 3. Implement Plugin
`Python/tools/my_new_tool/plugin.py`:
```python
from core import BasePlugin, ToolCapability, ToolStatus, ToolMetadata, CommandResult

class Plugin(BasePlugin):
    # Implement required methods (see template above)
    pass
```

### 4. Test Discovery
```bash
python test_plugin_system.py
# Should show "my_new_tool" in discovered tools
```

### 5. Enable in Config
`.env`:
```bash
FEATURE_MY_NEW_TOOL=true
```

---

## Benefits of New Architecture

1. **Extensibility**: Add new tools without modifying core code
2. **Maintainability**: Each tool is self-contained and independently testable
3. **Flexibility**: Route commands based on capabilities, not hardcoded tool names
4. **Scalability**: Lazy loading conserves resources for unused tools
5. **Discoverability**: Tools auto-register via metadata, no manual setup
6. **Workflows**: Multi-tool coordination with dependency management
7. **Safety**: Gradual migration via feature flags, zero downtime

---

## Next Steps

1. **Enable Plugin System**: Set `FEATURE_PLUGIN_SYSTEM=true` in `.env`
2. **Test Thoroughly**: Run integration tests with both systems enabled
3. **Frontend Updates**: Migrate UI components to support multiple tools
4. **Production Rollout**: Gradually phase out legacy handlers
5. **Add New Tools**: Implement Blender, video generation plugins

---

---

## Summary Statistics

### Backend Implementation (Commit 118ec71)
- **18 files changed**, 2,274 insertions(+), 3 deletions(-)
- Core plugin system: `plugin_base.py`, `tool_registry.py`, `config.py`
- Resource management: Videos, 3D objects modules
- Orchestrator: Multi-tool workflow coordination
- Tool plugins: Nano Banana, Unreal Engine
- Testing & docs: Test suite, comprehensive guide

### Frontend Implementation (Commit 9bc06f4)
- **8 files changed**, 695 insertions(+)
- ToolSelector component with dropdown UI
- MessageItem3DResult for 3D object display
- API routes for tools and 3D object serving
- Comprehensive styling for all resource types

### Total Impact
- **26 files changed**, 2,969 insertions(+), 3 deletions(-)
- Full-stack implementation from plugin system to UI
- Backwards compatible via feature flags
- Production-ready with fallback mechanisms

---

## Support

For questions or issues with the Creative Hub architecture, see:
- **Main Documentation**: `/CLAUDE.md`
- **Architecture Guide**: `/CREATIVE_HUB_ARCHITECTURE.md` (this file)
- **Test Script**: `Python/test_plugin_system.py`
- **Example Config**: `Python/.env.example`
- **Frontend Components**: `Frontend/src/app/components/ToolSelector.tsx`
