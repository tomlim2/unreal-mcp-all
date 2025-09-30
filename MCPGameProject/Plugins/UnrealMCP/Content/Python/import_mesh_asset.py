"""
Python script for importing mesh assets (OBJ/FBX) via Unreal's AssetTools API.

This script runs outside the Game Thread, potentially avoiding the deadlock issue
that occurs when importing from C++ command handlers.

Supports both OBJ and FBX formats - automatically detects format from file extension.

Usage from C++:
    ExecutePythonCommand("exec(open(r'path/to/import_mesh_asset.py').read()); import_mesh(r'path/to/file', '/Game/Destination/Path')")
"""

import unreal
import os

def import_mesh(source_file_path, destination_package_path):
    """
    Import a mesh file (OBJ or FBX) using Unreal's AssetTools API.

    Args:
        source_file_path (str): Absolute path to mesh file (e.g., "D:/path/to/avatar.obj" or "D:/path/to/avatar.fbx")
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

        # Detect file format from extension
        _, ext = os.path.splitext(source_file_path)
        file_format = ext.lower().lstrip('.')

        # Log import attempt
        unreal.log(f"Python Import: Starting {file_format.upper()} import from {source_file_path}")
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
        unreal.log(f"  - format: {file_format.upper()}")

        # Execute import
        unreal.log(f"Python Import: Executing import_asset_tasks()...")
        asset_tools.import_asset_tasks([import_task])
        unreal.log(f"Python Import: import_asset_tasks() returned!")

        # Check result
        if import_task.imported_object_paths and len(import_task.imported_object_paths) > 0:
            asset_path = import_task.imported_object_paths[0]
            unreal.log(f"Python Import: SUCCESS - Asset imported to {asset_path}")

            return {
                "success": True,
                "message": f"{file_format.upper()} avatar imported to Content Browser",
                "asset_path": asset_path,
                "format": file_format
            }
        else:
            unreal.log_error(f"Python Import: FAILED - No objects imported")
            return {
                "success": False,
                "error": f"Import failed: import_asset_tasks() returned no objects for {file_format.upper()} file"
            }

    except Exception as e:
        error_msg = f"Python Import: EXCEPTION - {str(e)}"
        unreal.log_error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

# Test function for manual execution
def test_import_obj():
    """Test function for OBJ import"""
    test_obj = "D:/vs/unreal-mcp/unreal-mcp/Python/data_storage/assets/objects3d/obj/obj_029/avatar.obj"
    test_dest = "/Game/UnrealMCP/Assets/Roblox/Test_OBJ"

    result = import_mesh(test_obj, test_dest)
    unreal.log(f"Test OBJ Result: {result}")
    return result

def test_import_fbx():
    """Test function for FBX import"""
    test_fbx = "D:/download/roblox/OBJToFBX/R6ForUnreal.fbx"
    test_dest = "/Game/UnrealMCP/Assets/Roblox/Test_FBX"

    result = import_mesh(test_fbx, test_dest)
    unreal.log(f"Test FBX Result: {result}")
    return result