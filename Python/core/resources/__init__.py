"""
Core Resources Module

Resource processing modules (images, videos, 3D objects, etc.)
"""

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
