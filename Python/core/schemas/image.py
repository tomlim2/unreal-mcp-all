"""
Image Schema Utilities

Standard schema builders for consistent image API responses.
Handles screenshot captures and image transformations (AI styling, filters, etc.).
"""

import time
from typing import Dict, Any
from .base import get_current_timestamp, calculate_file_size


def build_screenshot_response(
    image_uid: str,
    filename: str,
    image_path: str,
    width: int,
    height: int,
    request_id: str,
    start_time: float
) -> Dict[str, Any]:
    """Build standard schema response for screenshot operations.

    Args:
        image_uid: Unique identifier for the screenshot
        filename: Screenshot filename
        image_path: Absolute path to screenshot file
        width: Image width in pixels
        height: Image height in pixels
        request_id: Request tracking ID
        start_time: Operation start timestamp

    Returns:
        Standardized screenshot response with UIDs, metadata, and audit info
    """
    duration_ms = int((time.time() - start_time) * 1000)
    file_size = calculate_file_size(image_path)

    return {
        "success": True,
        "status_code": 200,
        "message": f"Screenshot saved: {filename}",
        "uids": {
            "image": image_uid
        },
        "processing": {
            "model": "unreal",
            "origin": "direct_capture",
            "timestamp": get_current_timestamp(),
            "version": "1.0.0"
        },
        "image": {
            "url": f"/api/screenshot/{filename}",
            "metadata": {
                "size": {
                    "processed": f"{width}x{height}"
                },
                "file_size": file_size
            }
        },
        "audit": {
            "request_id": request_id,
            "duration_ms": duration_ms,
            "server": "unreal-bridge"
        }
    }


def build_transform_response(
    image_uid: str,
    parent_uid: str,
    filename: str,
    image_path: str,
    original_width: int,
    original_height: int,
    processed_width: int,
    processed_height: int,
    style_name: str,
    style_prompt: str,
    intensity: float,
    tokens: int,
    cost: float,
    request_id: str,
    start_time: float,
    origin: str = "screenshot"
) -> Dict[str, Any]:
    """Build standard schema response for image transformation operations.

    Args:
        image_uid: Unique identifier for transformed image
        parent_uid: UID of the source image
        filename: Output filename
        image_path: Absolute path to transformed image
        original_width: Source image width
        original_height: Source image height
        processed_width: Output image width
        processed_height: Output image height
        style_name: Style identifier (e.g., "cyberpunk")
        style_prompt: Full style description
        intensity: Style intensity (0.0-1.0)
        tokens: Token count used
        cost: Processing cost in USD
        request_id: Request tracking ID
        start_time: Operation start timestamp
        origin: Source type ("screenshot" or "user_upload")

    Returns:
        Standardized transformation response with parent tracking and cost info
    """
    duration_ms = int((time.time() - start_time) * 1000)
    file_size = calculate_file_size(image_path)

    return {
        "success": True,
        "status_code": 200,
        "message": f"Image styled successfully: {filename}",
        "uids": {
            "image": image_uid,
            "parent": parent_uid
        },
        "processing": {
            "model": "nanobanana",
            "origin": origin,
            "timestamp": get_current_timestamp(),
            "version": "1.0.0"
        },
        "image": {
            "url": f"/api/screenshot/{filename}",
            "metadata": {
                "size": {
                    "original": f"{original_width}x{original_height}",
                    "processed": f"{processed_width}x{processed_height}"
                },
                "file_size": file_size,
                "style": {
                    "name": style_name,
                    "intensity": intensity,
                    "prompt": style_prompt
                }
            }
        },
        "cost": {
            "tokens": tokens,
            "currency": "USD",
            "value": cost,
            "pricing_model": "manual_config_v1"
        },
        "audit": {
            "request_id": request_id,
            "duration_ms": duration_ms,
            "server": "render-node-05"
        }
    }


def extract_style_name(style_prompt: str) -> str:
    """Extract style name from style prompt for cleaner display.

    Args:
        style_prompt: Full style description (e.g., "cyberpunk, neon lights, futuristic")

    Returns:
        Short style identifier (e.g., "cyberpunk")
    """
    # Simple extraction - take first word or phrase before comma
    style_name = style_prompt.split(',')[0].strip().lower()

    # Common style mappings
    style_mappings = {
        "cyberpunk": "cyberpunk",
        "anime": "anime",
        "watercolor": "watercolor",
        "oil painting": "oil_painting",
        "sketch": "sketch",
        "cartoon": "cartoon",
        "photorealistic": "photorealistic",
        "abstract": "abstract"
    }

    # Check for known styles
    for key, value in style_mappings.items():
        if key in style_name:
            return value

    # Default to cleaned first word
    return style_name.replace(' ', '_')[:20]
