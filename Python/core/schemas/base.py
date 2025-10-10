"""
Base Schema Utilities

Shared utilities for all schema builders across the application.
Provides common functions for request tracking, timestamps, and file metadata.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from pathlib import Path


def generate_request_id() -> str:
    """Generate unique request ID for audit tracking."""
    return f"req_{uuid.uuid4().hex[:12]}"


def get_current_timestamp() -> str:
    """Get current ISO timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def calculate_file_size(file_path: str) -> Dict[str, Any]:
    """Calculate file size in bytes and display format.

    Args:
        file_path: Absolute path to the file

    Returns:
        Dict with 'bytes' and 'display' keys
    """
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
