"""
Asset renaming command handler.

Handles Unreal Engine asset renaming operations including getting selected assets
and batch renaming with various naming conventions.
"""

import logging
from typing import Dict, Any, List
from tools.ai.command_handlers.main import BaseCommandHandler
from tools.ai.command_handlers.validation import ValidatedCommand
from core.errors import (
    command_failed, connection_failed, command_timeout
)

logger = logging.getLogger("UnrealMCP")


class AssetRenameCommandHandler(BaseCommandHandler):
    """Handler for asset renaming commands.

    Purpose: Get selected assets and perform batch renaming operations

    Supported Commands:
    - get_selected_assets: Get array of currently selected assets in Content Browser
    - rename_assets_batch: Rename multiple assets at once

    Input Constraints:
    - get_selected_assets: No parameters required
    - rename_assets_batch: Requires 'operations' array with rename instructions
    """

    def get_supported_commands(self) -> List[str]:
        return ["get_selected_assets", "rename_assets_batch"]

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate asset commands with parameter checks."""
        errors = []

        if command_type == "rename_assets_batch":
            if "operations" not in params:
                errors.append("Missing required parameter: operations")
            elif not isinstance(params["operations"], list):
                errors.append("operations must be an array")
            else:
                # Validate each operation
                for idx, op in enumerate(params["operations"]):
                    if not isinstance(op, dict):
                        errors.append(f"Operation {idx} must be an object")
                        continue

                    if "old_path" not in op:
                        errors.append(f"Operation {idx} missing required field: old_path")
                    elif not isinstance(op["old_path"], str) or not op["old_path"].strip():
                        errors.append(f"Operation {idx} old_path must be a non-empty string")

                    if "new_name" not in op:
                        errors.append(f"Operation {idx} missing required field: new_name")
                    elif not isinstance(op["new_name"], str) or not op["new_name"].strip():
                        errors.append(f"Operation {idx} new_name must be a non-empty string")

        # get_selected_assets requires no parameters

        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )

    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute asset commands."""
        logger.info(f"Asset Rename Handler: Executing {command_type} with params: {params}")

        try:
            # Pass commands through to Unreal
            response = connection.send_command(command_type, params)

            if response and response.get("status") == "error":
                error_msg = response.get("error", "Unknown Unreal error")

                # Map specific errors
                if "no assets selected" in error_msg.lower():
                    raise command_failed(command_type, "No assets selected in Content Browser. Please select assets first.")
                elif "already exists" in error_msg.lower():
                    raise command_failed(command_type, f"Asset rename failed: {error_msg}")
                else:
                    raise command_failed(command_type, error_msg)

            return response

        except ConnectionError as e:
            logger.error(f"Connection to Unreal failed: {e}")
            raise connection_failed()
        except TimeoutError as e:
            logger.error(f"Asset command timed out: {e}")
            raise command_timeout(command_type)
        except Exception as e:
            logger.error(f"Asset command failed: {e}")
            raise command_failed(command_type, str(e))
