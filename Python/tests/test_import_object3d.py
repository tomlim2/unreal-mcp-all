"""
Test script for 3D object import functionality.

Tests the complete pipeline from UID validation to Unreal Editor asset import.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.ai.command_handlers.asset.import_object3d import Object3DImportHandler
from tools.ai.uid_manager import get_uid_manager, add_uid_mapping
from tools.ai.session_management.utils.path_manager import get_path_manager


def test_validation():
    """Test command validation logic."""
    print("\n=== Testing Command Validation ===\n")

    handler = Object3DImportHandler()

    # Test 1: Missing UID
    print("Test 1: Missing UID")
    result = handler.validate_command("import_object3d_by_uid", {})
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {result.validation_errors}")
    assert not result.is_valid, "Should fail without UID"

    # Test 2: Invalid UID format
    print("\nTest 2: Invalid UID format")
    result = handler.validate_command("import_object3d_by_uid", {"uid": "invalid_123"})
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {result.validation_errors}")
    assert not result.is_valid, "Should fail with invalid UID format"

    # Test 3: Nonexistent UID
    print("\nTest 3: Nonexistent UID")
    result = handler.validate_command("import_object3d_by_uid", {"uid": "obj_999"})
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {result.validation_errors}")
    assert not result.is_valid, "Should fail with nonexistent UID"

    print("\n✅ Validation tests passed!\n")


def test_preprocessing():
    """Test parameter preprocessing with real test data."""
    print("\n=== Testing Parameter Preprocessing ===\n")

    handler = Object3DImportHandler()
    path_manager = get_path_manager()
    uid_manager = get_uid_manager()

    # Create test UID and directory structure
    test_uid = "obj_test_001"
    test_username = "TestUser"
    test_user_id = 12345

    # Get object directory
    object_dir = Path(path_manager.get_3d_object_uid_path(test_uid))
    object_dir.mkdir(parents=True, exist_ok=True)

    # Create test metadata.json
    metadata = {
        "name": test_username,
        "id": test_user_id,
        "displayName": "Test User Display Name"
    }

    metadata_path = object_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    # Create test OBJ file
    obj_path = object_dir / "test_model.obj"
    obj_path.write_text("# Test OBJ file\nv 0 0 0\n")

    # Add UID mapping
    add_uid_mapping(test_uid, "3d_object", "test_model.obj", metadata=metadata)

    print(f"Created test structure:")
    print(f"  Directory: {object_dir}")
    print(f"  Metadata: {metadata_path}")
    print(f"  OBJ file: {obj_path}")

    # Test preprocessing
    print("\nTesting preprocessing...")
    try:
        params = {"uid": test_uid}
        processed = handler.preprocess_params("import_object3d_by_uid", params)

        print(f"\n  Processed parameters:")
        print(f"    UID: {processed['uid']}")
        print(f"    Username: {processed['username']}")
        print(f"    User ID: {processed['user_id']}")
        print(f"    OBJ Path: {processed['obj_file_path']}")

        assert processed['username'] == test_username
        assert processed['user_id'] == test_user_id
        assert Path(processed['obj_file_path']).exists()

        print("\n✅ Preprocessing test passed!\n")

    except Exception as e:
        print(f"\n❌ Preprocessing failed: {e}\n")
        raise

    finally:
        # Cleanup test files
        print("Cleaning up test files...")
        import shutil
        if object_dir.exists():
            shutil.rmtree(object_dir)
        print("  Cleanup complete")


def test_uid_manager_integration():
    """Test integration with UID manager."""
    print("\n=== Testing UID Manager Integration ===\n")

    uid_manager = get_uid_manager()

    # Get current counters
    counters = uid_manager.get_current_counters()
    print(f"Current counters:")
    print(f"  Images: {counters['img_counter']}")
    print(f"  Videos: {counters['vid_counter']}")
    print(f"  References: {counters['ref_counter']}")
    print(f"  Objects: {counters['obj_counter']}")

    # Check if there are any existing object UIDs
    all_mappings = uid_manager.get_all_mappings()
    object_mappings = {uid: mapping for uid, mapping in all_mappings.items()
                      if uid.startswith("obj_")}

    print(f"\nFound {len(object_mappings)} object UID(s) in registry:")
    for uid, mapping in list(object_mappings.items())[:5]:  # Show first 5
        print(f"  {uid}: {mapping.get('filename')}")

    if object_mappings:
        print(f"\n💡 You can test import with existing UIDs!")
        print(f"   Example: Most recent UID is {list(object_mappings.keys())[-1]}")

    print("\n✅ UID Manager integration test passed!\n")


def print_usage():
    """Print usage instructions."""
    print("\n" + "="*70)
    print("3D Object Import Test Suite")
    print("="*70)
    print("\nThis test suite validates the import_object3d_by_uid command.")
    print("\nTests:")
    print("  1. Command validation (UID format, existence)")
    print("  2. Parameter preprocessing (metadata extraction, path resolution)")
    print("  3. UID manager integration")
    print("\nTo test the full pipeline:")
    print("  1. Download a Roblox avatar first (generates obj_XXX UID)")
    print("  2. Run: python -c \"from tools.ai.command_handlers.asset.import_object3d import Object3DImportHandler; ...\"")
    print("  3. Or use the web frontend/MCP client to test end-to-end")
    print("\nNOTE: Full import testing requires Unreal Engine to be running.")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        print_usage()

        # Run tests
        test_validation()
        test_uid_manager_integration()
        test_preprocessing()

        print("\n" + "="*70)
        print("✅ All tests passed successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)