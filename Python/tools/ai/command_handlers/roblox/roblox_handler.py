"""
Roblox command handler with synchronous download execution.

Executes downloads synchronously (blocks until complete) and returns complete results
with username and folder_path for immediate display. Aligned with FBX converter flow.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional

from ..main import BaseCommandHandler
from ..validation import ValidatedCommand
from core.resources.uid_manager import generate_object_uid
from core.errors import RobloxError, RobloxErrorCodes
from core.response import success_response
from .roblox_errors import RobloxErrorHandler, log_roblox_error
from .roblox_job import RobloxDownloadJob
from .roblox_cleanup import cleanup_existing_roblox_downloads

logger = logging.getLogger("UnrealMCP.Roblox.Handler")


class RobloxCommandHandler(BaseCommandHandler):
    """
    Command handler for Roblox 3D avatar downloads (synchronous).

    Features:
    - Synchronous download execution (blocks until complete)
    - Immediate complete results (like FBX converter)
    - Comprehensive parameter validation and error handling
    - Session-based organization and cleanup
    - Returns username and folder_path for UI display

    Supported Commands:
    - download_roblox_obj: Download 3D avatar (synchronous)
    """

    def get_supported_commands(self) -> List[str]:
        """Return list of supported Roblox commands."""
        return [
            "download_roblox_obj"
        ]

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """
        Validate Roblox command parameters.

        Args:
            command_type: Command to validate
            params: Parameters to validate

        Returns:
            ValidatedCommand with validation results
        """
        errors = []
        validated_params = params.copy()

        try:
            if command_type == "download_roblox_obj":
                errors.extend(self._validate_download_params(validated_params))
            else:
                errors.append(f"Unknown Roblox command: {command_type}")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            logger.exception(f"Validation exception for {command_type}: {e}")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Validation failed for {command_type}: {'; '.join(errors)}")

        return ValidatedCommand(command_type, validated_params, is_valid, errors)

    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """
        Execute validated Roblox command.

        Args:
            connection: Unreal connection (not used for Roblox commands)
            command_type: Validated command type
            params: Validated and preprocessed parameters

        Returns:
            Command execution result
        """
        try:
            if command_type == "download_roblox_obj":
                return self._execute_download(params)
            else:
                error = RobloxError(
                    code=RobloxErrorCodes.INVALID_USER_INPUT,
                    message=f"Unsupported command: {command_type}",
                    details={"command_type": command_type}
                )
                raise error

        except Exception as exc:
            logger.exception(f"Failed to execute {command_type}: {exc}")

            # Convert to standardized error if needed
            if isinstance(exc, RobloxError):
                error = exc
            else:
                error = RobloxErrorHandler.from_exception(exc, f"{command_type} execution")

            log_roblox_error(error, {
                "command_type": command_type,
                "params": params
            })

            # Return error dict for consistency with other handlers
            return error.to_dict()

    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess parameters before execution.

        Args:
            command_type: Command being processed
            params: Validated parameters

        Returns:
            Preprocessed parameters
        """
        processed = params.copy()

        # Clean up user input for download commands
        if command_type == "download_roblox_obj" and "user_input" in processed:
            user_input = processed["user_input"].strip()

            # Remove common prefixes that users might include
            prefixes_to_remove = ["@", "user:", "id:", "roblox:", "username:"]
            for prefix in prefixes_to_remove:
                if user_input.lower().startswith(prefix):
                    user_input = user_input[len(prefix):].strip()

            processed["user_input"] = user_input

        # Add default values
        if "session_id" not in processed or not processed["session_id"]:
            processed["session_id"] = None

        return processed

    def _validate_download_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate parameters for download_roblox_obj command."""
        errors = []

        # Validate user_input (required)
        user_input = params.get("user_input")
        if not user_input:
            errors.append("user_input is required for Roblox downloads")
        elif not isinstance(user_input, str):
            errors.append("user_input must be a string")
        elif not user_input.strip():
            errors.append("user_input cannot be empty")
        else:
            user_input = user_input.strip()
            # Basic validation - allow alphanumeric usernames and numeric user IDs
            if not user_input.replace("_", "").replace("-", "").isalnum():
                errors.append("user_input must contain only letters, numbers, underscores, and hyphens")
            elif len(user_input) > 50:  # Reasonable username length limit
                errors.append("user_input is too long (max 50 characters)")

        # Validate session_id (optional)
        session_id = params.get("session_id")
        if session_id is not None and not isinstance(session_id, str):
            errors.append("session_id must be a string if provided")

        return errors

    def _execute_download(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Roblox avatar download command asynchronously.

        Starts download job in background and returns UID immediately.
        Use get_job_status() to poll for completion.
        """
        user_input = params["user_input"]
        session_id = params.get("session_id")

        try:
            logger.info(f"Starting synchronous Roblox download for '{user_input}' (session: {session_id})")

            # Check for existing downloads and clean them up
            reuse_uid, cleanup_count = cleanup_existing_roblox_downloads(
                user_input,
                session_id,
                reuse_uid=True
            )

            # Use reused UID or generate new one
            if reuse_uid:
                uid = reuse_uid
                logger.info(f"Reusing UID {uid} for user '{user_input}' (cleaned up {cleanup_count} existing downloads)")
            else:
                uid = generate_object_uid()
                if cleanup_count > 0:
                    logger.info(f"Generated new UID {uid} for user '{user_input}' (cleaned up {cleanup_count} existing downloads)")
                else:
                    logger.info(f"Generated new UID {uid} for user '{user_input}' (no existing downloads)")

            # Submit download job for async processing
            from .roblox_job import submit_download_job
            job = submit_download_job(uid, user_input, session_id)

            # Return immediately with UID (job runs in background)
            logger.info(f"Roblox download started: {uid} for user '{user_input}'")

            return {
                "success": True,
                "uid": uid,
                "status": "queued",
                "message": f"Download queued for user '{user_input}'"
            }

        except Exception as e:
            # Handle errors
            error = RobloxErrorHandler.from_exception(e, "download execution")
            log_roblox_error(error, {
                "user_input": user_input,
                "session_id": session_id
            })
            return error.to_dict()


