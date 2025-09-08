"""
Modular command handlers for Unreal MCP NLP system.

Public API for the command handler system. Provides modular organization
of commands by category (actor, rendering, etc.).

Usage:
    from tools.ai.command_handlers import get_command_registry
    
    registry = get_command_registry()
    response = registry.execute_command(command, connection)
"""

from .main import BaseCommandHandler, CommandRegistry, get_command_registry
from .actor.uds import UDSCommandHandler
from .actor.udw import UDWCommandHandler
from .actor.cesium import CesiumCommandHandler
from .actor.light import LightCommandHandler
from .actor.actor import ActorCommandHandler
from .rendering.screenshot import ScreenshotCommandHandler
from .nano_banana.image_edit import NanoBananaImageEditHandler

__all__ = [
    'BaseCommandHandler',
    'CommandRegistry', 
    'get_command_registry',
    'UDSCommandHandler',
    'UDWCommandHandler',
    'CesiumCommandHandler',
    'LightCommandHandler', 
    'ActorCommandHandler',
    'ScreenshotCommandHandler',
    'NanoBananaImageEditHandler'
]