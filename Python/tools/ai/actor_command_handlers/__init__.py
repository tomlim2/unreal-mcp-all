"""
Modular command handlers for Unreal MCP NLP system.

Public API for the actor command handler system. Provides backward compatibility
with the previous monolithic handler structure while enabling modular organization.

Usage:
    from tools.ai.actor_command_handlers import get_command_registry
    
    registry = get_command_registry()
    response = registry.execute_command(command, connection)
"""

from .main import BaseCommandHandler, CommandRegistry, get_command_registry
from .uds import UDSCommandHandler
from .cesium import CesiumCommandHandler
from .light import LightCommandHandler
from .actor import ActorCommandHandler

__all__ = [
    'BaseCommandHandler',
    'CommandRegistry', 
    'get_command_registry',
    'UDSCommandHandler',
    'CesiumCommandHandler',
    'LightCommandHandler', 
    'ActorCommandHandler'
]