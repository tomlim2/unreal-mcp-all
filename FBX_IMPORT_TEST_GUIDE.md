# FBX Import Test Guide

## Summary

Successfully integrated FBX support into the UID system. The system now supports both OBJ and FBX formats with separate UID counters and auto-detection.

## What Was Done

### 1. UID Manager Updates
- Added `fbx_counter` alongside existing `obj_counter`
- Created `get_next_fbx_uid()` method
- Updated state persistence to save/load FBX counter

### 2. Path Manager Updates
- Modified `get_3d_object_uid_path()` to detect format from UID prefix
- OBJ files: `assets/objects3d/obj/obj_XXX/`
- FBX files: `assets/objects3d/fbx/fbx_XXX/`

### 3. Import Handler Updates
- Updated validation to accept both `obj_` and `fbx_` prefixes
- Enhanced file detection to look for both `.obj` and `.fbx` files
- Prefer FBX when both formats exist (Epic's native format)
- Changed parameters from `obj_file_path` to `mesh_file_path` + `mesh_format`

### 4. C++ Plugin Updates
- Updated to use format-agnostic `mesh_file_path` parameter
- Created unified `import_mesh_asset.py` Python script
- Auto-detects format from file extension

### 5. Test FBX Created
- **UID**: `fbx_001`
- **File**: `R6ForUnreal.fbx` (110.2 KB)
- **Location**: `D:\vs\unreal-mcp\unreal-mcp\Python\data_storage\assets\objects3d\fbx\fbx_001\`
- **User**: TestFBXUser (ID: 999999)

## How to Test FBX Import

### Option 1: Direct MCP Command (Recommended)

Make sure Unreal project is open, then from Python directory:

```bash
cd D:\vs\unreal-mcp\unreal-mcp\Python
python -c "from tools.mcp_test_client import test_import; test_import('fbx_001')"
```

### Option 2: Via HTTP Bridge

```bash
curl -X POST http://localhost:8080/process_natural_language \
  -H "Content-Type: application/json" \
  -d '{"input": "import 3D object with UID fbx_001"}'
```

### Option 3: Direct Python Script

Create a test script:

```python
import sys
sys.path.insert(0, 'D:/vs/unreal-mcp/unreal-mcp/Python')

from tools.ai.command_handlers.asset.import_object3d import Object3DImportHandler
from unreal_mcp_server import UnrealTCPConnection

# Connect to Unreal
connection = UnrealTCPConnection('localhost', 55557)
connection.connect()

# Execute import
handler = Object3DImportHandler()
params = {"uid": "fbx_001"}

# Validate
validated = handler.validate_command("import_object3d_by_uid", params)
print(f"Validation: {'✅ Passed' if validated.is_valid else '❌ Failed'}")

if validated.is_valid:
    # Preprocess
    processed = handler.preprocess_params("import_object3d_by_uid", params)
    print(f"Format: {processed['mesh_format']}")
    print(f"File: {processed['mesh_file_path']}")

    # Execute import
    result = handler.execute_command(connection, "import_object3d_by_uid", processed)
    print(f"Result: {result}")
```

## What to Check

### Success Indicators:
1. **Python logs** show:
   - `"Python Import: Starting FBX import from..."`
   - `"Python Import: import_asset_tasks() returned!"`
   - `"Python Import: SUCCESS - Asset imported to..."`

2. **Unreal Content Browser** shows:
   - Path: `/Game/UnrealMCP/Assets/Roblox/TestFBXUser_999999/`
   - Asset: `R6ForUnreal` (Static Mesh)

3. **No editor freeze** (this is the KEY test!)

### Failure Indicators:
- Editor freezes (same as OBJ issue)
- Python shows: `"Python Import: FAILED - No objects imported"`
- Error in Unreal output log

## Expected Import Path

The FBX will be imported to:
```
/Game/UnrealMCP/Assets/Roblox/TestFBXUser_999999/R6ForUnreal
```

## Files Modified

### Python Files:
- `tools/ai/uid_manager.py` - Added FBX counter
- `tools/ai/session_management/utils/path_manager.py` - Format detection
- `tools/ai/command_handlers/asset/import_object3d.py` - FBX validation
- `register_fbx_uid.py` - Registration script
- `test_fbx_import.py` - Verification script

### C++ Files:
- `UnrealMCPObject3DCommands.cpp` - Format-agnostic parameters

### Python Scripts in Unreal:
- `MCPGameProject/Plugins/UnrealMCP/Content/Python/import_mesh_asset.py` - Unified import
- `E:/CINEVStudio/CINEVStudio/Plugins/UnrealMCP/Content/Python/import_mesh_asset.py` - Copied

## Next Steps

1. **Test FBX import** using one of the methods above
2. **If FBX works without freezing**:
   - Integrate FBX download into Roblox pipeline
   - Update frontend to show format info
   - Add FBX conversion step to downloader

3. **If FBX still freezes**:
   - Consider async job-based approach
   - Implement manual import workflow with good UX
   - Document the Game Thread limitation

## Quick Verification

Run this to verify everything is set up:
```bash
cd D:\vs\unreal-mcp\unreal-mcp\Python
python test_fbx_import.py
```

All checks should pass ✅