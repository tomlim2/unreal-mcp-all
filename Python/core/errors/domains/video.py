"""Video-specific error codes and exceptions."""

from ..base import AppError, ErrorCategory
from typing import Optional


class VideoErrorCodes:
    """Standardized error codes for video operations."""
    UID_NOT_FOUND = "VIDEO_UID_NOT_FOUND"
    INVALID_FORMAT = "VIDEO_INVALID_FORMAT"
    SIZE_EXCEEDED = "VIDEO_SIZE_EXCEEDED"
    GENERATION_FAILED = "VIDEO_GENERATION_FAILED"
    PROCESSING_FAILED = "VIDEO_PROCESSING_FAILED"
    API_UNAVAILABLE = "VIDEO_API_UNAVAILABLE"
    INVALID_DURATION = "VIDEO_INVALID_DURATION"
    INVALID_RESOLUTION = "VIDEO_INVALID_RESOLUTION"


class VideoError(AppError):
    """Video-specific error."""
    def __init__(self, code: str, message: str, **kwargs):
        super().__init__(
            code=code,
            message=message,
            category=kwargs.pop('category', ErrorCategory.INTERNAL_SERVER),
            **kwargs
        )


# Helper functions for common video errors

def video_not_found(uid: str, request_id: Optional[str] = None) -> VideoError:
    """Create UID not found error."""
    return VideoError(
        code=VideoErrorCodes.UID_NOT_FOUND,
        message=f"Video {uid} not found",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        details={"uid": uid},
        suggestion="Check UID spelling or use /api/videos to list available videos",
        request_id=request_id
    )


def video_size_exceeded(size_mb: float, max_mb: float = 100, request_id: Optional[str] = None) -> VideoError:
    """Create size exceeded error."""
    return VideoError(
        code=VideoErrorCodes.SIZE_EXCEEDED,
        message=f"Video size {size_mb:.1f}MB exceeds limit of {max_mb}MB",
        category=ErrorCategory.USER_INPUT,
        details={"size_mb": size_mb, "max_mb": max_mb},
        suggestion=f"Compress video to under {max_mb}MB or reduce duration",
        request_id=request_id
    )


def video_generation_failed(reason: str, model: str = "veo", request_id: Optional[str] = None) -> VideoError:
    """Create generation failed error."""
    return VideoError(
        code=VideoErrorCodes.GENERATION_FAILED,
        message=f"Video generation failed: {reason}",
        category=ErrorCategory.EXTERNAL_API,
        details={"reason": reason, "model": model},
        suggestion="Try a simpler prompt or shorter duration",
        request_id=request_id
    )


def video_api_unavailable(api_name: str, reason: str = "", request_id: Optional[str] = None) -> VideoError:
    """Create API unavailable error."""
    message = f"{api_name} API unavailable"
    if reason:
        message += f": {reason}"
    return VideoError(
        code=VideoErrorCodes.API_UNAVAILABLE,
        message=message,
        category=ErrorCategory.EXTERNAL_API,
        details={"api_name": api_name, "reason": reason},
        suggestion=f"Ensure {api_name} API credentials are configured",
        request_id=request_id
    )


def invalid_video_duration(duration_s: float, max_duration_s: float = 30, request_id: Optional[str] = None) -> VideoError:
    """Create invalid duration error."""
    return VideoError(
        code=VideoErrorCodes.INVALID_DURATION,
        message=f"Video duration {duration_s}s exceeds maximum {max_duration_s}s",
        category=ErrorCategory.USER_INPUT,
        details={"duration_s": duration_s, "max_duration_s": max_duration_s},
        suggestion=f"Reduce video duration to {max_duration_s}s or less",
        request_id=request_id
    )


def invalid_video_format(mime_type: str, allowed_types: list, request_id: Optional[str] = None) -> VideoError:
    """Create invalid format error."""
    return VideoError(
        code=VideoErrorCodes.INVALID_FORMAT,
        message=f"Invalid video format: {mime_type}",
        category=ErrorCategory.USER_INPUT,
        details={"mime_type": mime_type, "allowed_types": allowed_types},
        suggestion=f"Use one of: {', '.join(allowed_types)}",
        request_id=request_id
    )
