"""
Compatibility shim for roblox_errors imports.

This file maintains backward compatibility for existing code while redirecting
to the core.errors system. Use core.errors directly for new code.
"""

import logging
from typing import Dict, Any
from core.errors import (
    RobloxError as _RobloxError,
    RobloxErrorCodes as _RobloxErrorCodes,
    user_not_found,
    invalid_user_input,
    api_rate_limited,
    avatar_3d_unavailable,
    download_failed,
    network_error,
    storage_error,
    uid_generation_failed,
    job_queue_full,
    job_timeout,
    permission_denied,
    AppError,
    ErrorCategory
)

logger = logging.getLogger("UnrealMCP.Roblox")

# Re-export for compatibility
RobloxError = _RobloxError
RobloxErrorCodes = _RobloxErrorCodes


class RobloxErrorHandler:
    """Compatibility wrapper for error helper functions."""

    @staticmethod
    def user_not_found(user_input: str):
        return user_not_found(user_input)

    @staticmethod
    def invalid_user_input(user_input: str):
        return invalid_user_input(user_input)

    @staticmethod
    def api_rate_limited(retry_after: int = 30):
        return api_rate_limited(retry_after)

    @staticmethod
    def avatar_3d_unavailable(user_id: int, username: str = None):
        return avatar_3d_unavailable(user_id, username)

    @staticmethod
    def download_failed(file_type: str, reason: str = None):
        return download_failed(file_type, reason)

    @staticmethod
    def network_error(operation: str, error_details: str = None):
        return network_error(operation, error_details)

    @staticmethod
    def storage_error(operation: str, path: str = None):
        return storage_error(operation, path)

    @staticmethod
    def uid_generation_failed(reason: str = None):
        return uid_generation_failed(reason)

    @staticmethod
    def job_queue_full():
        return job_queue_full()

    @staticmethod
    def job_timeout(timeout_seconds: int):
        return job_timeout(timeout_seconds)

    @staticmethod
    def from_exception(exc: Exception, operation: str = "unknown") -> RobloxError:
        """Convert generic exception to standardized Roblox error."""
        exc_name = exc.__class__.__name__
        exc_msg = str(exc)

        # Map common exceptions to specific error codes
        if "rate limit" in exc_msg.lower() or "429" in exc_msg:
            return api_rate_limited()
        elif "not found" in exc_msg.lower() or "404" in exc_msg:
            return user_not_found("unknown")
        elif "network" in exc_msg.lower() or "connection" in exc_msg.lower():
            return network_error(operation, exc_msg)
        elif "permission" in exc_msg.lower() or "access" in exc_msg.lower():
            return permission_denied(operation)
        else:
            # Generic error for unhandled exceptions
            return download_failed(
                file_type=operation,
                reason=f"{exc_name}: {exc_msg}"
            )


def log_roblox_error(error: RobloxError, context: Dict[str, Any] = None):
    """Log Roblox error with appropriate level and context."""
    # Just use the built-in logging from AppError
    error.log()

    # Log extra context if provided
    if context:
        logger.debug(f"Error context: {context}")
