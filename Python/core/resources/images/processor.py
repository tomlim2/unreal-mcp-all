"""
Image Resource Processor

Handles image processing for all APIs with copyright-safe approach.

Copyright Policy:
- User-uploaded images: IN-MEMORY ONLY (no storage, no UID)
- Generated images: PERSISTENT with UID assignment
"""

import base64
import logging
import re
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger("UnrealMCP.Resources.Images")


class ImageProcessor:
    """
    Central image resource processor.

    Responsibilities:
    - Decode/validate user-uploaded images
    - Load images from UID system
    - Enforce copyright policy (no storage for user uploads)
    """

    # Image constraints
    MAX_IMAGE_SIZE_MB = 10
    ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/jpg'}

    @classmethod
    def decode_base64_image(cls, data_str: str) -> Dict[str, Any]:
        """
        Decode base64 image data.

        Supports:
        - Data URI: data:image/png;base64,iVBORw0...
        - Raw base64: iVBORw0KGgoAAAANS...

        Returns:
            {'mime_type': str, 'data': bytes}

        Raises:
            ValueError: Invalid format or unsupported type
        """
        # Try Data URI format
        match = re.match(r"^data:(image/[\w]+);base64,(.*)", data_str)
        if match:
            mime_type, b64_data = match.groups()

            if mime_type not in cls.ALLOWED_MIME_TYPES:
                raise ValueError(
                    f"Unsupported image type: {mime_type}. "
                    f"Allowed: {cls.ALLOWED_MIME_TYPES}"
                )

            decoded_data = base64.b64decode(b64_data)
            return {"mime_type": mime_type, "data": decoded_data}

        # Fallback: raw base64 (assume PNG)
        decoded_data = base64.b64decode(data_str)
        return {"mime_type": "image/png", "data": decoded_data}

    @classmethod
    def validate_image_size(cls, image_data: bytes, max_size_mb: int = None) -> None:
        """
        Validate image size.

        Raises:
            ValueError: If image exceeds limit
        """
        max_size = max_size_mb or cls.MAX_IMAGE_SIZE_MB
        size_mb = len(image_data) / (1024 * 1024)

        if size_mb > max_size:
            raise ValueError(
                f"Image too large: {size_mb:.2f}MB (max: {max_size}MB)"
            )

    @classmethod
    def process_main_image(
        cls,
        main_image_request: Optional[Dict[str, Any]] = None,
        target_image_uid: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Process main/target image from request.

        Args:
            main_image_request: {'data': base64_str, 'mime_type': str}
            target_image_uid: Existing image UID (from screenshot)

        Returns:
            (uid, image_data)
            - Option A (UID): (str, None) - Load from UID system
            - Option B (Upload): (None, Dict) - User-uploaded (in-memory)
            - Option C (Neither): (None, None) - No image provided

        Copyright Policy:
            User-uploaded images are processed IN-MEMORY ONLY.
            NO storage, NO UID assignment for user originals.
        """
        # Priority 1: Use existing UID (screenshot)
        if target_image_uid:
            logger.info(f"Using existing image UID: {target_image_uid}")
            return (target_image_uid, None)

        # Priority 2: Process user upload
        if main_image_request:
            logger.info("Processing user-uploaded image (in-memory only, no UID)")

            try:
                image_data = cls.decode_base64_image(main_image_request['data'])
                cls.validate_image_size(image_data['data'])

                logger.debug(
                    f"Decoded user image: {image_data['mime_type']}, "
                    f"{len(image_data['data']) // 1024}KB"
                )

                return (None, image_data)

            except Exception as e:
                logger.error(f"Failed to process main image: {e}")
                raise ValueError(f"Main image validation failed: {e}")

        # No image provided
        return (None, None)

    @classmethod
    def process_reference_images(
        cls,
        reference_images_request: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process reference images from request.

        Args:
            reference_images_request: List of {'data': base64_str, ...}

        Returns:
            List of {'data': bytes, 'mime_type': str}

        Copyright Policy:
            Reference images are processed IN-MEMORY ONLY.
            NO storage, NO UID assignment.
        """
        if not reference_images_request:
            return []

        processed_refs = []

        for i, ref_img in enumerate(reference_images_request):
            try:
                image_data = cls.decode_base64_image(ref_img['data'])
                cls.validate_image_size(image_data['data'])
                processed_refs.append(image_data)

            except Exception as e:
                logger.error(f"Failed to process reference image {i}: {e}")
                raise ValueError(f"Reference image {i} validation failed: {e}")

        logger.info(
            f"Processed {len(processed_refs)} reference images "
            f"(in-memory only, no UID)"
        )
        return processed_refs

    @classmethod
    def load_image_from_uid(cls, uid: str) -> Dict[str, Any]:
        """
        Load image from UID system.

        Args:
            uid: Image UID (e.g., img_075)

        Returns:
            {'data': bytes, 'mime_type': str, 'file_path': str}

        Raises:
            ValueError: UID not found or file missing
        """
        # Import here to avoid circular imports
        import sys
        from pathlib import Path

        # Add Python directory to path if needed
        python_dir = Path(__file__).parent.parent.parent.parent
        if str(python_dir) not in sys.path:
            sys.path.insert(0, str(python_dir))

        from core.resources.uid_manager import get_uid_mapping

        mapping = get_uid_mapping(uid)
        if not mapping:
            raise ValueError(f"Image UID not found: {uid}")

        file_path = mapping.get('metadata', {}).get('file_path')
        if not file_path:
            raise ValueError(f"No file path in UID mapping: {uid}")

        file_path = Path(file_path)
        if not file_path.exists():
            raise ValueError(f"Image file not found: {file_path}")

        with open(file_path, 'rb') as f:
            image_bytes = f.read()

        logger.info(f"Loaded image from UID {uid}: {file_path.name}")

        return {
            'data': image_bytes,
            'mime_type': 'image/png',
            'file_path': str(file_path)
        }


# Convenience functions for easier imports
def process_main_image(main_image_request=None, target_image_uid=None):
    """Process main/target image (convenience wrapper)"""
    return ImageProcessor.process_main_image(main_image_request, target_image_uid)


def process_reference_images(reference_images_request=None):
    """Process reference images (convenience wrapper)"""
    return ImageProcessor.process_reference_images(reference_images_request)


def load_image_from_uid(uid):
    """Load image from UID (convenience wrapper)"""
    return ImageProcessor.load_image_from_uid(uid)
