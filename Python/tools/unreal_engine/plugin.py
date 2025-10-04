"""
Unreal Engine plugin for Creative Hub.

Wraps existing Unreal Engine command handlers (actor, light, UDS, Cesium, etc.)
to integrate with the plugin system.
"""

import logging
from typing import Dict, Any, List
from core import BasePlugin, ToolCapability, ToolStatus, ToolMetadata, CommandResult

# Import internal handlers (moved from command_handlers to plugin)
from .handlers.actor import ActorCommandHandler
from .handlers.light import LightCommandHandler
from .handlers.uds import UDSCommandHandler
from .handlers.cesium import CesiumCommandHandler
from .handlers.screenshot import ScreenshotCommandHandler


logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """Unreal Engine tool plugin for 3D scene management and rendering."""

    def __init__(self):
        super().__init__()
        self._handlers = []
        self._tcp_connection = None  # Will be set externally

    def get_metadata(self) -> ToolMetadata:
        """Return Unreal Engine tool metadata."""
        return ToolMetadata(
            tool_id="unreal_engine",
            display_name="Unreal Engine",
            version="5.5.4",
            capabilities=[
                ToolCapability.MESH_3D_CREATION,
                ToolCapability.MESH_3D_EDITING,
                ToolCapability.SCENE_MANAGEMENT,
                ToolCapability.RENDERING,
                ToolCapability.LIGHTING_CONTROL,
                ToolCapability.CAMERA_CONTROL,
                ToolCapability.ANIMATION,
                ToolCapability.GEOSPATIAL
            ],
            description="Real-time 3D creation tool for games, film, and virtual production",
            author="Epic Games / MegaMelange Integration",
            requires_connection=True,
            icon="🎮",
            pricing_tier="free"
        )

    def initialize(self) -> bool:
        """Initialize all Unreal Engine command handlers."""
        try:
            # Initialize all handlers
            self._handlers = [
                ActorCommandHandler(),
                LightCommandHandler(),
                UDSCommandHandler(),
                CesiumCommandHandler(),
                ScreenshotCommandHandler()
            ]

            self.set_status(ToolStatus.AVAILABLE)
            logger.info("Unreal Engine plugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Unreal Engine plugin: {e}")
            self.set_status(ToolStatus.ERROR)
            return False

    def shutdown(self) -> bool:
        """Shutdown the plugin and close TCP connection if active."""
        self._handlers = []
        self._tcp_connection = None
        self.set_status(ToolStatus.UNAVAILABLE)
        logger.info("Unreal Engine plugin shutdown")
        return True

    def health_check(self) -> ToolStatus:
        """Check if Unreal Engine is accessible via TCP connection."""
        if self._tcp_connection is None:
            return ToolStatus.UNAVAILABLE

        try:
            # Attempt to ping the connection (you may need to implement this)
            # For now, assume available if connection object exists
            return ToolStatus.AVAILABLE
        except Exception:
            return ToolStatus.ERROR

    def set_connection(self, connection):
        """
        Set the TCP connection for communicating with Unreal Engine.

        Args:
            connection: TCP connection object (from UnrealConnection)
        """
        self._tcp_connection = connection
        if connection:
            self.set_status(ToolStatus.AVAILABLE)
        else:
            self.set_status(ToolStatus.UNAVAILABLE)

    def get_supported_commands(self) -> List[str]:
        """Return list of all supported Unreal Engine commands."""
        all_commands = []
        for handler in self._handlers:
            all_commands.extend(handler.get_supported_commands())
        return all_commands

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Unreal Engine command parameters."""
        if not self._handlers:
            return {'valid': False, 'errors': ['Plugin not initialized']}

        # Find appropriate handler for this command
        handler = self._get_handler_for_command(command_type)
        if not handler:
            return {'valid': False, 'errors': [f'No handler found for command: {command_type}']}

        try:
            validated = handler.validate_command(command_type, params)
            return {
                'valid': validated.is_valid,
                'errors': validated.errors
            }
        except Exception as e:
            logger.error(f"Validation error for {command_type}: {e}")
            return {'valid': False, 'errors': [str(e)]}

    def execute_command(self, command_type: str, params: Dict[str, Any]) -> CommandResult:
        """Execute Unreal Engine command via TCP connection."""
        if not self._handlers:
            return CommandResult(
                success=False,
                error="Plugin not initialized",
                error_code="PLUGIN_NOT_INITIALIZED"
            )

        if not self._tcp_connection:
            return CommandResult(
                success=False,
                error="No TCP connection to Unreal Engine",
                error_code="NO_CONNECTION",
                suggestion="Ensure Unreal Engine project is open with UnrealMCP plugin enabled"
            )

        # Find appropriate handler
        handler = self._get_handler_for_command(command_type)
        if not handler:
            return CommandResult(
                success=False,
                error=f"No handler found for command: {command_type}",
                error_code="UNKNOWN_COMMAND"
            )

        try:
            # Execute command using handler
            result = handler.execute_command(self._tcp_connection, command_type, params)

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
                category="unreal_engine"
            )

    def _get_handler_for_command(self, command_type: str):
        """Find the appropriate handler for a given command type."""
        for handler in self._handlers:
            if command_type in handler.get_supported_commands():
                return handler
        return None
