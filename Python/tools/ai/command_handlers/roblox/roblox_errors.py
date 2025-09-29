"""
Standardized error handling system for Roblox 3D avatar downloads.

Provides structured error codes and user-friendly error messages for better frontend UX.
Each error includes a code, message, and optional details for debugging and user guidance.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("UnrealMCP.Roblox")


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


@dataclass
class RobloxError:
    """Structured error information for Roblox operations."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    retry_after: Optional[int] = None  # Seconds to wait before retry

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            "success": False,
            "error": self.message,
            "code": self.code
        }

        if self.details:
            result["details"] = self.details

        if self.suggestion:
            result["suggestion"] = self.suggestion

        if self.retry_after:
            result["retry_after"] = self.retry_after

        return result


class RobloxErrorHandler:
    """Central error handler for Roblox operations with user-friendly messages."""

    @staticmethod
    def user_not_found(user_input: str) -> RobloxError:
        """Handle user not found errors."""
        return RobloxError(
            code=RobloxErrorCodes.USER_NOT_FOUND,
            message=f"User '{user_input}' not found",
            details={
                "user_input": user_input,
                "input_type": "username" if not user_input.isdigit() else "user_id"
            },
            suggestion="Check username spelling or try user ID instead"
        )

    @staticmethod
    def invalid_user_input(user_input: str) -> RobloxError:
        """Handle invalid user input errors."""
        return RobloxError(
            code=RobloxErrorCodes.INVALID_USER_INPUT,
            message=f"Invalid user input: '{user_input}'",
            details={
                "user_input": user_input,
                "valid_formats": ["username (letters/numbers)", "user_id (numbers only)"]
            },
            suggestion="Provide a valid Roblox username or user ID"
        )

    @staticmethod
    def api_rate_limited(retry_after: int = 30) -> RobloxError:
        """Handle API rate limiting errors."""
        return RobloxError(
            code=RobloxErrorCodes.API_RATE_LIMITED,
            message="Roblox API rate limit exceeded",
            details={
                "reason": "Too many requests to Roblox API",
                "retry_after_seconds": retry_after
            },
            suggestion=f"Please wait {retry_after} seconds before trying again",
            retry_after=retry_after
        )

    @staticmethod
    def avatar_3d_unavailable(user_id: int, username: str = None) -> RobloxError:
        """Handle 3D avatar unavailable errors."""
        display_name = username or f"User {user_id}"
        return RobloxError(
            code=RobloxErrorCodes.AVATAR_3D_UNAVAILABLE,
            message=f"3D avatar not available for {display_name}",
            details={
                "user_id": user_id,
                "username": username,
                "reason": "User may not have a 3D avatar configured"
            },
            suggestion="Try a different user or check if the user has set up a 3D avatar"
        )

    @staticmethod
    def download_failed(file_type: str, reason: str = None) -> RobloxError:
        """Handle download failure errors."""
        message = f"Failed to download {file_type}"
        if reason:
            message += f": {reason}"

        return RobloxError(
            code=RobloxErrorCodes.DOWNLOAD_FAILED,
            message=message,
            details={
                "file_type": file_type,
                "failure_reason": reason
            },
            suggestion="Check internet connection or try again later"
        )

    @staticmethod
    def network_error(operation: str, error_details: str = None) -> RobloxError:
        """Handle network-related errors."""
        return RobloxError(
            code=RobloxErrorCodes.NETWORK_ERROR,
            message=f"Network error during {operation}",
            details={
                "operation": operation,
                "error_details": error_details
            },
            suggestion="Check internet connection and try again"
        )

    @staticmethod
    def storage_error(operation: str, path: str = None) -> RobloxError:
        """Handle storage/filesystem errors."""
        return RobloxError(
            code=RobloxErrorCodes.STORAGE_ERROR,
            message=f"Storage error during {operation}",
            details={
                "operation": operation,
                "path": path
            },
            suggestion="Check disk space and file permissions"
        )

    @staticmethod
    def uid_generation_failed(reason: str = None) -> RobloxError:
        """Handle UID generation failures."""
        return RobloxError(
            code=RobloxErrorCodes.UID_GENERATION_FAILED,
            message="Failed to generate unique identifier",
            details={
                "reason": reason
            },
            suggestion="Try again or contact support if problem persists"
        )

    @staticmethod
    def job_queue_full() -> RobloxError:
        """Handle job queue full errors."""
        return RobloxError(
            code=RobloxErrorCodes.JOB_QUEUE_FULL,
            message="Download queue is full",
            details={
                "reason": "Too many concurrent downloads in progress"
            },
            suggestion="Please wait for current downloads to complete",
            retry_after=60
        )

    @staticmethod
    def job_timeout(timeout_seconds: int) -> RobloxError:
        """Handle job timeout errors."""
        return RobloxError(
            code=RobloxErrorCodes.JOB_TIMEOUT,
            message=f"Download timed out after {timeout_seconds} seconds",
            details={
                "timeout_seconds": timeout_seconds,
                "reason": "Download took longer than expected"
            },
            suggestion="Large avatars may take longer. Try again or use a simpler avatar"
        )

    @staticmethod
    def from_exception(exc: Exception, operation: str = "unknown") -> RobloxError:
        """Convert generic exception to standardized Roblox error."""
        exc_name = exc.__class__.__name__
        exc_msg = str(exc)

        # Map common exceptions to specific error codes
        if "rate limit" in exc_msg.lower() or "429" in exc_msg:
            return RobloxErrorHandler.api_rate_limited()
        elif "not found" in exc_msg.lower() or "404" in exc_msg:
            return RobloxErrorHandler.user_not_found("unknown")
        elif "network" in exc_msg.lower() or "connection" in exc_msg.lower():
            return RobloxErrorHandler.network_error(operation, exc_msg)
        elif "permission" in exc_msg.lower() or "access" in exc_msg.lower():
            return RobloxError(
                code=RobloxErrorCodes.PERMISSION_DENIED,
                message=f"Permission denied during {operation}",
                details={"exception": exc_name, "message": exc_msg},
                suggestion="Check file permissions and try again"
            )
        else:
            # Generic error for unhandled exceptions
            return RobloxError(
                code=RobloxErrorCodes.DOWNLOAD_FAILED,
                message=f"Unexpected error during {operation}: {exc_msg}",
                details={
                    "exception_type": exc_name,
                    "exception_message": exc_msg,
                    "operation": operation
                },
                suggestion="Please try again or contact support"
            )


def log_roblox_error(error: RobloxError, context: Dict[str, Any] = None):
    """Log Roblox error with appropriate level and context."""
    log_data = {
        "error_code": error.code,
        "error_message": error.message,
        "error_details": error.details,
        "context": context or {}
    }

    # Choose log level based on error type
    if error.code in [RobloxErrorCodes.API_RATE_LIMITED, RobloxErrorCodes.JOB_QUEUE_FULL]:
        logger.warning(f"Roblox operation throttled: {error.code} - {error.message}", extra=log_data)
    elif error.code in [RobloxErrorCodes.USER_NOT_FOUND, RobloxErrorCodes.AVATAR_3D_UNAVAILABLE]:
        logger.info(f"Roblox user/content issue: {error.code} - {error.message}", extra=log_data)
    elif error.code in [RobloxErrorCodes.NETWORK_ERROR, RobloxErrorCodes.DOWNLOAD_FAILED]:
        logger.error(f"Roblox technical error: {error.code} - {error.message}", extra=log_data)
    else:
        logger.error(f"Roblox error: {error.code} - {error.message}", extra=log_data)