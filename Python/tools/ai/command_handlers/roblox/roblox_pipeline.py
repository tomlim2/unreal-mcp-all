"""
Unified Roblox avatar pipeline handler.

Combines download → convert → import into a single command for seamless UX.
Handles the full pipeline: download avatar, wait for completion, convert to FBX, import to Unreal.
"""

import logging
import time
from typing import Dict, Any, List
from pathlib import Path

from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand
from .roblox_errors import RobloxError, RobloxErrorHandler, RobloxErrorCodes
from .roblox_handler import RobloxCommandHandler
from .roblox_fbx_converter import RobloxFBXConverterHandler
from .roblox_job import get_job_status

logger = logging.getLogger("UnrealMCP.Roblox.Pipeline")


class RobloxPipelineHandler(BaseCommandHandler):
    """
    Unified pipeline handler for Roblox avatars.

    Orchestrates the full workflow:
    1. Download Roblox avatar (async)
    2. Wait for download completion (with polling)
    3. Convert OBJ → FBX
    4. Import FBX to Unreal Engine

    Supported Commands:
    - download_and_import_roblox_avatar: Full pipeline from user ID to imported asset
    """

    def __init__(self):
        super().__init__()
        self.download_handler = RobloxCommandHandler()
        self.fbx_converter = RobloxFBXConverterHandler()

    def get_supported_commands(self) -> List[str]:
        return ["download_and_import_roblox_avatar"]

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate pipeline command parameters."""
        errors = []
        validated_params = params.copy()

        if command_type == "download_and_import_roblox_avatar":
            # Required: user_input (user ID or username)
            user_input = params.get("user_input")
            if not user_input:
                errors.append("user_input is required (Roblox user ID or username)")
            elif not isinstance(user_input, str):
                errors.append("user_input must be a string")

            # Optional: session_id
            session_id = params.get("session_id")
            if session_id is not None and not isinstance(session_id, str):
                errors.append("session_id must be a string if provided")

            # Optional: blender_path
            blender_path = params.get("blender_path")
            if blender_path is not None and not isinstance(blender_path, str):
                errors.append("blender_path must be a string if provided")
        else:
            errors.append(f"Unknown command: {command_type}")

        return ValidatedCommand(
            type=command_type,
            params=validated_params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )

    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess parameters before execution."""
        processed = params.copy()

        # Add default blender path if not provided
        if "blender_path" not in processed or not processed["blender_path"]:
            processed["blender_path"] = r"D:\steam\steamapps\common\Blender\blender.exe"

        return processed

    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute unified pipeline command."""
        if command_type != "download_and_import_roblox_avatar":
            return {
                "success": False,
                "error": f"Unsupported command: {command_type}"
            }

        return self._execute_pipeline(connection, params)

    def _execute_pipeline(self, connection, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the full Roblox avatar pipeline.

        Steps:
        1. Start async download
        2. Poll for download completion
        3. Convert OBJ → FBX
        4. Import FBX to Unreal

        Returns:
            Pipeline result with all UIDs and asset path
        """
        user_input = params["user_input"]
        session_id = params.get("session_id")
        blender_path = params.get("blender_path")

        logger.info(f"Starting Roblox pipeline for user: {user_input}")

        try:
            # Step 1: Download Roblox avatar (async)
            logger.info("Step 1/4: Starting download...")
            download_params = {
                "user_input": user_input,
                "session_id": session_id
            }

            download_result = self.download_handler.execute_command(
                connection,
                "download_roblox_obj",
                download_params
            )

            if not download_result.get("success"):
                return {
                    "success": False,
                    "error": f"Download failed: {download_result.get('error', 'Unknown error')}",
                    "stage": "download"
                }

            obj_uid = download_result.get("uid")
            logger.info(f"Download queued: {obj_uid}")

            # Step 2: Wait for download completion (with polling)
            logger.info("Step 2/4: Waiting for download completion...")
            max_wait_time = 300  # 5 minutes
            poll_interval = 5  # 5 seconds
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                job_status = get_job_status(obj_uid)

                if job_status.get("status") == "completed":
                    logger.info(f"Download completed: {obj_uid}")
                    break
                elif job_status.get("status") == "failed":
                    return {
                        "success": False,
                        "error": f"Download failed: {job_status.get('error', 'Unknown error')}",
                        "stage": "download",
                        "obj_uid": obj_uid
                    }

                # Still queued or processing, wait and retry
                time.sleep(poll_interval)
                elapsed_time += poll_interval
                logger.debug(f"Waiting for download... {elapsed_time}/{max_wait_time}s")

            if elapsed_time >= max_wait_time:
                return {
                    "success": False,
                    "error": "Download timeout - avatar download took longer than 5 minutes",
                    "stage": "download",
                    "obj_uid": obj_uid,
                    "suggestion": "Try again or check the avatar complexity"
                }

            # Step 3: Convert OBJ → FBX
            logger.info("Step 3/4: Converting OBJ to FBX...")
            conversion_params = {
                "obj_uid": obj_uid,
                "blender_path": blender_path
            }

            fbx_result = self.fbx_converter.execute_command(
                connection,
                "convert_roblox_obj_to_fbx",
                conversion_params
            )

            if not fbx_result.get("success"):
                return {
                    "success": False,
                    "error": f"FBX conversion failed: {fbx_result.get('error', 'Unknown error')}",
                    "stage": "conversion",
                    "obj_uid": obj_uid
                }

            fbx_uid = fbx_result.get("fbx_uid")
            logger.info(f"Conversion completed: {fbx_uid}")

            # Step 4: Import FBX to Unreal Engine
            logger.info("Step 4/4: Importing to Unreal Engine...")

            # Import the FBX using the import handler
            from ..asset.import_object3d import Object3DImportHandler
            import_handler = Object3DImportHandler()

            import_params = {"uid": fbx_uid}

            # Validate first
            validated = import_handler.validate_command("import_object3d_by_uid", import_params)
            if not validated.is_valid:
                return {
                    "success": False,
                    "error": f"Import validation failed: {'; '.join(validated.validation_errors)}",
                    "stage": "import",
                    "obj_uid": obj_uid,
                    "fbx_uid": fbx_uid
                }

            # Preprocess and execute
            processed_import_params = import_handler.preprocess_params("import_object3d_by_uid", import_params)

            # IMPORTANT: Create fresh connection for import
            # The pipeline connection is stale after 5+ min of polling/conversion
            logger.info("Creating fresh connection for import (pipeline connection is stale)")
            from unreal_mcp_server import UnrealConnection
            fresh_connection = UnrealConnection()

            import_result = import_handler.execute_command(
                fresh_connection,
                "import_object3d_by_uid",
                processed_import_params
            )

            if not import_result.get("success"):
                return {
                    "success": False,
                    "error": f"Import failed: {import_result.get('error', 'Unknown error')}",
                    "stage": "import",
                    "obj_uid": obj_uid,
                    "fbx_uid": fbx_uid
                }

            asset_path = import_result.get("asset_path", "Unknown")
            logger.info(f"Import completed: {asset_path}")

            # Step 5: Return combined success result
            return {
                "success": True,
                "obj_uid": obj_uid,
                "fbx_uid": fbx_uid,
                "asset_path": asset_path,
                "message": f"Successfully downloaded and imported Roblox avatar for '{user_input}'",
                "pipeline_complete": True
            }

        except Exception as e:
            logger.exception(f"Pipeline execution failed: {e}")
            return {
                "success": False,
                "error": f"Pipeline failed: {str(e)}",
                "stage": "unknown"
            }
