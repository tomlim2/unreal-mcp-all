"""Validation-specific error codes and exceptions."""

from ..base import AppError, ErrorCategory
from typing import Optional, List, Dict


class ValidationErrorCodes:
    """Standardized error codes for validation operations."""
    MISSING_REQUIRED = "VALIDATION_MISSING_REQUIRED"
    INVALID_TYPE = "VALIDATION_INVALID_TYPE"
    INVALID_VALUE = "VALIDATION_INVALID_VALUE"
    INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    CONSTRAINT_VIOLATION = "VALIDATION_CONSTRAINT_VIOLATION"


class ValidationError(AppError):
    """Validation-specific error."""
    def __init__(self, code: str, message: str, **kwargs):
        super().__init__(
            code=code,
            message=message,
            category=kwargs.pop('category', ErrorCategory.USER_INPUT),
            **kwargs
        )


# Helper functions for common validation errors

def validation_failed(
    message: str,
    missing_params: Optional[List[str]] = None,
    invalid_params: Optional[Dict[str, str]] = None,
    suggestion: Optional[str] = None,
    request_id: Optional[str] = None
) -> ValidationError:
    """Create generic validation failed error.

    Args:
        message: Human-readable error message
        missing_params: List of missing required parameters
        invalid_params: Dict of invalid params with reasons {param: reason}
        suggestion: Optional suggestion for fixing the error
        request_id: Optional request ID for tracking

    Returns:
        ValidationError with appropriate code and details

    Example:
        >>> raise validation_failed(
        ...     message="Either target_image_uid or main_image_data is required",
        ...     missing_params=["target_image_uid", "main_image_data"],
        ...     suggestion="Provide target_image_uid for existing screenshot or main_image_data for upload"
        ... )
    """
    details = {}
    if missing_params:
        details["missing_params"] = missing_params
    if invalid_params:
        details["invalid_params"] = invalid_params

    # Choose appropriate code based on error type
    code = ValidationErrorCodes.MISSING_REQUIRED if missing_params else ValidationErrorCodes.INVALID_VALUE

    return ValidationError(
        code=code,
        message=message,
        category=ErrorCategory.USER_INPUT,
        details=details if details else None,
        suggestion=suggestion,
        request_id=request_id
    )


def missing_required_param(param: str, request_id: Optional[str] = None) -> ValidationError:
    """Create missing required parameter error."""
    return ValidationError(
        code=ValidationErrorCodes.MISSING_REQUIRED,
        message=f"Missing required parameter: {param}",
        category=ErrorCategory.USER_INPUT,
        details={"missing_params": [param]},
        suggestion=f"Provide required parameter '{param}'",
        request_id=request_id
    )


def invalid_param_type(param: str, expected_type: str, actual_type: str, request_id: Optional[str] = None) -> ValidationError:
    """Create invalid parameter type error."""
    return ValidationError(
        code=ValidationErrorCodes.INVALID_TYPE,
        message=f"Parameter '{param}' must be {expected_type}, got {actual_type}",
        category=ErrorCategory.USER_INPUT,
        details={
            "param": param,
            "expected_type": expected_type,
            "actual_type": actual_type
        },
        suggestion=f"Provide '{param}' as {expected_type}",
        request_id=request_id
    )


def invalid_param_value(param: str, value: any, reason: str, request_id: Optional[str] = None) -> ValidationError:
    """Create invalid parameter value error."""
    return ValidationError(
        code=ValidationErrorCodes.INVALID_VALUE,
        message=f"Invalid value for parameter '{param}': {reason}",
        category=ErrorCategory.USER_INPUT,
        details={
            "param": param,
            "value": str(value),
            "reason": reason
        },
        request_id=request_id
    )


def invalid_param_format(param: str, expected_format: str, request_id: Optional[str] = None) -> ValidationError:
    """Create invalid parameter format error."""
    return ValidationError(
        code=ValidationErrorCodes.INVALID_FORMAT,
        message=f"Parameter '{param}' has invalid format",
        category=ErrorCategory.USER_INPUT,
        details={
            "param": param,
            "expected_format": expected_format
        },
        suggestion=f"Use format: {expected_format}",
        request_id=request_id
    )
