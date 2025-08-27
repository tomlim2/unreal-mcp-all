"""
Session Management Package

Provides persistent session context for chat conversations with Unreal Engine.
Supports Supabase primary storage with local file fallback.
"""

from .session_manager import SessionManager, get_session_manager
from .session_context import SessionContext, ChatMessage, SceneState
from .storage.storage_factory import StorageFactory

__all__ = [
    'SessionManager',
    'get_session_manager',
    'SessionContext', 
    'ChatMessage',
    'SceneState',
    'StorageFactory'
]