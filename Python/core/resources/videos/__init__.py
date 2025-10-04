"""
Video Resource Processing Module

Central module for all video processing operations.

Copyright Policy:
- User uploads: In-memory only (no storage, no UID)
- Generated videos: Persistent with UID

Usage:
    from core.resources.videos import process_video, load_video_from_uid

    uid, video_data = process_video(
        video_request={'data': 'base64...', 'mime_type': 'video/mp4'},
        target_video_uid='vid_042'
    )
"""

from .processor import (
    VideoProcessor,
    process_video,
    load_video_from_uid
)

__all__ = [
    'VideoProcessor',
    'process_video',
    'load_video_from_uid'
]
