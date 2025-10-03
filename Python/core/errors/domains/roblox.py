"""Roblox-specific error codes and exceptions."""

from ..base import AppError, ErrorCategory
from typing import Optional, Dict, Any


class RobloxErrorCodes:
    """Standardized error codes for Roblox operations."""

    # User resolution errors
    USER_NOT_FOUND = "ROBLOX_USER_NOT_FOUND"
    INVALID_USER_INPUT = "ROBLOX_INVALID_INPUT"
    USER_RESOLUTION_FAILED = "ROBLOX_USER_RESOLUTION_FAILED"

    # API interaction errors
    API_RATE_LIMITED = "ROBLOX_API_RATE_LIMITED"
    API_UNAVAILABLE = "ROBLOX_API_UNAVAILABLE"
    NETWORK_ERROR = "ROBLOX_NETWORK_ERROR"

    # Avatar/content errors
    AVATAR_3D_UNAVAILABLE = "ROBLOX_3D_UNAVAILABLE"
    AVATAR_PROCESSING_FAILED = "ROBLOX_AVATAR_PROCESSING_FAILED"
    METADATA_UNAVAILABLE = "ROBLOX_METADATA_UNAVAILABLE"

    # Download errors
    DOWNLOAD_FAILED = "ROBLOX_DOWNLOAD_FAILED"
    CDN_UNAVAILABLE = "ROBLOX_CDN_UNAVAILABLE"
    FILE_CORRUPTION = "ROBLOX_FILE_CORRUPTION"

    # System errors
    STORAGE_ERROR = "ROBLOX_STORAGE_ERROR"
    UID_GENERATION_FAILED = "ROBLOX_UID_GENERATION_FAILED"
    PERMISSION_DENIED = "ROBLOX_PERMISSION_DENIED"

    # Async processing errors
    JOB_QUEUE_FULL = "ROBLOX_JOB_QUEUE_FULL"
    JOB_TIMEOUT = "ROBLOX_JOB_TIMEOUT"
    JOB_CANCELLED = "ROBLOX_JOB_CANCELLED"


class RobloxError(AppError):
    """Roblox-specific error."""
    def __init__(self, code: str, message: str, **kwargs):
        super().__init__(
            code=code,
            message=message,
            category=kwargs.pop('category', ErrorCategory.EXTERNAL_API),
            **kwargs
        )


# Helper functions for common Roblox errors

def user_not_found(user_input: str, request_id: Optional[str] = None) -> RobloxError:
    """Handle user not found errors."""
    return RobloxError(
        code=RobloxErrorCodes.USER_NOT_FOUND,
        message=f"User '{user_input}' not found",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        details={
            "user_input": user_input,
            "input_type": "username" if not user_input.isdigit() else "user_id"
        },
        suggestion="Check username spelling or try user ID instead",
        request_id=request_id
    )


def invalid_user_input(user_input: str, request_id: Optional[str] = None) -> RobloxError:
    """Handle invalid user input errors."""
    return RobloxError(
        code=RobloxErrorCodes.INVALID_USER_INPUT,
        message=f"Invalid user input: '{user_input}'",
        category=ErrorCategory.USER_INPUT,
        details={
            "user_input": user_input,
            "valid_formats": ["username (letters/numbers)", "user_id (numbers only)"]
        },
        suggestion="Provide a valid Roblox username or user ID",
        request_id=request_id
    )


def api_rate_limited(retry_after: int = 30, request_id: Optional[str] = None) -> RobloxError:
    """Handle API rate limiting errors."""
    return RobloxError(
        code=RobloxErrorCodes.API_RATE_LIMITED,
        message="Roblox API rate limit exceeded",
        category=ErrorCategory.RATE_LIMIT,
        details={
            "reason": "Too many requests to Roblox API",
            "retry_after_seconds": retry_after
        },
        suggestion=f"Please wait {retry_after} seconds before trying again",
        retry_after=retry_after,
        request_id=request_id
    )


