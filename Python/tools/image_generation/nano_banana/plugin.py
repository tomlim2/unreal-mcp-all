"""
Nano Banana plugin for Creative Hub.

Wraps the existing NanoBananaImageEditHandler to integrate with the plugin system.
"""

import logging
from typing import Dict, Any, List
from core import BasePlugin, ToolCapability, ToolStatus, ToolMetadata, CommandResult
from .handlers.image_edit import NanoBananaImageEditHandler


logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """Nano Banana tool plugin for image generation and editing."""

    def __init__(self):
        super().__init__()
        self._handler = None

    def get_metadata(self) -> ToolMetadata:
        """Return Nano Banana tool metadata."""
        return ToolMetadata(
            tool_id="nano_banana",
            display_name="Nano Banana",
            version="1.0.0",
            capabilities=[
                ToolCapability.IMAGE_GENERATION,
                ToolCapability.IMAGE_EDITING,
                ToolCapability.IMAGE_STYLE_TRANSFER
            ],
            description="AI-powered image generation, editing, and style transfer using Nano Banana API",
            author="MegaMelange Team",
            requires_connection=True,
            icon="🍌",
            pricing_tier="premium"
        )

    def initialize(self) -> bool:
        """Initialize the Nano Banana handler."""
        try:
            self._handler = NanoBananaImageEditHandler()
            self.set_status(ToolStatus.AVAILABLE)
            logger.info("Nano Banana plugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Nano Banana plugin: {e}")
            self.set_status(ToolStatus.ERROR)
            return False

    def shutdown(self) -> bool:
        """Shutdown the plugin (no cleanup needed currently)."""
        self._handler = None
        self.set_status(ToolStatus.UNAVAILABLE)
        logger.info("Nano Banana plugin shutdown")
        return True

    def health_check(self) -> ToolStatus:
        """Check if Nano Banana API is accessible."""
        if self._handler is None:
            return ToolStatus.UNAVAILABLE

        # API health is determined by API key availability
        try:
            # The handler will check API key on first use
            return ToolStatus.AVAILABLE
        except Exception:
            return ToolStatus.ERROR

    def get_supported_commands(self) -> List[str]:
        """Return list of supported Nano Banana commands."""
        if self._handler:
            return self._handler.get_supported_commands()
        return [
            "text_to_image",
            "image_to_image",
            "edit_image",
            "style_transfer",
            "upscale_image",
            "remove_background"
        ]

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Nano Banana command parameters."""
        if not self._handler:
            return {'valid': False, 'errors': ['Handler not initialized']}

        try:
            validated = self._handler.validate_command(command_type, params)
            return {
                'valid': validated.is_valid,
                'errors': validated.errors
            }
        except Exception as e:
            logger.error(f"Validation error for {command_type}: {e}")
            return {'valid': False, 'errors': [str(e)]}

    def execute_command(self, command_type: str, params: Dict[str, Any]) -> CommandResult:
        """Execute Nano Banana command."""
        if not self._handler:
            return CommandResult(
                success=False,
                error="Plugin not initialized",
                error_code="PLUGIN_NOT_INITIALIZED"
            )

        try:
            # Execute command using the handler
            # Note: Handler expects a connection object for Unreal commands
            # For Nano Banana, we pass None as connection since it uses HTTP API
            result = self._handler.execute_command(None, command_type, params)

            # Convert handler result to CommandResult
            if isinstance(result, dict):
                success = result.get('success', True)
                return CommandResult(
                    success=success,
                    result=result if success else None,
                    error=result.get('error') if not success else None,
                    error_code=result.get('error_code'),
                    error_details=result.get('error_details'),
                    suggestion=result.get('suggestion'),
                    category=result.get('category')
                )
            else:
                # If result is not a dict, wrap it
                return CommandResult(success=True, result={'data': result})

        except Exception as e:
            logger.error(f"Error executing {command_type}: {e}")
            return CommandResult(
                success=False,
                error=str(e),
                error_code="EXECUTION_ERROR",
                category="nano_banana"
            )
