"""
Image processing service.

Handles image data extraction and processing from requests.
"""

from typing import Tuple, Optional, List, Dict, Any
import logging

logger = logging.getLogger("http_bridge.services.image")


def process_images_from_request(
    request_data: dict,
    session_id: str = None
) -> Tuple[Optional[str], Optional[Dict], Optional[List[Dict]]]:
    """
    Process all image data from request.

    Args:
        request_data: HTTP request data
        session_id: Optional session ID (unused, kept for compatibility)

    Returns:
        Tuple of (target_image_uid, main_image_data, reference_images)

    Image Sources:
        1. target_image_uid - Existing screenshot UID (explicit selection)
        2. mainImageData - User-uploaded image (in-memory, explicit upload)

    Note: No auto-fetching. If neither is provided, returns (None, None, reference_images)
    to enable true text-to-image generation mode.
    """
    from core.resources.images import process_main_image, process_reference_images

    # Process main/target image (supports both UID and user upload)
    target_uid, main_image_data = process_main_image(
        main_image_request=request_data.get('mainImageData'),
        target_image_uid=request_data.get('target_image_uid')
    )

    # Log selected image source
    if target_uid:
        logger.debug(f"Using target image UID: {target_uid}")
    elif main_image_data:
        logger.debug("Using user-uploaded main image (in-memory, no UID)")

    # Process reference images
    raw_reference_images = request_data.get('referenceImageData', [])
    reference_images = None

    if raw_reference_images:
        logger.debug(f"Processing {len(raw_reference_images)} reference images")
        reference_images = process_reference_images(raw_reference_images)
        logger.debug(f"Successfully processed {len(reference_images)} reference images")

        # Log reference image details
        for i, ref in enumerate(reference_images):
            size_kb = len(ref['data']) // 1024
            logger.debug(f"Ref {i}: {ref['mime_type']}, {size_kb}KB")

    return target_uid, main_image_data, reference_images


def prepare_reference_images_for_nlp(reference_images: Optional[List[Dict]]) -> Optional[List[Dict]]:
    """
    Convert reference images to NLP-compatible format with strict validation.

    Args:
        reference_images: Processed reference images from process_images_from_request()

    Returns:
        List of NLP-compatible reference images, or None

    Raises:
        ValueError: If image data is invalid

    Validation:
        - Each image must have 'data' field
        - Each image must have 'mime_type' field
    """
    if not reference_images:
        return None

    nlp_reference_images = []

    for i, ref in enumerate(reference_images):
        # Strict validation
        if not ref.get('data'):
            raise ValueError(f"Reference image {i}: Missing 'data' field")
        if not ref.get('mime_type'):
            raise ValueError(f"Reference image {i}: Missing 'mime_type' field")

        # Convert to NLP format (only data and mime_type)
        nlp_ref = {
            'data': ref['data'],
            'mime_type': ref['mime_type']
        }

        nlp_reference_images.append(nlp_ref)
        logger.debug(f"NLP ref {i}: mime_type={ref['mime_type']}, data_length={len(ref['data'])}")

    logger.debug(f"Successfully converted {len(nlp_reference_images)} reference images for NLP")
    return nlp_reference_images
