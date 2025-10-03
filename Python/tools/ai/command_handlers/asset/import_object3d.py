"""
3D Object import command handler for Unreal Editor asset import.

Handles importing downloaded 3D objects (OBJ files) as persistent Unreal Editor assets
in the plugin Content directory, organized by user identity (Username_UserId).
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand
from ...uid_manager import get_uid_manager, get_uid_mapping
from ...session_management.utils.path_manager import get_path_manager
from core.errors import (
    command_failed, asset_not_found, connection_failed,
    command_timeout, AppError, ErrorCategory
)
from core.response import success_response

logger = logging.getLogger("UnrealMCP")


class Object3DImportHandler(BaseCommandHandler):
    """
    Handler for 3D object import commands using UID-based file resolution.

    Purpose: Import downloaded Roblox 3D files (OBJ or FBX) as persistent Unreal Editor assets

    Features:
    - UID validation via UIDManager
    - File path resolution via PathManager
    - Format auto-detection (OBJ or FBX, prefers FBX if both exist)
    - Metadata extraction for user identity (username, user_id)
    - Import to plugin Content directory: /UnrealMCP/Assets/Roblox/[Username_UserId]/
    - Clean success/failure responses for frontend

    Workflow:
    1. Validate UID exists in UIDManager
    2. Read metadata.json for username and user_id
    3. Detect available formats (FBX > OBJ priority)
    4. Resolve UID to absolute file paths (FBX/OBJ, MTL, textures)
    5. Send paths + format + user info to C++ for Editor import
    6. Return simplified response (success/error + asset_path)
    """

    def get_supported_commands(self) -> List[str]:
        return ["import_object3d_by_uid"]

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """
        Validate import command parameters.

        Required:
        - uid: Object UID (must exist in UIDManager and have valid metadata)

        Validation Steps:
        1. Check UID format (obj_XXX)
        2. Check UID exists in UIDManager
        3. Verify object directory exists
        4. Verify metadata.json exists
        5. Verify OBJ file exists
        """
        errors = []

        # Validate UID parameter
        uid = params.get("uid")
        if not uid:
            errors.append("Missing required parameter: uid")
            return ValidatedCommand(command_type, params, False, errors)

        if not isinstance(uid, str):
            errors.append("uid must be a string")
            return ValidatedCommand(command_type, params, False, errors)

        if not (uid.startswith("obj_") or uid.startswith("fbx_")):
            errors.append("uid must be a valid 3D object UID (obj_XXX or fbx_XXX format)")
            return ValidatedCommand(command_type, params, False, errors)

        # Check if UID exists in UIDManager
        uid_mapping = get_uid_mapping(uid)
        if not uid_mapping:
            errors.append(f"Object UID not found in registry: {uid}")
            return ValidatedCommand(command_type, params, False, errors)

        # Verify object directory exists
        path_manager = get_path_manager()
        object_dir = Path(path_manager.get_3d_object_uid_path(uid))

        if not object_dir.exists():
            errors.append(f"Object directory not found: {object_dir}")
            return ValidatedCommand(command_type, params, False, errors)

        # Verify metadata.json exists
        metadata_path = object_dir / "metadata.json"
        if not metadata_path.exists():
            errors.append(f"Metadata file not found: {metadata_path}")
            return ValidatedCommand(command_type, params, False, errors)

        # Verify OBJ or FBX file exists
        fbx_files = list(object_dir.glob("*.fbx"))
        obj_files = list(object_dir.glob("*.obj"))

        if not fbx_files and not obj_files:
            errors.append(f"No 3D mesh file (OBJ or FBX) found in directory: {object_dir}")
            return ValidatedCommand(command_type, params, False, errors)

        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )

    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve UID to absolute file paths and extract user metadata.

        This is the key design: Python handles all path resolution and metadata extraction,
        C++ receives ready-to-use absolute paths and user information.

        Steps:
        1. Get object directory from PathManager
        2. Read metadata.json for username and user_id
        3. Find OBJ file (*.obj)
        4. Find MTL file (*.mtl) - optional
        5. Find textures directory - optional
        6. Package all paths for C++

        Returns:
            Preprocessed params with absolute file paths and user info
        """
        processed = params.copy()
        uid = processed["uid"]

        try:
            # Get object directory
            path_manager = get_path_manager()
            object_dir = Path(path_manager.get_3d_object_uid_path(uid))

            # Read metadata.json for user information
            metadata_path = object_dir / "metadata.json"
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Extract username and user_id (required for directory naming)
            # Handle multiple metadata structures
            if "user_info" in metadata:
                # Nested structure from Roblox API
                user_info = metadata["user_info"]
                username = user_info.get("name", user_info.get("displayName", "Unknown"))
                user_id = user_info.get("id", 0)
            elif "username" in metadata and "user_id" in metadata:
                # FBX conversion metadata (has username/user_id at root)
                username = metadata.get("username", "Unknown")
                user_id = metadata.get("user_id", 0)
            else:
                # Flat structure (legacy or other sources)
                username = metadata.get("name", "Unknown")
                user_id = metadata.get("id", 0)

            if not username or username == "Unknown" or user_id <= 0:
                raise ValueError(f"Invalid metadata: username='{username}', user_id={user_id}")

            processed["username"] = username
            processed["user_id"] = user_id

            logger.info(f"Resolved UID {uid} to user: {username} (ID: {user_id})")

            # Find FBX or OBJ file (prefer FBX if both exist)
            fbx_files = list(object_dir.glob("*.fbx"))
            obj_files = list(object_dir.glob("*.obj"))

            if fbx_files:
                # Prefer FBX format (Epic's native format, better import support)
                mesh_file = fbx_files[0]
                processed["mesh_file_path"] = str(mesh_file.absolute())
                processed["mesh_format"] = "fbx"
                logger.info(f"Found FBX file (preferred): {mesh_file.name}")
            elif obj_files:
                # Fallback to OBJ format
                mesh_file = obj_files[0]
                processed["mesh_file_path"] = str(mesh_file.absolute())
                processed["mesh_format"] = "obj"
                logger.info(f"Found OBJ file: {mesh_file.name}")
            else:
                raise FileNotFoundError(f"No 3D mesh file (FBX or OBJ) found in {object_dir}")

            # Find MTL file (optional)
            mtl_files = list(object_dir.glob("*.mtl"))
            if mtl_files:
                processed["mtl_file_path"] = str(mtl_files[0].absolute())
                logger.debug(f"Found MTL file: {mtl_files[0].name}")

            # Find textures directory (optional)
            textures_dir = object_dir / "textures"
            if textures_dir.exists() and textures_dir.is_dir():
                processed["textures_directory"] = str(textures_dir.absolute())
                texture_count = len(list(textures_dir.glob("*.png")))
                logger.debug(f"Found textures directory with {texture_count} textures")

            logger.info(f"Preprocessing complete for UID {uid}: {username}_{user_id}")
            logger.info(f"Format: {processed.get('mesh_format').upper()}, Path: {processed.get('mesh_file_path')}")
            logger.info(f"Full preprocessed params: {processed}")
            return processed

        except AppError:
            raise  # Re-raise AppError as-is
        except Exception as e:
            from core.errors import AppError, ErrorCategory
            logger.error(f"Failed to preprocess params for UID {uid}: {e}")
            raise AppError(
                code="IMPORT_PREP_FAILED",
                message=f"Failed to prepare import: {str(e)}",
                category=ErrorCategory.INTERNAL_SERVER,
                suggestion="Check UID exists and file paths are accessible"
            )

    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """
        Execute import command via TCP connection to Unreal C++ plugin.

        Sends preprocessed parameters (with absolute paths and user info) to C++.
        Returns simplified response for frontend consumption.

        Response Format (Success):
        {
            "success": true,
            "message": "Avatar imported to Content Browser",
            "uid": "obj_001",
            "username": "Builderman",
            "user_id": 156,
            "asset_path": "/UnrealMCP/Assets/Roblox/Builderman_156/avatar"
        }

        Response Format (Error):
        {
            "success": false,
            "error": "Error message",
            "uid": "obj_001"
        }
        """
        uid = params.get("uid")
        username = params.get("username")

        try:
            logger.info(f"Executing import for UID {uid}: {username}")
            logger.info(f"Sending to C++: command_type='{command_type}', params={params}")

            # Send command to C++ via TCP
            logger.info("About to call connection.send_command()...")
            response = connection.send_command(command_type, params)
            logger.info(f"Received response from C++: {response}")

            # Check for C++ errors
            if response and response.get("status") == "error":
                error_msg = response.get("error", "Unknown Unreal import error")
                logger.error(f"C++ import failed for {uid}: {error_msg}")

                # Map to appropriate error type
                if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    raise asset_not_found(params.get("mesh_file_path", uid))
                else:
                    raise command_failed(command_type, error_msg)

            # Build simplified success response
            asset_path = response.get("asset_path", "")
            logger.info(f"Import successful for {uid}: {asset_path}")

            return success_response(
                message=response.get("message", "Avatar imported to Content Browser"),
                data={
                    "uid": uid,
                    "username": username,
                    "user_id": params.get("user_id"),
                    "asset_path": asset_path
                }
            )

        except ConnectionError as e:
            logger.error(f"Connection to Unreal failed: {e}")
            raise connection_failed()
        except TimeoutError as e:
            logger.error(f"Import command timed out: {e}")
            raise command_timeout(command_type)
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Asset preparation failed for {uid}: {e}")
            raise AppError(
                code="ASSET_PREPARATION_FAILED",
                message=str(e),
                category=ErrorCategory.RESOURCE_NOT_FOUND,
                details={"uid": uid},
                suggestion="Ensure the asset files exist and metadata is valid"
            )
        except Exception as e:
            logger.exception(f"Import execution failed for UID {uid}: {e}")
            raise command_failed(command_type, str(e))