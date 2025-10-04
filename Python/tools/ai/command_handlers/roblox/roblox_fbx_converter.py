"""
Roblox OBJ to FBX converter command handler.

Handles conversion of downloaded Roblox OBJ avatars to FBX format for Unreal Engine.
Manages UID resolution, Blender script execution, and FBX UID registration.
"""

import logging
import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..main import BaseCommandHandler
from ..validation import ValidatedCommand
from core.resources.uid_manager import get_uid_manager, generate_object_uid
from core.utils.path_manager import get_path_manager
from core.errors import RobloxError, RobloxErrorCodes
from core.response import conversion_success
from .roblox_errors import RobloxErrorHandler, log_roblox_error

logger = logging.getLogger("UnrealMCP.Roblox.FBXConverter")


class RobloxFBXConverterHandler(BaseCommandHandler):
    """
    Command handler for converting Roblox OBJ downloads to FBX format.

    Features:
    - Resolves OBJ UID to file path
    - Executes Blender conversion script
    - Generates FBX UID and registers it
    - Validates conversion results
    - Handles Blender execution errors

    Supported Commands:
    - convert_roblox_obj_to_fbx: Convert OBJ UID to FBX UID
    """

    def __init__(self):
        super().__init__()
        self.uid_manager = get_uid_manager()
        self.path_manager = get_path_manager()

    def get_supported_commands(self) -> List[str]:
        """Return list of supported commands."""
        return ["convert_roblox_obj_to_fbx"]

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """
        Validate conversion command parameters.

        Args:
            command_type: Command to validate
            params: Parameters to validate

        Returns:
            ValidatedCommand with validation results
        """
        errors = []
        validated_params = params.copy()

        try:
            if command_type == "convert_roblox_obj_to_fbx":
                errors.extend(self._validate_conversion_params(validated_params))
            else:
                errors.append(f"Unknown command: {command_type}")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            logger.exception(f"Validation exception for {command_type}: {e}")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Validation failed for {command_type}: {'; '.join(errors)}")

        return ValidatedCommand(command_type, validated_params, is_valid, errors)

    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """
        Execute validated conversion command.

        Args:
            connection: Unreal connection (not used)
            command_type: Validated command type
            params: Validated parameters

        Returns:
            Command execution result
        """
        try:
            if command_type == "convert_roblox_obj_to_fbx":
                return self._execute_conversion(params)
            else:
                error = RobloxError(
                    code=RobloxErrorCodes.INVALID_USER_INPUT,
                    message=f"Unsupported command: {command_type}",
                    details={"command_type": command_type}
                )
                return error.to_dict()

        except Exception as exc:
            logger.exception(f"Failed to execute {command_type}: {exc}")

            if isinstance(exc, RobloxError):
                error = exc
            else:
                error = RobloxErrorHandler.from_exception(exc, f"{command_type} execution")

            log_roblox_error(error, {
                "command_type": command_type,
                "params": params
            })

            return error.to_dict()

    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess parameters before execution."""
        processed = params.copy()

        # Add default blender path if not provided
        if "blender_path" not in processed or not processed["blender_path"]:
            processed["blender_path"] = r"D:\steam\steamapps\common\Blender\blender.exe"

        return processed

    def _validate_conversion_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate parameters for convert_roblox_obj_to_fbx command."""
        errors = []

        # Validate obj_uid (required)
        obj_uid = params.get("obj_uid")
        if not obj_uid:
            errors.append("obj_uid is required for conversion")
        elif not isinstance(obj_uid, str):
            errors.append("obj_uid must be a string")
        elif not obj_uid.startswith("obj_"):
            errors.append("obj_uid must be a valid object UID (obj_XXX format)")

        # Validate blender_path (optional)
        blender_path = params.get("blender_path")
        if blender_path is not None and not isinstance(blender_path, str):
            errors.append("blender_path must be a string if provided")

        return errors

    def _execute_conversion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute OBJ to FBX conversion.

        Args:
            params: Validated parameters containing obj_uid

        Returns:
            Conversion result with FBX UID
        """
        obj_uid = params["obj_uid"]
        blender_path = params.get("blender_path", "blender")

        logger.info(f"Starting OBJ to FBX conversion for UID: {obj_uid}")

        try:
            # Step 1: Resolve OBJ UID to path
            obj_mapping = self._resolve_obj_uid(obj_uid)
            obj_path = self._get_obj_file_path(obj_uid, obj_mapping)

            if not obj_path or not Path(obj_path).exists():
                error = RobloxError(
                    code=RobloxErrorCodes.DOWNLOAD_FAILED,
                    message=f"OBJ file not found for UID: {obj_uid}",
                    details={"obj_uid": obj_uid, "obj_path": obj_path},
                    suggestion="Ensure the OBJ has been downloaded successfully"
                )
                return error.to_dict()

            logger.info(f"Resolved OBJ path: {obj_path}")

            # Step 2: Check if avatar is R6 type (only R6 supported for FBX conversion)
            obj_dir = Path(obj_path).parent
            metadata_file = obj_dir / "metadata.json"

            if not metadata_file.exists():
                error = RobloxError(
                    code=RobloxErrorCodes.METADATA_UNAVAILABLE,
                    message=f"Metadata file not found for {obj_uid}",
                    details={"obj_uid": obj_uid, "expected_path": str(metadata_file)},
                    suggestion="The downloaded OBJ is missing metadata. Try re-downloading the avatar."
                )
                return error.to_dict()

            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    avatar_type = metadata.get("avatar_type", "Unknown")

                    if avatar_type != "R6":
                        username = metadata.get("user_info", {}).get("name", "Unknown")
                        error = RobloxError(
                            code=RobloxErrorCodes.AVATAR_PROCESSING_FAILED,
                            message=f"Only R6 avatars are supported for FBX conversion",
                            details={
                                "obj_uid": obj_uid,
                                "username": username,
                                "avatar_type": avatar_type,
                                "supported_types": ["R6"]
                            },
                            suggestion=f"This avatar uses {avatar_type} body type. Currently only R6 avatars can be converted to FBX format with rigging for Unreal Engine."
                        )
                        return error.to_dict()

                    logger.info(f"Avatar type check passed: {avatar_type}")

            except json.JSONDecodeError as e:
                error = RobloxError(
                    code=RobloxErrorCodes.METADATA_UNAVAILABLE,
                    message="Failed to parse metadata file",
                    details={"obj_uid": obj_uid, "error": str(e)},
                    suggestion="The metadata file is corrupted. Try re-downloading the avatar."
                )
                return error.to_dict()
            except Exception as e:
                error = RobloxError(
                    code=RobloxErrorCodes.AVATAR_PROCESSING_FAILED,
                    message=f"Failed to validate avatar type: {str(e)}",
                    details={"obj_uid": obj_uid, "error": str(e)},
                    suggestion="Could not read avatar metadata. Check the OBJ download."
                )
                return error.to_dict()

            # Step 3: Allocate FBX UID and create output directory
            fbx_uid = self.uid_manager.get_next_fbx_uid()
            session_id = obj_mapping.get("session_id")
            fbx_dir = Path(self.path_manager.get_3d_object_uid_path(fbx_uid, session_id))
            fbx_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Allocated FBX UID: {fbx_uid}, directory: {fbx_dir}")

            # Step 4: Execute Blender conversion script
            try:
                fbx_path = self._run_blender_conversion(blender_path, obj_path, str(fbx_dir))

                if not fbx_path or not Path(fbx_path).exists():
                    # Rollback UID counter on failure
                    self._rollback_fbx_uid()
                    error = RobloxError(
                        code=RobloxErrorCodes.AVATAR_PROCESSING_FAILED,
                        message="FBX conversion failed - output file not created",
                        details={"obj_uid": obj_uid, "fbx_uid": fbx_uid, "expected_fbx_path": fbx_path},
                        suggestion="Check Blender installation and conversion script"
                    )
                    return error.to_dict()

                logger.info(f"FBX created: {fbx_path}")

            except RobloxError as e:
                # Rollback UID counter on conversion error
                self._rollback_fbx_uid()
                raise
            except Exception as e:
                # Rollback UID counter on any error
                self._rollback_fbx_uid()
                raise

            # Step 5: Register FBX UID with metadata
            self._register_fbx_metadata(fbx_uid, obj_uid, obj_mapping, fbx_path)

            logger.info(f"FBX UID registered: {fbx_uid}")

            # Step 6: Return success response using conversion_success helper
            logger.info(f"Conversion completed: {obj_uid} -> {fbx_uid}")
            return conversion_success(
                source_uid=obj_uid,
                target_uid=fbx_uid,
                source_type="obj",
                target_type="fbx",
                message=f"Successfully converted {obj_uid} to FBX format",
                additional_data={"fbx_path": fbx_path}
            )

        except RobloxError as e:
            return e.to_dict()
        except Exception as e:
            error = RobloxErrorHandler.from_exception(e, "FBX conversion")
            return error.to_dict()

    def _resolve_obj_uid(self, obj_uid: str) -> Dict[str, Any]:
        """
        Resolve OBJ UID to its mapping.

        Args:
            obj_uid: OBJ UID to resolve

        Returns:
            UID mapping dictionary

        Raises:
            RobloxError: If UID not found
        """
        all_mappings = self.uid_manager.get_all_mappings()
        mapping = all_mappings.get(obj_uid)

        if not mapping:
            raise RobloxError(
                code=RobloxErrorCodes.USER_NOT_FOUND,
                message=f"OBJ UID not found: {obj_uid}",
                details={"obj_uid": obj_uid},
                suggestion="Check the UID or download the Roblox avatar first"
            )

        # Verify it's a 3D object
        if mapping.get("type") != "3d_object":
            raise RobloxError(
                code=RobloxErrorCodes.INVALID_USER_INPUT,
                message=f"UID {obj_uid} is not a 3D object",
                details={"obj_uid": obj_uid, "actual_type": mapping.get("type")},
                suggestion="Provide a valid OBJ UID from a Roblox download"
            )

        return mapping

    def _get_obj_file_path(self, obj_uid: str, mapping: Dict[str, Any]) -> Optional[str]:
        """
        Get the OBJ file path from UID mapping.

        Args:
            obj_uid: OBJ UID
            mapping: UID mapping dictionary

        Returns:
            Path to avatar.obj file
        """
        # Get the UID directory path
        session_id = mapping.get("session_id")
        uid_dir = Path(self.path_manager.get_3d_object_uid_path(obj_uid, session_id))

        # Look for avatar.obj
        obj_file = uid_dir / "avatar.obj"

        if obj_file.exists():
            return str(obj_file)

        logger.warning(f"avatar.obj not found in {uid_dir}")
        return None

    def _run_blender_conversion(self, blender_path: str, obj_path: str, output_dir: str) -> Optional[str]:
        """
        Run Blender conversion script.

        Args:
            blender_path: Path to Blender executable
            obj_path: Path to OBJ file
            output_dir: Directory where FBX should be created

        Returns:
            Path to generated FBX file

        Raises:
            RobloxError: If Blender execution fails
        """
        # Get the conversion script path
        script_dir = Path(__file__).parent / "blender"
        conversion_script = script_dir / "roblox_obj2fbx.py"
        base_blend_file = script_dir / "Roblox_Base_R6_For_Unreal.blend"

        if not conversion_script.exists():
            raise RobloxError(
                code=RobloxErrorCodes.AVATAR_PROCESSING_FAILED,
                message="Blender conversion script not found",
                details={"script_path": str(conversion_script)},
                suggestion="Ensure the conversion script is in the correct location"
            )

        if not base_blend_file.exists():
            raise RobloxError(
                code=RobloxErrorCodes.AVATAR_PROCESSING_FAILED,
                message="Base Blender file not found",
                details={"blend_file": str(base_blend_file)},
                suggestion="Ensure Roblox_Base_R6_For_Unreal.blend is in the blender directory"
            )

        # Build Blender command
        cmd = [
            blender_path,
            "-b",  # Background mode
            str(base_blend_file),
            "-P", str(conversion_script),
            "--",
            str(obj_path),
            output_dir
        ]

        logger.info(f"Running Blender command: {' '.join(cmd)}")

        try:
            # Execute Blender
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Parse JSON output from script
            output_lines = result.stdout.strip().split('\n')
            json_output = None

            for line in reversed(output_lines):
                if line.startswith('{'):
                    try:
                        json_output = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue

            if not json_output:
                raise RobloxError(
                    code=RobloxErrorCodes.AVATAR_PROCESSING_FAILED,
                    message="Blender script did not return valid JSON output",
                    details={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    },
                    suggestion="Check Blender script for errors"
                )

            if not json_output.get("success"):
                error_message = json_output.get("error_message", "Unknown error")
                raise RobloxError(
                    code=RobloxErrorCodes.AVATAR_PROCESSING_FAILED,
                    message=f"Blender conversion failed: {error_message}",
                    details={
                        "blender_output": json_output,
                        "obj_path": obj_path
                    },
                    suggestion="Check the OBJ file and metadata"
                )

            fbx_path = json_output.get("fbx_path")
            logger.info(f"Blender conversion successful: {fbx_path}")

            return fbx_path

        except subprocess.TimeoutExpired:
            raise RobloxError(
                code=RobloxErrorCodes.JOB_TIMEOUT,
                message="Blender conversion timed out after 5 minutes",
                details={"obj_path": obj_path},
                suggestion="Try with a simpler avatar or check Blender installation"
            )
        except FileNotFoundError:
            raise RobloxError(
                code=RobloxErrorCodes.AVATAR_PROCESSING_FAILED,
                message=f"Blender executable not found: {blender_path}",
                details={"blender_path": blender_path},
                suggestion="Install Blender or provide the correct blender_path parameter"
            )

    def _rollback_fbx_uid(self):
        """Rollback FBX UID counter after failed conversion."""
        with self.uid_manager._lock:
            if self.uid_manager._fbx_counter > 0:
                self.uid_manager._fbx_counter -= 1
                logger.info(f"Rolled back FBX counter to {self.uid_manager._fbx_counter}")

    def _register_fbx_metadata(self, fbx_uid: str, obj_uid: str, obj_mapping: Dict[str, Any], fbx_path: str):
        """
        Register FBX UID with metadata and create metadata.json file.

        Args:
            fbx_uid: Generated FBX UID
            obj_uid: Original OBJ UID
            obj_mapping: Original OBJ mapping
            fbx_path: Path to generated FBX file
        """
        import json

        # Read the OBJ metadata.json file for user info
        session_id = obj_mapping.get("session_id")
        obj_dir = Path(self.path_manager.get_3d_object_uid_path(obj_uid, session_id))
        obj_metadata_file = obj_dir / "metadata.json"

        username = "unknown"
        user_id = 0

        if obj_metadata_file.exists():
            try:
                with open(obj_metadata_file, 'r', encoding='utf-8') as f:
                    obj_file_metadata = json.load(f)
                    user_info = obj_file_metadata.get("user_info", {})
                    username = user_info.get("name", "unknown")
                    user_id = user_info.get("id", 0)
            except Exception as e:
                logger.warning(f"Failed to read OBJ metadata: {e}")

        obj_metadata = obj_mapping.get("metadata", {})

        # Create FBX metadata
        fbx_metadata = {
            "conversion_type": "roblox_obj_to_fbx",
            "source_obj_uid": obj_uid,
            "username": username,
            "user_id": user_id,
            "converted_at": datetime.now().isoformat(),
            "original_download_metadata": obj_metadata
        }

        # Register FBX UID
        self.uid_manager.add_mapping(
            uid=fbx_uid,
            content_type="3d_object",
            filename=f"{username}_{user_id}_FBX",
            session_id=session_id,
            metadata=fbx_metadata
        )

        # Write metadata.json file in FBX directory
        fbx_dir = Path(fbx_path).parent
        metadata_file = fbx_dir / "metadata.json"

        metadata_content = {
            "uid": fbx_uid,
            "type": "fbx_model",
            "source": "roblox_conversion",
            "source_obj_uid": obj_uid,
            "username": username,
            "user_id": user_id,
            "converted_at": datetime.now().isoformat(),
            "fbx_file": Path(fbx_path).name,
            "session_id": session_id
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_content, f, indent=2, ensure_ascii=False)

        logger.info(f"Registered FBX UID: {fbx_uid} for {username}_{user_id}")
        logger.info(f"Created metadata file: {metadata_file}")


# Convenience function
def convert_roblox_obj_to_fbx(obj_uid: str, blender_path: str = "blender") -> Dict[str, Any]:
    """
    Convenience function to convert Roblox OBJ to FBX.

    Args:
        obj_uid: OBJ UID to convert
        blender_path: Path to Blender executable (default: "blender")

    Returns:
        Conversion result with FBX UID
    """
    handler = RobloxFBXConverterHandler()

    params = {
        "obj_uid": obj_uid,
        "blender_path": blender_path
    }

    # Validate
    validated = handler.validate_command("convert_roblox_obj_to_fbx", params)
    if not validated.is_valid:
        error = RobloxError(
            code=RobloxErrorCodes.INVALID_USER_INPUT,
            message="Invalid parameters: " + "; ".join(validated.validation_errors),
            details={"validation_errors": validated.validation_errors}
        )
        return error.to_dict()

    processed_params = handler.preprocess_params("convert_roblox_obj_to_fbx", validated.params)

    # Execute conversion
    return handler._execute_conversion(processed_params)
