"""
Centralized error handling middleware.

Builds standardized error responses for consistent error format.
"""

from typing import Optional, Dict, Any
from core.errors import AppError, CATEGORY_STATUS_MAP


def build_error_response(error: Exception, trace_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Build standardized error response from exception.

    Args:
        error: Exception that occurred
        trace_id: Optional trace ID for debugging

    Returns:
        Error response dict with consistent structure

    Handles:
        - AppError: Structured application errors with codes
        - Exception: Generic Python exceptions

    Response Format:
        {
            "error": "Error message",
            "code": "error_code",
            "category": "error_category",  # (for AppError only)
            "trace_id": "a3f2b4c1"         # (if provided)
        }
    """
    if isinstance(error, AppError):
        response = {
            'error': error.message,
            'code': error.code,
            'category': error.category.value
        }
    else:
        response = {
            'error': str(error),
            'code': 'internal_error'
        }

    if trace_id:
        response['trace_id'] = trace_id

    return response


def get_http_status_from_error(error: Exception) -> int:
    """
    Determine HTTP status code from exception.

    Args:
        error: Exception instance

    Returns:
        HTTP status code (400-599)

    Mapping:
        - AppError: Uses CATEGORY_STATUS_MAP
        - ValueError: 400 (Bad Request)
        - Exception: 500 (Internal Server Error)
    """
    if isinstance(error, AppError):
        return CATEGORY_STATUS_MAP.get(error.category, 500)
    elif isinstance(error, ValueError):
        return 400
    else:
        return 500
