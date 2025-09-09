"""
Session Management Package

Provides persistent session context for chat conversations with Unreal Engine.
Uses MegaMelange file-based storage with centralized path management.
"""

from .session_manager import SessionManager, get_session_manager
from .session_context import SessionContext, ChatMessage, SceneState
from .storage.storage_factory import StorageFactory
from .utils.path_manager import PathManager, PathConfig, get_path_manager

__all__ = [
    'SessionManager',
    'get_session_manager',
    'SessionContext', 
    'ChatMessage',
    'SceneState',
    'StorageFactory',
    'PathManager',
    'PathConfig',
    'get_path_manager'
]