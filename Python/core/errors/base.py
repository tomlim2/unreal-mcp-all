"""
Core error handling system for MegaMelange backend.
Provides structured errors with HTTP status mapping, logging, and retry hints.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import logging
import uuid

logger = logging.getLogger("MegaMelange.Errors")


class ErrorCategory(Enum):
    """Error categories with automatic HTTP status code mapping."""
    USER_INPUT = "user_input"
    EXTERNAL_API = "external_api"
    INTERNAL_SERVER = "internal_server"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PERMISSION = "permission"
    RATE_LIMIT = "rate_limit"


# HTTP status code mapping by category
CATEGORY_STATUS_MAP = {
    ErrorCategory.USER_INPUT: 400,
    ErrorCategory.RESOURCE_NOT_FOUND: 404,
    ErrorCategory.PERMISSION: 403,
    ErrorCategory.RATE_LIMIT: 429,
    ErrorCategory.EXTERNAL_API: 502,
    ErrorCategory.INTERNAL_SERVER: 500,
}


@dataclass
class AppError(Exception):
    """
    Base application error with structured information.

    Examples:
        >>> error = AppError(
        ...     code="IMG_NOT_FOUND",
        ...     message="Image img_004 not found",
        ...     category=ErrorCategory.RESOURCE_NOT_FOUND,
        ...     details={"uid": "img_004"},
        ...     suggestion="Check UID or upload new image"
        ... )
        >>> error.to_response()
    """
    code: str
    message: str
    category: ErrorCategory
    details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    retry_after: Optional[int] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = field(default_factory=lambda: f"err_{uuid.uuid4().hex[:12]}")
    status_code: int = field(init=False)

    def __post_init__(self):
        """Auto-assign HTTP status code based on category."""
        self.status_code = CATEGORY_STATUS_MAP.get(self.category, 500)

    def __str__(self) -> str:
        """Return string representation for exception handling."""
        return self.message

    def to_response(self) -> Dict[str, Any]:
        """Convert to HTTP response format."""
        response = {
            "success": False,
            "status_code": self.status_code,
            "error": {
                "code": self.code,
                "message": self.message,
                "category": self.category.value,
            }
        }

        if self.details:
            response["error"]["details"] = self.details

        if self.suggestion:
            response["error"]["suggestion"] = self.suggestion

        if self.retry_after:
            response["error"]["retry_after"] = self.retry_after

        if self.request_id:
            response["request_id"] = self.request_id

        if self.correlation_id:
            response["error"]["correlation_id"] = self.correlation_id

        return response

    def to_log(self) -> Dict[str, Any]:
        """Convert to structured log format (JSON-compatible)."""
        return {
            "error_code": self.code,
            "error_message": self.message,
            "error_category": self.category.value,
            "status_code": self.status_code,
            "details": self.details,
            "suggestion": self.suggestion,
            "retry_after": self.retry_after,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id
        }

    def log(self, level: str = "error", context: Optional[Dict[str, Any]] = None):
        """Log error with appropriate level and context."""
        log_data = self.to_log()
        if context:
            log_data["context"] = context

        # Choose log level based on category
        if self.category == ErrorCategory.RATE_LIMIT:
            logger.warning(f"[{self.code}] {self.message}", extra=log_data)
        elif self.category == ErrorCategory.RESOURCE_NOT_FOUND:
            logger.info(f"[{self.code}] {self.message}", extra=log_data)
        elif self.category in [ErrorCategory.EXTERNAL_API, ErrorCategory.INTERNAL_SERVER]:
            logger.error(f"[{self.code}] {self.message}", extra=log_data)
        else:
            getattr(logger, level)(f"[{self.code}] {self.message}", extra=log_data)
