"""
Schema Utilities

Standard schema builders for consistent API responses across all handlers.
Provides unified response formats for images, videos, and other media types.

Usage:
    from core.schemas import build_screenshot_response, build_transform_response
    from core.schemas.image import extract_style_name
    from core.schemas.video import generate_video_filename
    from core.schemas.base import generate_request_id
"""

# Base utilities
from .base import (
    generate_request_id,
    get_current_timestamp,
    calculate_file_size
)

# Image schema builders
from .image import (
    build_screenshot_response,
    build_transform_response,
    extract_style_name
)

# Video schema builders
from .video import (
    build_video_transform_response,
    extract_parent_filename,
    generate_video_filename
)

__all__ = [
    # Base utilities
    'generate_request_id',
    'get_current_timestamp',
    'calculate_file_size',

    # Image schemas
    'build_screenshot_response',
    'build_transform_response',
    'extract_style_name',

    # Video schemas
    'build_video_transform_response',
    'extract_parent_filename',
    'generate_video_filename'
]
