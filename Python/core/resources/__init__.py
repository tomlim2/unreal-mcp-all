"""
Core Resources Module

Resource processing modules (images, videos, 3D objects, UIDs, etc.)
"""

# UID Management
from .uid_manager import (
    generate_image_uid,
    generate_video_uid,
    generate_object_uid as generate_object3d_uid,
    add_uid_mapping,
    get_uid_mapping,
    get_children_by_parent_uid,
    get_mappings_by_session_id,
    delete_mappings_by_session_id,
    get_latest_image_uid
)

# Image resources
from .images import (
    ImageProcessor,
    process_main_image,
    process_reference_images,
    load_image_from_uid
)

# Video resources
from .videos import (
    VideoProcessor,
    process_video,
    load_video_from_uid
)

# 3D object resources
from .objects_3d import (
    Object3DProcessor,
    process_3d_object,
    load_3d_object_from_uid
)

__all__ = [
    # UID Management
    'generate_image_uid',
    'generate_video_uid',
    'generate_object3d_uid',
    'add_uid_mapping',
    'get_uid_mapping',
    'get_children_by_parent_uid',
    'get_mappings_by_session_id',
    'delete_mappings_by_session_id',
    'get_latest_image_uid',
    # Images
    'ImageProcessor',
    'process_main_image',
    'process_reference_images',
    'load_image_from_uid',
    # Videos
    'VideoProcessor',
    'process_video',
    'load_video_from_uid',
    # 3D Objects
    'Object3DProcessor',
    'process_3d_object',
    'load_3d_object_from_uid'
]
