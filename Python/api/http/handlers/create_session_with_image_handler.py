"""
Handler for creating a new session with image generation.

This endpoint is designed for the /app first page where no session exists yet.
It performs an atomic operation: create session + generate image in one request.
"""

from typing import Dict, Any
import logging

from ..router import route
from ..middleware.trace_logger import log_request_start, log_error
from core.session import get_session_manager
from core.services import (
    process_images_from_request,
    prepare_reference_images_for_nlp,
    extract_prompts,
    build_error_response
)
from core.errors import AppError

logger = logging.getLogger("http_bridge.handlers.create_session_with_image")


@route("/api/create-session-with-image", method="POST", description="Create new session with image generation", tags=["Session", "Image"])
def handle_create_session_with_image(handler, request_data: dict, trace_id: str) -> Dict[str, Any]:
    """
    Create a new session and generate image in one atomic operation.

    Request:
        {
            "prompt": str (required),
            "main_prompt": str (optional),
            "text_prompt": str (optional),
            "aspect_ratio": str (optional, default: "16:9"),
            "model": str (optional, default: "gemini-2"),
            "session_name": str (optional),
            "mainImageData": {...} (optional),
            "referenceImageData": [...] (optional),
            "reference_prompts": [...] (optional)
        }

    Response:
        {
            "success": true,
            "session_id": "newly-created-id",
            "session_name": "Session Name",
            "image_uid": "img_XXX",
            "image_url": "/api/screenshot/...",
            "redirect_url": "/app/{session_id}",
            "nlp_result": {...}
        }
    """
    log_request_start(trace_id, "POST", "/api/create-session-with-image", "create_session_with_image")

    try:
        # Extract prompt
        prompt = request_data.get('prompt', '').strip()
        if not prompt:
            return {
                "success": False,
                "error": "prompt is required",
                "status_code": 400,
                "trace_id": trace_id
            }

        # Generate session name from first 6 words of prompt
        words = prompt.split()[:6]
        session_name = ' '.join(words)

        # Create new session (only session_id parameter)
        logger.info(f"[{trace_id}] Creating new session")
        session_manager = get_session_manager()
        new_session = session_manager.create_session()
        session_id = new_session.session_id

        # Update session name
        new_session.session_name = session_name
        session_manager.update_session(new_session)

        logger.info(f"[{trace_id}] Created new session: {session_id} (name: {session_name})")

        # Process images from request
        target_uid, main_image_data, reference_images = process_images_from_request(
            request_data, session_id
        )

        # Prepare reference images for NLP
        nlp_reference_images = prepare_reference_images_for_nlp(reference_images)

        # Extract prompts
        main_prompt, reference_prompts = extract_prompts(request_data)

        # Call NLP service to generate image
        logger.info(f"[{trace_id}] Processing NLP for image generation in session {session_id}")
        from tools.ai.nlp import process_natural_language

        user_input = prompt
        context = f"New session created. Generate image based on user request."
        llm_model = request_data.get('model', 'gemini-2')

        result = process_natural_language(
            user_input,
            context,
            session_id,
            llm_model,
            target_image_uid=target_uid,
            main_image_data=main_image_data,
            main_prompt=main_prompt,
            reference_prompts=reference_prompts,
            reference_images=nlp_reference_images
        )

        # Extract image UID from execution results
        image_uid = None
        image_url = None

        if result.get('executionResults'):
            for exec_result in result['executionResults']:
                if exec_result.get('success') and exec_result.get('result'):
                    result_data = exec_result['result']
                    uids = result_data.get('uids', {})
                    image_uid = uids.get('image')
                    if image_uid and result_data.get('image'):
                        image_url = result_data['image'].get('url')
                        break

        logger.info(f"[{trace_id}] Session created successfully: {session_id}, Image: {image_uid}")

        # Build response
        return {
            "success": True,
            "status_code": 200,
            "session_id": session_id,
            "session_name": session_name,
            "image_uid": image_uid,
            "image_url": image_url,
            "redirect_url": f"/app/{session_id}",
            "nlp_result": result,
            "trace_id": trace_id
        }

    except AppError as e:
        # Structured application error
        log_error(trace_id, e, "create session with image")
        error_response = build_error_response(e, request_data.get('prompt', ''), None, trace_id)
        return error_response

    except Exception as e:
        # Unexpected error
        log_error(trace_id, e, "create session with image")
        logger.exception(f"[{trace_id}] Unexpected error in create_session_with_image handler")
        return {
            "success": False,
            "error": str(e),
            "status_code": 500,
            "trace_id": trace_id
        }
