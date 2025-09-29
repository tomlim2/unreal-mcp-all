"""
Enhanced Roblox command handler with async download support and immediate UID responses.

Provides non-blocking user experience by returning UIDs immediately and processing downloads
in the background with comprehensive error handling and progress tracking.
"""

import logging
from typing import Dict, Any, List, Optional

from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand
from ...uid_manager import generate_object_uid
from .roblox_errors import RobloxError, RobloxErrorHandler, log_roblox_error, RobloxErrorCodes
from .roblox_job import submit_download_job, get_job_status, cancel_job
from .roblox_cleanup import cleanup_existing_roblox_downloads

logger = logging.getLogger("UnrealMCP.Roblox.Handler")


class RobloxCommandHandler(BaseCommandHandler):
    """
    Command handler for Roblox 3D avatar downloads with async processing.

    Features:
    - Immediate UID generation and response for non-blocking UX
    - Background job submission for long-running downloads
    - Comprehensive parameter validation and error handling
    - Session-based organization and cleanup
    - Status polling support for frontend integration

    Supported Commands:
    - download_roblox_obj: Download 3D avatar with async processing
    - get_roblox_download_status: Check status of ongoing download
    - cancel_roblox_download: Cancel ongoing download
    """

    def get_supported_commands(self) -> List[str]:
        """Return list of supported Roblox commands."""
        return [
            "download_roblox_obj",
            "get_roblox_download_status",
            "cancel_roblox_download"
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
            elif command_type == "get_roblox_download_status":
                errors.extend(self._validate_status_params(validated_params))
            elif command_type == "cancel_roblox_download":
                errors.extend(self._validate_cancel_params(validated_params))
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
            elif command_type == "get_roblox_download_status":
                return self._execute_get_status(params)
            elif command_type == "cancel_roblox_download":
                return self._execute_cancel(params)
            else:
                error = RobloxError(
                    code=RobloxErrorCodes.INVALID_USER_INPUT,
                    message=f"Unsupported command: {command_type}",
                    details={"command_type": command_type}
                )
                raise Exception(error.message)

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

        # Validate include_textures (optional, default True)
        include_textures = params.get("include_textures", True)
        if not isinstance(include_textures, bool):
            errors.append("include_textures must be a boolean")

        # Validate include_thumbnails (optional, default False)
        include_thumbnails = params.get("include_thumbnails", False)
        if not isinstance(include_thumbnails, bool):
            errors.append("include_thumbnails must be a boolean")

        return errors

    def _validate_status_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate parameters for get_roblox_download_status command."""
        errors = []

        # Validate uid (required)
        uid = params.get("uid")
        if not uid:
            errors.append("uid is required for status checks")
        elif not isinstance(uid, str):
            errors.append("uid must be a string")
        elif not uid.startswith("obj_"):
            errors.append("uid must be a valid object UID (obj_XXX format)")

        return errors

    def _validate_cancel_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate parameters for cancel_roblox_download command."""
        errors = []

        # Validate uid (required)
        uid = params.get("uid")
        if not uid:
            errors.append("uid is required for cancellation")
        elif not isinstance(uid, str):
            errors.append("uid must be a string")
        elif not uid.startswith("obj_"):
            errors.append("uid must be a valid object UID (obj_XXX format)")

        return errors

    def _execute_download(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Roblox avatar download command.

        Returns immediate response with UID and queues background job.
        Automatically cleans up existing downloads for the same user.
        """
        user_input = params["user_input"]
        session_id = params.get("session_id")
        include_textures = params.get("include_textures", True)
        include_thumbnails = params.get("include_thumbnails", False)

        try:
            logger.info(f"Starting Roblox download for '{user_input}' (session: {session_id})")

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

            # Submit background job
            job = submit_download_job(uid, user_input, session_id)

            # Prepare response message
            if cleanup_count > 0:
                cleanup_message = f" (replaced {cleanup_count} existing download{'s' if cleanup_count > 1 else ''})"
            else:
                cleanup_message = ""

            # Return immediate response
            response = {
                "success": True,
                "uid": uid,
                "status": "queued",
                "message": f"Roblox download queued for '{user_input}'{cleanup_message}",
                "user_input": user_input,
                "estimated_time": "2-5 minutes",
                "poll_url": f"/api/roblox-status/{uid}",
                "cleanup_info": {
                    "existing_downloads_cleaned": cleanup_count,
                    "reused_uid": reuse_uid is not None
                },
                "job_details": {
                    "include_textures": include_textures,
                    "include_thumbnails": include_thumbnails,
                    "session_id": session_id
                }
            }

            logger.info(f"Roblox download queued: {uid} for user '{user_input}' (cleanup: {cleanup_count})")
            return response

        except ValueError as e:
            # Handle job submission errors (e.g., duplicate UID)
            error = RobloxError(
                code=RobloxErrorCodes.UID_GENERATION_FAILED,
                message=f"Failed to queue download: {str(e)}",
                details={"user_input": user_input, "error": str(e)},
                suggestion="Please try again"
            )
            return error.to_dict()

        except Exception as e:
            # Handle unexpected errors
            error = RobloxErrorHandler.from_exception(e, "download queue")
            return error.to_dict()

    def _execute_get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute get download status command.

        Returns current status of the specified download job.
        """
        uid = params["uid"]

        try:
            status = get_job_status(uid)

            if status is None:
                error = RobloxError(
                    code=RobloxErrorCodes.USER_NOT_FOUND,  # Reusing appropriate code
                    message=f"Download job not found: {uid}",
                    details={"uid": uid},
                    suggestion="Check the UID or the job may have completed and been cleaned up"
                )
                return error.to_dict()

            # Add success field for consistency
            status["success"] = True

            logger.debug(f"Retrieved status for Roblox download: {uid}")
            return status

        except Exception as e:
            error = RobloxErrorHandler.from_exception(e, "status check")
            return error.to_dict()

    def _execute_cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute cancel download command.

        Cancels the specified download job if it's still running.
        """
        uid = params["uid"]

        try:
            cancelled = cancel_job(uid)

            if cancelled:
                response = {
                    "success": True,
                    "uid": uid,
                    "status": "cancelled",
                    "message": f"Download job {uid} has been cancelled"
                }
                logger.info(f"Cancelled Roblox download: {uid}")
            else:
                error = RobloxError(
                    code=RobloxErrorCodes.USER_NOT_FOUND,  # Reusing appropriate code
                    message=f"Download job not found or already completed: {uid}",
                    details={"uid": uid},
                    suggestion="Job may have already completed or been cleaned up"
                )
                response = error.to_dict()

            return response

        except Exception as e:
            error = RobloxErrorHandler.from_exception(e, "job cancellation")
            return error.to_dict()


# Convenience functions for external use
def download_roblox_avatar(user_input: str, session_id: Optional[str] = None,
                          include_textures: bool = True, include_thumbnails: bool = False) -> Dict[str, Any]:
    """
    Convenience function to download Roblox avatar.

    Args:
        user_input: Roblox username or user ID
        session_id: Optional session ID for organization
        include_textures: Whether to download texture files
        include_thumbnails: Whether to download 2D thumbnails

    Returns:
        Download response with UID and status
    """
    handler = RobloxCommandHandler()

    params = {
        "user_input": user_input,
        "session_id": session_id,
        "include_textures": include_textures,
        "include_thumbnails": include_thumbnails
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