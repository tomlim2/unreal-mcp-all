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
from .video_generation.video_handler import VideoGenerationHandler
from .roblox.roblox_handler import RobloxCommandHandler
from .roblox.roblox_fbx_converter import RobloxFBXConverterHandler
from .roblox.roblox_pipeline import RobloxPipelineHandler
from .asset.import_object3d import Object3DImportHandler

__all__ = [
    'BaseCommandHandler',
    'CommandRegistry',
    'get_command_registry',
    'VideoGenerationHandler',
    'RobloxCommandHandler',
    'RobloxFBXConverterHandler',
    'RobloxPipelineHandler',
    'Object3DImportHandler'
]