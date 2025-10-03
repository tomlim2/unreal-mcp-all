"""Domain-specific error codes and exceptions."""

from .image import (
    ImageError, ImageErrorCodes, image_not_found, image_size_exceeded,
    transformation_failed, api_unavailable
)
from .video import (
    VideoError, VideoErrorCodes, video_not_found, video_size_exceeded,
    video_generation_failed, video_api_unavailable, invalid_video_duration
)
from .unreal import (
    UnrealError,
    UnrealErrorCodes,
    connection_failed,
    connection_timeout,
    command_failed,
    actor_not_found,
    asset_not_found,
    screenshot_failed,
    plugin_not_found,
    invalid_transform,
    command_timeout
)
from .roblox import (
    RobloxError,
    RobloxErrorCodes,
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
    permission_denied
)
from .validation import (
    ValidationError,
    ValidationErrorCodes,
    validation_failed,
    missing_required_param,
    invalid_param_type,
    invalid_param_value,
    invalid_param_format
)

__all__ = [
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

    # Validation domain
    'ValidationError',
    'ValidationErrorCodes',
    'validation_failed',
    'missing_required_param',
    'invalid_param_type',
    'invalid_param_value',
    'invalid_param_format',
]
