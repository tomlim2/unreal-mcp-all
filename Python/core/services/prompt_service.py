"""
Prompt processing service.

Handles prompt extraction and formatting from requests.
"""

from typing import Tuple, List, Optional
import logging

logger = logging.getLogger("http_bridge.services.prompt")


def extract_prompts(request_data: dict) -> Tuple[Optional[str], List[str]]:
    """
    Extract and format prompts from request.

    Args:
        request_data: HTTP request data

    Returns:
        Tuple of (main_prompt, reference_prompts)

    Auto-generation Logic:
        - If main_prompt is empty but reference_prompts exist:
          → Auto-generate: "Apply style transformation: {combined_prompts}"
    """
    main_prompt = request_data.get('main_prompt')
    reference_prompts = request_data.get('reference_prompts', [])

    logger.debug(f"Extracted prompts - main: '{main_prompt}', references: {reference_prompts}")

    # Auto-generate main_prompt if empty but references exist
    if _should_auto_generate_main_prompt(main_prompt, reference_prompts):
        original_main_prompt = main_prompt
        combined = ", ".join(reference_prompts)
        main_prompt = f"Apply style transformation: {combined}"

        logger.debug(
            f"Auto-generated main_prompt (original was empty/None). "
            f"Generated: '{main_prompt}'"
        )

    return main_prompt, reference_prompts


def _should_auto_generate_main_prompt(main_prompt: Optional[str], reference_prompts: List[str]) -> bool:
    """
    Determine if main_prompt should be auto-generated.

    Args:
        main_prompt: Main prompt string (may be None or empty)
        reference_prompts: List of reference prompts

    Returns:
        True if auto-generation should occur

    Conditions:
        1. main_prompt is None OR empty string OR whitespace-only
        2. reference_prompts is not empty
        3. At least one reference prompt has non-whitespace content
    """
    # Check if main_prompt is empty/None
    is_main_empty = not main_prompt or main_prompt.strip() == ''

    # Check if any reference prompt has content
    has_reference_content = reference_prompts and any(p.strip() for p in reference_prompts)

    return is_main_empty and has_reference_content
