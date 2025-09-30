"""
Python script for importing OBJ assets via Unreal's EditorAssetLibrary.

This script runs outside the Game Thread, preventing the deadlock issue
that occurs when importing from C++ command handlers.

Usage from C++:
    ExecutePythonCommand("import sys; sys.path.append('path/to/script'); import import_obj_asset; import_obj_asset.import_obj('path/to/file.obj', '/Game/Destination/Path')")
"""

import unreal
import os

def import_obj(source_file_path, destination_package_path):
    """
    Import an OBJ file using Unreal's EditorAssetLibrary.

    Args:
        source_file_path (str): Absolute path to OBJ file (e.g., "D:/path/to/avatar.obj")
        destination_package_path (str): Package path in Unreal (e.g., "/Game/UnrealMCP/Assets/Roblox/User_123")

    Returns:
        dict: Result dictionary with success status and message
    """
    try:
        # Validate source file exists
        if not os.path.exists(source_file_path):
            return {
                "success": False,
                "error": f"Source file not found: {source_file_path}"
            }

        # Log import attempt
        unreal.log(f"Python Import: Starting OBJ import from {source_file_path}")
        unreal.log(f"Python Import: Destination package: {destination_package_path}")

        # Get AssetTools (correct way to import assets in UE5)
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

        # Create import task
        import_task = unreal.AssetImportTask()
        import_task.filename = source_file_path
        import_task.destination_path = destination_package_path
        import_task.automated = True  # Suppress UI dialogs
        import_task.save = True  # Save imported asset
        import_task.replace_existing = False  # Don't replace if exists

        unreal.log(f"Python Import: Created import task")
        unreal.log(f"  - filename: {import_task.filename}")
        unreal.log(f"  - destination: {import_task.destination_path}")

        # Execute import
        asset_tools.import_asset_tasks([import_task])

        # Check result
        if import_task.imported_object_paths and len(import_task.imported_object_paths) > 0:
            asset_path = import_task.imported_object_paths[0]
            unreal.log(f"Python Import: SUCCESS - Asset imported to {asset_path}")

            return {
                "success": True,
                "message": "Avatar imported to Content Browser",
                "asset_path": asset_path
            }
        else:
            unreal.log_error(f"Python Import: FAILED - No objects imported")
            return {
                "success": False,
                "error": "Import failed: import_asset_tasks() returned no objects"
            }

    except Exception as e:
        error_msg = f"Python Import: EXCEPTION - {str(e)}"
        unreal.log_error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

# Test function for manual execution
def test_import():
    """Test function for manual debugging"""
    test_obj = "D:/vs/unreal-mcp/unreal-mcp/Python/data_storage/assets/objects3d/obj/obj_029/avatar.obj"
    test_dest = "/Game/UnrealMCP/Assets/Roblox/Test"

    result = import_obj(test_obj, test_dest)
    unreal.log(f"Test Result: {result}")
    return result