# Convenience functions for external use
def download_roblox_avatar(user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to download Roblox avatar.

    Args:
        user_input: Roblox username or user ID
        session_id: Optional session ID for organization

    Returns:
        Download response with UID and status
    """
    handler = RobloxCommandHandler()

    params = {
        "user_input": user_input,
        "session_id": session_id
    }

    # Validate and preprocess
    validated = handler.validate_command("download_roblox_obj", params)
    if not validated.is_valid:
        error = RobloxError(
            code=RobloxErrorCodes.INVALID_USER_INPUT,
            message="Invalid parameters: " + "; ".join(validated.validation_errors),
            details={"validation_errors": validated.validation_errors}
        )
        return error.to_dict()

    processed_params = handler.preprocess_params("download_roblox_obj", validated.params)

    # Execute download
    return handler._execute_download(processed_params)


def get_download_status(uid: str) -> Dict[str, Any]:
    """
    Convenience function to get download status.

    Args:
        uid: Object UID to check

    Returns:
        Status information for the download
    """
    handler = RobloxCommandHandler()

    params = {"uid": uid}

    # Validate
    validated = handler.validate_command("get_roblox_download_status", params)
    if not validated.is_valid:
        error = RobloxError(
            code=RobloxErrorCodes.INVALID_USER_INPUT,
            message="Invalid UID: " + "; ".join(validated.validation_errors),
            details={"validation_errors": validated.validation_errors}
        )
        return error.to_dict()

    # Execute status check
    return handler._execute_get_status(validated.params)


def cancel_download(uid: str) -> Dict[str, Any]:
    """
    Convenience function to cancel download.

    Args:
        uid: Object UID to cancel

    Returns:
        Cancellation result
    """
    handler = RobloxCommandHandler()

    params = {"uid": uid}

    # Validate
    validated = handler.validate_command("cancel_roblox_download", params)
    if not validated.is_valid:
        error = RobloxError(
            code=RobloxErrorCodes.INVALID_USER_INPUT,
            message="Invalid UID: " + "; ".join(validated.validation_errors),
            details={"validation_errors": validated.validation_errors}
        )
        return error.to_dict()

    # Execute cancellation
    return handler._execute_cancel(validated.params)