"""
Video Resource Processor

Handles video processing for all APIs with copyright-safe approach.

Copyright Policy:
- User-uploaded videos: IN-MEMORY ONLY (no storage, no UID)
- Generated videos: PERSISTENT with UID assignment
"""

import base64
import logging
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger("UnrealMCP.Resources.Videos")


class VideoProcessor:
    """
    Central video resource processor.

    Responsibilities:
    - Decode/validate user-uploaded videos
    - Load videos from UID system
    - Enforce copyright policy (no storage for user uploads)
    """

    # Video constraints
    MAX_VIDEO_SIZE_MB = 100  # Larger than images
    ALLOWED_MIME_TYPES = {
        'video/mp4', 'video/mpeg', 'video/quicktime',
        'video/webm', 'video/x-msvideo'  # avi
    }

    @classmethod
    def decode_base64_video(cls, data_str: str, mime_type: str = 'video/mp4') -> Dict[str, Any]:
        """
        Decode base64 video data.

        Supports:
        - Data URI: data:video/mp4;base64,AAAAHGZ0...
        - Raw base64: AAAAHGZ0eXBpc29t...

        Args:
            data_str: Base64 encoded video data
            mime_type: MIME type if not in Data URI

        Returns:
            {'mime_type': str, 'data': bytes}

        Raises:
            ValueError: Invalid format or unsupported type
        """
        # Try Data URI format
        match = re.match(r"^data:(video/[\w\-]+);base64,(.*)", data_str)
        if match:
            mime_type, b64_data = match.groups()

            if mime_type not in cls.ALLOWED_MIME_TYPES:
                raise ValueError(
                    f"Unsupported video type: {mime_type}. "
                    f"Allowed: {cls.ALLOWED_MIME_TYPES}"
                )

            decoded_data = base64.b64decode(b64_data)
            return {"mime_type": mime_type, "data": decoded_data}

        # Fallback: raw base64
        if mime_type not in cls.ALLOWED_MIME_TYPES:
            mime_type = 'video/mp4'  # Default to MP4

        decoded_data = base64.b64decode(data_str)
        return {"mime_type": mime_type, "data": decoded_data}

    @classmethod
    def validate_video_size(cls, video_data: bytes, max_size_mb: int = None) -> None:
        """
        Validate video size.

        Raises:
            ValueError: If video exceeds limit
        """
        max_size = max_size_mb or cls.MAX_VIDEO_SIZE_MB
        size_mb = len(video_data) / (1024 * 1024)

        if size_mb > max_size:
            raise ValueError(
                f"Video too large: {size_mb:.2f}MB (max: {max_size}MB)"
            )


def process_video(
    video_request: Optional[Dict[str, Any]] = None,
    target_video_uid: Optional[str] = None
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Process video from request.

    Args:
        video_request: {'data': base64_str, 'mime_type': str}
        target_video_uid: Existing video UID (from render)

    Returns:
        (uid, video_data)
        - Option A (UID): (str, None) - Load from UID system
        - Option B (Upload): (None, Dict) - User-uploaded (in-memory)
        - Option C (Neither): (None, None) - No video provided

    Raises:
        ValueError: Invalid video format or size
    """
    # Priority 1: Load from UID
    if target_video_uid:
        logger.info(f"Loading video from UID: {target_video_uid}")
        return (target_video_uid, None)

    # Priority 2: Process user upload (IN-MEMORY, NO STORAGE)
    if video_request:
        data_str = video_request.get('data')
        mime_type = video_request.get('mime_type', 'video/mp4')

        if not data_str:
            raise ValueError("video_request missing 'data' field")

        # Decode
        decoded = VideoProcessor.decode_base64_video(data_str, mime_type)

        # Validate size
        VideoProcessor.validate_video_size(decoded['data'])

        logger.info(f"Processed user-uploaded video: {decoded['mime_type']}, "
                    f"{len(decoded['data']) / 1024 / 1024:.2f}MB (IN-MEMORY)")

        return (None, decoded)

    # No video provided
    return (None, None)


def load_video_from_uid(uid: str) -> Optional[Path]:
    """
    Load video file path from UID.

    Args:
        uid: Video UID (e.g., 'vid_042')

    Returns:
        Path to video file or None if not found
    """
    from tools.ai.uid_manager import get_uid_mapping

    mapping = get_uid_mapping(uid)
    if not mapping:
        logger.warning(f"Video UID not found: {uid}")
        return None

    # Get file path from mapping
    file_path = Path(mapping.get('file_path', ''))
    if not file_path.exists():
        logger.error(f"Video file not found: {file_path}")
        return None

    logger.info(f"Loaded video from UID {uid}: {file_path}")
    return file_path
