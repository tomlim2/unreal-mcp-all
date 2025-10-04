"""
Video Generation plugin for Creative Hub.

Wraps Google Veo-3 video generation handler to integrate with the plugin system.
"""

import logging
from typing import Dict, Any, List
from core import BasePlugin, ToolCapability, ToolStatus, ToolMetadata, CommandResult

# Import internal handler
from .veo.video_handler import VideoGenerationHandler


logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """Video Generation tool plugin using Google Veo-3."""

    def __init__(self):
        super().__init__()
        self._handler = None
        self._api_available = False

    def get_metadata(self) -> ToolMetadata:
        """Return Video Generation tool metadata."""
        return ToolMetadata(
            tool_id="video_generation",
            display_name="Video Generation (Veo-3)",
            version="1.0.0",
            capabilities=[
                ToolCapability.VIDEO_GENERATION,
                ToolCapability.VIDEO_EDITING
            ],
            description="AI-powered video generation using Google Veo-3",
            author="Google / MegaMelange Integration",
            requires_connection=False,  # API-based, not TCP
            icon="🎬",
            pricing_tier="premium"
        )

    def initialize(self) -> bool:
        """Initialize the video generation handler."""
        try:
            self._handler = VideoGenerationHandler()

            # Check if Google Generative AI is available
            try:
                import google.generativeai
                self._api_available = True
                self.set_status(ToolStatus.AVAILABLE)
                logger.info("Video Generation plugin initialized successfully")
            except ImportError:
                self._api_available = False
                self.set_status(ToolStatus.UNAVAILABLE)
                logger.warning("Google Generative AI SDK not available - Video Generation disabled")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize Video Generation plugin: {e}")
            self.set_status(ToolStatus.ERROR)
            return False

    def shutdown(self) -> bool:
        """Shutdown the plugin."""
        self._handler = None
        self._api_available = False
        self.set_status(ToolStatus.UNAVAILABLE)
        logger.info("Video Generation plugin shutdown")
        return True

    def health_check(self) -> ToolStatus:
        """Check if Google Generative AI API is accessible."""
        if not self._api_available:
            return ToolStatus.UNAVAILABLE

        try:
            # Could add API ping here if needed
            return ToolStatus.AVAILABLE
        except Exception:
            return ToolStatus.ERROR

    def get_supported_commands(self) -> List[str]:
        """Return list of supported video generation commands."""
        if not self._handler:
            return []
        return self._handler.get_supported_commands()

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate video generation command parameters."""
        if not self._handler:
            return {'valid': False, 'errors': ['Plugin not initialized']}

        if not self._api_available:
            return {'valid': False, 'errors': ['Google Generative AI SDK not available']}

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
        """Execute video generation command."""
        if not self._handler:
            return CommandResult(
                success=False,
                error="Plugin not initialized",
                error_code="PLUGIN_NOT_INITIALIZED"
            )

        if not self._api_available:
            return CommandResult(
                success=False,
                error="Google Generative AI SDK not available",
                error_code="API_UNAVAILABLE",
                suggestion="Install google-generativeai package"
            )

        try:
            # Note: Video generation doesn't need TCP connection
            # Handler works directly with Google API
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
                return CommandResult(success=True, result={'data': result})

        except Exception as e:
            logger.error(f"Error executing {command_type}: {e}")
            return CommandResult(
                success=False,
                error=str(e),
                error_code="EXECUTION_ERROR",
                category="video_generation"
            )
