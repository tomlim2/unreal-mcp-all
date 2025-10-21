"""
Test script for FBX import via the import_object3d_by_uid command.

This script:
1. Verifies fbx_001 UID exists in the system
2. Tests the path resolution for FBX files
3. Simulates the import command to check parameter preparation
"""

import sys
from pathlib import Path

# Add Python tools to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.ai.uid_manager import get_uid_manager, get_uid_mapping
from tools.ai.session_management.utils.path_manager import get_path_manager
from tools.ai.command_handlers.asset.import_object3d import Object3DImportHandler

def test_fbx_import():
    """Test FBX import preparation"""
    print("=" * 60)
    print("FBX Import Test - Verification Phase")
    print("=" * 60)

    # Step 1: Verify UID exists
    print("\n[1] Checking UID Registration...")
    mapping = get_uid_mapping("fbx_001")

    if mapping:
        print(f"   ✅ UID found: fbx_001")
        print(f"   - Type: {mapping.get('type')}")
        print(f"   - Filename: {mapping.get('filename')}")
        print(f"   - User: {mapping.get('metadata', {}).get('username')} (ID: {mapping.get('metadata', {}).get('user_id')})")
    else:
        print("   ❌ UID not found: fbx_001")
        return False

    # Step 2: Verify path resolution
    print("\n[2] Checking Path Resolution...")
    path_manager = get_path_manager()
    fbx_path = path_manager.get_3d_object_uid_path("fbx_001")
    fbx_file = Path(fbx_path) / "R6ForUnreal.fbx"
    metadata_file = Path(fbx_path) / "metadata.json"

    print(f"   UID Directory: {fbx_path}")

    if fbx_file.exists():
        size_kb = fbx_file.stat().st_size / 1024
        print(f"   ✅ FBX file found: {fbx_file.name} ({size_kb:.1f} KB)")
    else:
        print(f"   ❌ FBX file NOT found: {fbx_file}")
        return False

    if metadata_file.exists():
        print(f"   ✅ Metadata found: {metadata_file.name}")
    else:
        print(f"   ❌ Metadata NOT found: {metadata_file}")
        return False

    # Step 3: Test import handler validation
    print("\n[3] Testing Import Handler...")
    handler = Object3DImportHandler()

    # Test validation
    params = {"uid": "fbx_001"}
    validated = handler.validate_command("import_object3d_by_uid", params)

    if validated.is_valid:
        print(f"   ✅ Validation passed")
    else:
        print(f"   ❌ Validation failed: {validated.validation_errors}")
        return False

    # Test preprocessing
    try:
        processed_params = handler.preprocess_params("import_object3d_by_uid", params)
        print(f"   ✅ Preprocessing successful")
        print(f"\n   Processed Parameters:")
        print(f"   - UID: {processed_params.get('uid')}")
        print(f"   - Format: {processed_params.get('mesh_format')}")
        print(f"   - File Path: {processed_params.get('mesh_file_path')}")
        print(f"   - Username: {processed_params.get('username')}")
        print(f"   - User ID: {processed_params.get('user_id')}")
    except Exception as e:
        print(f"   ❌ Preprocessing failed: {e}")
        return False

    # Step 4: Ready for import
    print("\n[4] Import Command Ready")
    print("   ✅ All checks passed - ready for Unreal import!")
    print(f"\n" + "=" * 60)
    print("Next Step: Test actual import in Unreal Engine")
    print("=" * 60)
    print("\nCommand to test FBX import:")
    print("  import_object3d_by_uid(uid='fbx_001')")
    print("\nThis will:")
    print("  1. Send FBX file path to C++ plugin")
    print("  2. Execute Python import script in Unreal")
    print("  3. Import to: /Game/UnrealMCP/Assets/Roblox/TestFBXUser_999999/")

    return True

if __name__ == "__main__":
    try:
        success = test_fbx_import()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)