"""
Video Schema Utilities

Standard schema builders for consistent video API responses across all handlers.
Implements the hierarchical schema structure for video generation and processing models.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path


def generate_request_id() -> str:
    """Generate unique request ID for audit tracking."""
    return f"req_{uuid.uuid4().hex[:12]}"


def get_current_timestamp() -> str:
    """Get current ISO timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def calculate_file_size(file_path: str) -> Dict[str, Any]:
    """Calculate file size in bytes and display format."""
    try:
        file_size_bytes = Path(file_path).stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        return {
            "bytes": file_size_bytes,
            "display": f"{file_size_mb:.1f} MB"
        }
    except Exception:
        return {
            "bytes": 0,
            "display": "0.0 MB"
        }


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
    """Build standard schema response for video generation operations."""
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


# REMOVED: build_error_response() - replaced by core.errors.AppError system


def extract_parent_filename(image_path: str) -> str:
    """Extract parent filename without extension for video naming."""
    try:
        path = Path(image_path)
        return path.stem  # Gets filename without extension
    except Exception:
        return "unknown_parent"


def generate_video_filename(parent_filename: str, timestamp: int) -> str:
    """Generate video filename using parent image filename + VEO3 + timestamp."""
    return f"{parent_filename}_VEO3_{timestamp}.mp4"