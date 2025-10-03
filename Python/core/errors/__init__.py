"""
Core error handling system for MegaMelange backend.

Usage:
    from core.errors import AppError, ErrorCategory, ImageError, image_not_found
    from core.errors import handle_request_errors, retry_external_api

Example:
    # Raise structured error
    raise image_not_found("img_999", request_id="req_abc123")

    # Use decorator
    @handle_request_errors()
    def my_handler(params):
        if not valid:
            raise ImageError(...)
        return result
"""

from .base import AppError, ErrorCategory, CATEGORY_STATUS_MAP
from .middleware import handle_request_errors
from .retry import retry_external_api, retry_unreal_command, retry_with_rate_limit_respect, TENACITY_AVAILABLE
from .domains import (
    ImageError, ImageErrorCodes, image_not_found, image_size_exceeded,
    transformation_failed, api_unavailable,
    VideoError, VideoErrorCodes, video_not_found, video_size_exceeded,
    video_generation_failed, video_api_unavailable, invalid_video_duration,
    UnrealError, UnrealErrorCodes, connection_failed, connection_timeout,
    command_failed, actor_not_found, asset_not_found, screenshot_failed,
    plugin_not_found, invalid_transform, command_timeout,
    RobloxError, RobloxErrorCodes, user_not_found, invalid_user_input,
    api_rate_limited, avatar_3d_unavailable, download_failed, network_error,
    storage_error, uid_generation_failed, job_queue_full, job_timeout,
    permission_denied
)

__all__ = [
    # Base error system
    'AppError',
    'ErrorCategory',
    'CATEGORY_STATUS_MAP',

    # Middleware
    'handle_request_errors',

    # Retry policies
    'retry_external_api',
    'retry_unreal_command',
    'retry_with_rate_limit_respect',
    'TENACITY_AVAILABLE',

    # Image domain
    'ImageError',
    'ImageErrorCodes',
    'image_not_found',
    'image_size_exceeded',
    'transformation_failed',
    'api_unavailable',

    # Video domain
    'VideoError',
    'VideoErrorCodes',
    'video_not_found',
    'video_size_exceeded',
    'video_generation_failed',
    'video_api_unavailable',
    'invalid_video_duration',

    # Unreal domain
    'UnrealError',
    'UnrealErrorCodes',
    'connection_failed',
    'connection_timeout',
    'command_failed',
    'actor_not_found',
    'asset_not_found',
    'screenshot_failed',
    'plugin_not_found',
    'invalid_transform',
    'command_timeout',

    # Roblox domain
    'RobloxError',
    'RobloxErrorCodes',
    'user_not_found',
    'invalid_user_input',
    'api_rate_limited',
    'avatar_3d_unavailable',
    'download_failed',
    'network_error',
    'storage_error',
    'uid_generation_failed',
    'job_queue_full',
    'job_timeout',
    'permission_denied',
]
