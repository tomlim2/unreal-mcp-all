"""
Image Schema Utilities

Standard schema builders for consistent image API responses across all handlers.
Implements the hierarchical schema structure for screenshots, transformations, and future processing models.
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


def build_screenshot_response(
    image_uid: str,
    filename: str,
    image_path: str,
    width: int,
    height: int,
    request_id: str,
    start_time: float
) -> Dict[str, Any]:
    """Build standard schema response for screenshot operations."""
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
    """Build standard schema response for image transformation operations."""
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


def build_error_response(
    message: str,
    error_code: Optional[str] = None,
    request_id: Optional[str] = None,
    start_time: Optional[float] = None
) -> Dict[str, Any]:
    """Build standard error response."""
    response = {
        "success": False,
        "status_code": 400,
        "message": message
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if request_id and start_time:
        duration_ms = int((time.time() - start_time) * 1000)
        response["audit"] = {
            "request_id": request_id,
            "duration_ms": duration_ms,
            "server": "unreal-bridge"
        }
    
    return response


def extract_style_name(style_prompt: str) -> str:
    """Extract style name from style prompt for cleaner display."""
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