def avatar_3d_unavailable(user_id: int, username: str = None, request_id: Optional[str] = None) -> RobloxError:
    """Handle 3D avatar unavailable errors."""
    display_name = username or f"User {user_id}"
    return RobloxError(
        code=RobloxErrorCodes.AVATAR_3D_UNAVAILABLE,
        message=f"3D avatar not available for {display_name}",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        details={
            "user_id": user_id,
            "username": username,
            "reason": "User may not have a 3D avatar configured"
        },
        suggestion="Try a different user or check if the user has set up a 3D avatar",
        request_id=request_id
    )


def download_failed(file_type: str, reason: str = None, request_id: Optional[str] = None) -> RobloxError:
    """Handle download failure errors."""
    message = f"Failed to download {file_type}"
    if reason:
        message += f": {reason}"

    return RobloxError(
        code=RobloxErrorCodes.DOWNLOAD_FAILED,
        message=message,
        category=ErrorCategory.EXTERNAL_API,
        details={
            "file_type": file_type,
            "failure_reason": reason
        },
        suggestion="Check internet connection or try again later",
        request_id=request_id
    )


def network_error(operation: str, error_details: str = None, request_id: Optional[str] = None) -> RobloxError:
    """Handle network-related errors."""
    return RobloxError(
        code=RobloxErrorCodes.NETWORK_ERROR,
        message=f"Network error during {operation}",
        category=ErrorCategory.EXTERNAL_API,
        details={
            "operation": operation,
            "error_details": error_details
        },
        suggestion="Check internet connection and try again",
        request_id=request_id
    )


def storage_error(operation: str, path: str = None, request_id: Optional[str] = None) -> RobloxError:
    """Handle storage/filesystem errors."""
    return RobloxError(
        code=RobloxErrorCodes.STORAGE_ERROR,
        message=f"Storage error during {operation}",
        category=ErrorCategory.INTERNAL_SERVER,
        details={
            "operation": operation,
            "path": path
        },
        suggestion="Check disk space and file permissions",
        request_id=request_id
    )


def uid_generation_failed(reason: str = None, request_id: Optional[str] = None) -> RobloxError:
    """Handle UID generation failures."""
    return RobloxError(
        code=RobloxErrorCodes.UID_GENERATION_FAILED,
        message="Failed to generate unique identifier",
        category=ErrorCategory.INTERNAL_SERVER,
        details={
            "reason": reason
        },
        suggestion="Try again or contact support if problem persists",
        request_id=request_id
    )


def job_queue_full(request_id: Optional[str] = None) -> RobloxError:
    """Handle job queue full errors."""
    return RobloxError(
        code=RobloxErrorCodes.JOB_QUEUE_FULL,
        message="Download queue is full",
        category=ErrorCategory.RATE_LIMIT,
        details={
            "reason": "Too many concurrent downloads in progress"
        },
        suggestion="Please wait for current downloads to complete",
        retry_after=60,
        request_id=request_id
    )


def job_timeout(timeout_seconds: int, request_id: Optional[str] = None) -> RobloxError:
    """Handle job timeout errors."""
    return RobloxError(
        code=RobloxErrorCodes.JOB_TIMEOUT,
        message=f"Download timed out after {timeout_seconds} seconds",
        category=ErrorCategory.EXTERNAL_API,
        details={
            "timeout_seconds": timeout_seconds,
            "reason": "Download took longer than expected"
        },
        suggestion="Large avatars may take longer. Try again or use a simpler avatar",
        request_id=request_id
    )


def permission_denied(operation: str, request_id: Optional[str] = None) -> RobloxError:
    """Handle permission denied errors."""
    return RobloxError(
        code=RobloxErrorCodes.PERMISSION_DENIED,
        message=f"Permission denied during {operation}",
        category=ErrorCategory.PERMISSION,
        details={"operation": operation},
        suggestion="Check file permissions and try again",
        request_id=request_id
    )
