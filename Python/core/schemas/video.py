"""
Video Schema Utilities

Standard schema builders for consistent video API responses.
Handles video generation from images and video processing operations.
"""

import time
from typing import Dict, Any
from pathlib import Path
from .base import get_current_timestamp, calculate_file_size


def build_video_transform_response(
    video_uid: str,
    parent_uid: str,
    filename: str,
    video_path: str,
    original_width: int,
    original_height: int,
    processed_width: int,
    processed_height: int,
    duration_seconds: int,
    prompt: str,
    aspect_ratio: str,
    resolution: str,
    cost: float,
    request_id: str,
    start_time: float,
    origin: str = "latest_screenshot_to_video"
) -> Dict[str, Any]:
    """Build standard schema response for video generation operations.

    Args:
        video_uid: Unique identifier for generated video
        parent_uid: UID of source image
        filename: Video filename
        video_path: Absolute path to video file
        original_width: Source image width
        original_height: Source image height
        processed_width: Output video width
        processed_height: Output video height
        duration_seconds: Video duration in seconds
        prompt: Generation prompt
        aspect_ratio: Video aspect ratio ("16:9" or "9:16")
        resolution: Video resolution ("720p" or "1080p")
        cost: Generation cost in USD
        request_id: Request tracking ID
        start_time: Operation start timestamp
        origin: Source type (default: "latest_screenshot_to_video")

    Returns:
        Standardized video generation response with metadata and cost tracking
    """
    duration_ms = int((time.time() - start_time) * 1000)
    file_size = calculate_file_size(video_path)

    return {
        "success": True,
        "status_code": 200,
        "message": f"Video generated successfully: {filename}",
        "uids": {
            "video": video_uid,
            "parent": parent_uid
        },
        "processing": {
            "model": "veo-3.0-generate-001",
            "origin": origin,
            "timestamp": get_current_timestamp(),
            "version": "1.0.0"
        },
        "video": {
            "url": f"/api/video/{filename}",
            "metadata": {
                "size": {
                    "original": f"{original_width}x{original_height}",
                    "processed": f"{processed_width}x{processed_height}"
                },
                "file_size": file_size,
                "duration": {
                    "seconds": duration_seconds,
                    "display": f"{duration_seconds}s"
                },
                "generation": {
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                    "has_audio": True,
                    "watermarked": True
                }
            }
        },
        "cost": {
            "currency": "USD",
            "value": cost,
            "display": f"${cost:.3f}",
            "pricing_model": "veo3_per_second_v1"
        },
        "audit": {
            "request_id": request_id,
            "duration_ms": duration_ms,
            "server": "veo3-video-node"
        }
    }


def extract_parent_filename(image_path: str) -> str:
    """Extract parent filename without extension for video naming.

    Args:
        image_path: Path to parent image file

    Returns:
        Filename stem (without extension)
    """
    try:
        path = Path(image_path)
        return path.stem  # Gets filename without extension
    except Exception:
        return "unknown_parent"


def generate_video_filename(parent_filename: str, timestamp: int) -> str:
    """Generate video filename using parent image filename + VEO3 + timestamp.

    Args:
        parent_filename: Parent image filename (without extension)
        timestamp: Unix timestamp for uniqueness

    Returns:
        Generated filename (e.g., "screenshot_VEO3_1696123456.mp4")
    """
    return f"{parent_filename}_VEO3_{timestamp}.mp4"
