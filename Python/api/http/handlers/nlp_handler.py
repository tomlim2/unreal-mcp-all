"""
NLP processing handler.

Handles natural language processing requests from frontend.
"""

from typing import Optional, Dict, Any
import logging

from ..router import route
from ..middleware.trace_logger import log_request_start, log_error
from core.services import (
    process_images_from_request,
    prepare_reference_images_for_nlp,
    extract_prompts,
    build_nlp_response,
    build_error_response
)
from core.errors import AppError

logger = logging.getLogger("http_bridge.handlers.nlp")


@route("/", method="POST", description="Process NLP request with optional image/prompt data", tags=["NLP"])
def handle_nlp_request(handler, request_data: dict, trace_id: str) -> Optional[Dict[str, Any]]:
    """
    Handle NLP processing endpoint.

    Args:
        handler: HTTP request handler instance
        request_data: Parsed request body
        trace_id: Request trace ID for logging

    Returns:
        Response dict, or None if not an NLP request

    Request Format:
        {
            "prompt": str (required),
            "session_id": str (optional),
            "llm_model": str (optional, default: "gemini-2"),
            "context": str (optional),
            "target_image_uid": str (optional),
            "mainImageData": {...} (optional),
            "referenceImageData": [...] (optional),
            "main_prompt": str (optional),
            "reference_prompts": [...] (optional)
        }

    Response Format:
        See build_nlp_response() in core.services.response_service
    """
    # Check if this is an NLP request
    user_input = request_data.get('prompt')
    if not user_input:
        return None  # Not our endpoint, let router try other handlers

    log_request_start(trace_id, "POST", "/", "nlp_processing")

    # Extract session context
    session_id = request_data.get('session_id')
    llm_model = request_data.get('llm_model')
    context = request_data.get('context', 'User is working with Unreal Engine project')

    try:
        # Process images using service layer
        target_uid, main_image_data, reference_images = process_images_from_request(
            request_data, session_id
        )

        # Prepare reference images for NLP (strict validation)
        nlp_reference_images = prepare_reference_images_for_nlp(reference_images)

        # Build images array for NLP (I2I: [main, refs...], T2I: [refs...])
        images = _build_images_array(target_uid, main_image_data, nlp_reference_images)

        # Log NLP call details
        _log_nlp_call_debug(images, trace_id)

        # Call NLP service with images array
        from tools.ai.nlp import process_natural_language

        result = process_natural_language(
            user_input, context, session_id, llm_model,
            images=images
        )

        # Verify images made it to commands (debug)
        if images and result.get('commands'):
            _verify_images_in_commands(result['commands'], images)

        # Build response
        response = build_nlp_response(result, user_input, session_id, trace_id)
        return response

    except ValueError as e:
        # Image validation error (400 Bad Request)
        log_error(trace_id, e, "image validation")
        error_response = build_error_response(e, user_input, session_id, trace_id)
        return error_response

    except AppError as e:
        # Structured application error
        log_error(trace_id, e, "NLP processing")
        error_response = build_error_response(e, user_input, session_id, trace_id)
        return error_response

    except Exception as e:
        # Unexpected error (500 Internal Server Error)
        log_error(trace_id, e, "NLP processing")
        logger.exception(f"[{trace_id}] Unexpected error in NLP handler")
        error_response = build_error_response(e, user_input, session_id, trace_id)
        return error_response


def _log_nlp_call_debug(images: Optional[list], trace_id: str):
    """
    Write NLP call details to debug log file.

    Args:
        images: Images array for NLP (I2I: [main, refs...], T2I: [refs...])
        trace_id: Request trace ID

    Writes to: http_bridge_debug.log
    """
    import datetime

    current_timestamp = datetime.datetime.now().isoformat()
    image_count = len(images) if images else 0

    with open('http_bridge_debug.log', 'a') as f:
        f.write(f"[{current_timestamp}] [{trace_id}] Calling NLP with {image_count} images\n")

        if images:
            for i, img in enumerate(images):
                data_len = len(img.get('data', ''))
                mime_type = img.get('mime_type')
                f.write(f"  Image [{i}]: {data_len} chars, type={mime_type}\n")


def _verify_images_in_commands(commands: list, images: list):
    """
    Verify images were injected into commands (debug logging).

    Args:
        commands: Generated commands from NLP
        images: Images array passed to NLP

    Logs warnings if images are missing from command params.
    """
    for i, command in enumerate(commands):
        cmd_params = command.get('params', {})
        if 'images' in cmd_params:
            img_count = len(cmd_params['images'])
            logger.debug(f"Command {i} has {img_count} images ✅")
        else:
            logger.warning(f"Command {i} missing images array ❌")


def _build_images_array(
    target_uid: Optional[str],
    main_image_data: Optional[Dict],
    reference_images: Optional[list]
) -> Optional[list]:
    """
    Build images array for NLP from processed image data.

    Logic:
        - I2I: images[0] = main (from target_uid or main_image_data)
               images[1,2,3] = references
        - T2I: images[0,1,2] = references (no main image)

    Args:
        target_uid: Optional screenshot UID
        main_image_data: Optional uploaded main image
        reference_images: Optional list of reference images

    Returns:
        List of image dicts: [{'data': base64, 'mime_type': str}, ...] or None
    """
    from core.resources.images import load_image_from_uid

    images = []

    # Check if we have main image (I2I mode)
    has_main_image = target_uid or main_image_data

    if target_uid:
        # Load from UID
        logger.debug(f"Loading main image from UID: {target_uid}")
        main_img = load_image_from_uid(target_uid)
        images.append(main_img)
    elif main_image_data:
        # Use uploaded main image
        logger.debug("Using uploaded main image")
        images.append(main_image_data)

    # Add reference images
    if reference_images:
        logger.debug(f"Adding {len(reference_images)} reference images")
        images.extend(reference_images)

    # Log final array structure
    if images:
        mode = "I2I" if has_main_image else "T2I"
        logger.info(f"Built {mode} images array with {len(images)} images")
        if has_main_image:
            logger.debug(f"  [0] = main image")
            for i in range(1, len(images)):
                logger.debug(f"  [{i}] = reference {i}")
        else:
            for i in range(len(images)):
                logger.debug(f"  [{i}] = reference {i+1}")

    return images if images else None
