"""
Image Resource Processing Module

Central module for all image processing operations.

Copyright Policy:
- User uploads: In-memory only (no storage, no UID)
- Generated images: Persistent with UID

Usage:
    from core.resources.images import process_main_image

    uid, image_data = process_main_image(
        main_image_request={'data': 'base64...'},
        target_image_uid='img_075'
    )
"""

from .processor import (
    ImageProcessor,
    process_main_image,
    process_reference_images,
    load_image_from_uid
)

# Convenience functions (delegate to ImageProcessor)
encode_image_to_base64 = ImageProcessor.encode_image_to_base64
calculate_image_size_mb = ImageProcessor.calculate_image_size_mb

__all__ = [
    'ImageProcessor',
    'process_main_image',
    'process_reference_images',
    'load_image_from_uid',
    'encode_image_to_base64',
    'calculate_image_size_mb'
]
