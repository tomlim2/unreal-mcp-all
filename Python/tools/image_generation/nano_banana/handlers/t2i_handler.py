"""Nano Banana Text-to-Image Handler (fal.ai style)."""

import logging
from typing import Dict, Any, List
from ._base import NanoBananaBaseHandler
from tools.ai.command_handlers.validation import ValidatedCommand

logger = logging.getLogger("UnrealMCP")


class NanaBananaTextToImageHandler(NanoBananaBaseHandler):
    """
    Nano Banana Text-to-Image generation handler.

    Schema (fal.ai style):
    - Command: "nano_banana_text_to_image"
    - images[0,1,2] = Reference images (optional, max 3)
    - prompt = Single unified prompt
    - config = {aspect_ratio, num_images, output_format}
    """

    def get_supported_commands(self) -> List[str]:
        return ["nano_banana_text_to_image"]

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate T2I-specific parameters."""
        errors = []

        if not self._ensure_gemini_initialized():
            from ._base import GEMINI_AVAILABLE
            if not GEMINI_AVAILABLE:
                errors.append("google.generativeai package not available")
            else:
                errors.append("Gemini API not properly configured (check GOOGLE_API_KEY)")

        # Prompt is required
        if not params.get("prompt"):
            errors.append("prompt is required")

        # Validate images array
        images = params.get("images", [])
        if not isinstance(images, list):
            errors.append("images must be an array")

        # T2I: images are optional reference images (max 3)
        if len(images) > 3:
            errors.append("Maximum 3 reference images allowed for nano_banana_text_to_image (images[0,1,2])")

        # Validate config.aspect_ratio if provided
        config = params.get("config", {})
        if "aspect_ratio" in config:
            valid_ratios = ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
            if config["aspect_ratio"] not in valid_ratios:
                errors.append(f"config.aspect_ratio must be one of {valid_ratios}")

        # Validate config.num_images if provided
        if "num_images" in config:
            num_images = config["num_images"]
            if not isinstance(num_images, int) or num_images < 1 or num_images > 4:
                errors.append("config.num_images must be an integer between 1 and 4")

        # Validate config.output_format if provided
        if "output_format" in config:
            valid_formats = ["png", "jpeg", "jpg"]
            if config["output_format"] not in valid_formats:
                errors.append(f"config.output_format must be one of {valid_formats}")

        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )

    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess T2I parameters with defaults."""
        processed = params.copy()

        # Ensure config exists
        if "config" not in processed:
            processed["config"] = {}

        config = processed["config"]

        # Set default config values
        config.setdefault("aspect_ratio", "16:9")
        config.setdefault("num_images", 1)
        config.setdefault("output_format", "png")

        # Ensure images array exists
        processed.setdefault("images", [])

        return processed

    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute T2I generation."""
        logger.info(f"Nano Banana T2I Handler: Executing {command_type}")
        logger.info(f"📝 Prompt: '{params.get('prompt', 'NO_PROMPT')}'")

        # Delegate to _text_to_image method from base class
        return self._text_to_image(params)
