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

        # Extract and format prompts
        main_prompt, reference_prompts = extract_prompts(request_data)

        # Log NLP call details
        _log_nlp_call_debug(nlp_reference_images, trace_id)

        # Call NLP service
        from tools.ai.nlp import process_natural_language

        result = process_natural_language(
            user_input, context, session_id, llm_model,
            target_image_uid=target_uid,
            main_image_data=main_image_data,
            main_prompt=main_prompt,
            reference_prompts=reference_prompts,
            reference_images=nlp_reference_images
        )

        # Verify reference images made it to commands (debug)
        if nlp_reference_images and result.get('commands'):
            _verify_reference_images_in_commands(result['commands'], nlp_reference_images)

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


def _log_nlp_call_debug(nlp_reference_images: Optional[list], trace_id: str):
    """
    Write NLP call details to debug log file.

    Args:
        nlp_reference_images: Prepared reference images for NLP
        trace_id: Request trace ID

    Writes to: http_bridge_debug.log
    """
    import datetime

    current_timestamp = datetime.datetime.now().isoformat()
    ref_count = len(nlp_reference_images) if nlp_reference_images else 0

    with open('http_bridge_debug.log', 'a') as f:
        f.write(f"[{current_timestamp}] [{trace_id}] Calling NLP with {ref_count} reference images\n")

        if nlp_reference_images:
            for i, ref in enumerate(nlp_reference_images):
                data_len = len(ref.get('data', ''))
                mime_type = ref.get('mime_type')
                f.write(f"  Ref {i}: {data_len} chars, type={mime_type}\n")


def _verify_reference_images_in_commands(commands: list, nlp_reference_images: list):
    """
    Verify reference images were injected into commands (debug logging).

    Args:
        commands: Generated commands from NLP
        nlp_reference_images: Reference images passed to NLP

    Logs warnings if reference images are missing from commands.
    """
    for i, command in enumerate(commands):
        cmd_params = command.get('params', {})
        if 'reference_images' in cmd_params:
            ref_count = len(cmd_params['reference_images'])
            logger.debug(f"Command {i} has {ref_count} reference images ✅")
        else:
            logger.warning(f"Command {i} missing reference_images ❌")
