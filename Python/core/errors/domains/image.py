"""Image-specific error codes and exceptions."""

from ..base import AppError, ErrorCategory
from typing import Optional


class ImageErrorCodes:
    """Standardized error codes for image operations."""
    UID_NOT_FOUND = "IMG_UID_NOT_FOUND"
    INVALID_FORMAT = "IMG_INVALID_FORMAT"
    SIZE_EXCEEDED = "IMG_SIZE_EXCEEDED"
    UPLOAD_FAILED = "IMG_UPLOAD_FAILED"
    TRANSFORMATION_FAILED = "IMG_TRANSFORMATION_FAILED"
    GENERATION_FAILED = "IMG_GENERATION_FAILED"
    INVALID_DIMENSIONS = "IMG_INVALID_DIMENSIONS"
    PROCESSING_FAILED = "IMG_PROCESSING_FAILED"
    API_UNAVAILABLE = "IMG_API_UNAVAILABLE"


class ImageError(AppError):
    """Image-specific error."""
    def __init__(self, code: str, message: str, **kwargs):
        super().__init__(
            code=code,
            message=message,
            category=kwargs.pop('category', ErrorCategory.INTERNAL_SERVER),
            **kwargs
        )


# Helper functions for common image errors

def image_not_found(uid: str, request_id: Optional[str] = None) -> ImageError:
    """Create UID not found error."""
    return ImageError(
        code=ImageErrorCodes.UID_NOT_FOUND,
        message=f"Image {uid} not found",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        details={"uid": uid},
        suggestion="Check UID spelling or use /api/images to list available images",
        request_id=request_id
    )


def image_size_exceeded(size_mb: float, max_mb: float = 10, request_id: Optional[str] = None) -> ImageError:
    """Create size exceeded error."""
    return ImageError(
        code=ImageErrorCodes.SIZE_EXCEEDED,
        message=f"Image size {size_mb:.1f}MB exceeds limit of {max_mb}MB",
        category=ErrorCategory.USER_INPUT,
        details={"size_mb": size_mb, "max_mb": max_mb},
        suggestion=f"Compress image to under {max_mb}MB",
        request_id=request_id
    )


def invalid_image_format(mime_type: str, allowed_types: list, request_id: Optional[str] = None) -> ImageError:
    """Create invalid format error."""
    return ImageError(
        code=ImageErrorCodes.INVALID_FORMAT,
        message=f"Invalid image format: {mime_type}",
        category=ErrorCategory.USER_INPUT,
        details={"mime_type": mime_type, "allowed_types": allowed_types},
        suggestion=f"Use one of: {', '.join(allowed_types)}",
        request_id=request_id
    )


def image_transformation_failed(reason: str, model: str = "nanobanana", request_id: Optional[str] = None) -> ImageError:
    """Create transformation failed error."""
    return ImageError(
        code=ImageErrorCodes.TRANSFORMATION_FAILED,
        message=f"Image transformation failed: {reason}",
        category=ErrorCategory.EXTERNAL_API,
        details={"reason": reason, "model": model},
        suggestion="Try a different style or simpler prompt",
        request_id=request_id
    )


def image_generation_failed(reason: str, model: str = "gemini", request_id: Optional[str] = None) -> ImageError:
    """Create generation failed error."""
    return ImageError(
        code=ImageErrorCodes.GENERATION_FAILED,
        message=f"Image generation failed: {reason}",
        category=ErrorCategory.EXTERNAL_API,
        details={"reason": reason, "model": model},
        suggestion="Try again or use a different model",
        request_id=request_id
    )


def image_api_unavailable(api_name: str, reason: str = "", request_id: Optional[str] = None) -> ImageError:
    """Create API unavailable error."""
    message = f"{api_name} API unavailable"
    if reason:
        message += f": {reason}"
    return ImageError(
        code=ImageErrorCodes.API_UNAVAILABLE,
        message=message,
        category=ErrorCategory.EXTERNAL_API,
        details={"api_name": api_name, "reason": reason},
        suggestion=f"Ensure {api_name} API credentials are configured",
        request_id=request_id
    )


# Aliases for convenience
transformation_failed = image_transformation_failed
api_unavailable = image_api_unavailable
