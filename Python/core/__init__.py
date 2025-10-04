"""Core modules for MegaMelange backend."""

# Response utilities
from .response import (
    SuccessResponse,
    success_response,
    job_success,
    resource_success,
    conversion_success,
    error_response
)

# Plugin system
from .plugin_base import (
    BasePlugin,
    ToolCapability,
    ToolStatus,
    ToolMetadata,
    CommandResult
)

from .registry import (
    ToolRegistry,
    get_registry,
    reset_registry
)

# Configuration
from .config import (
    Config,
    FeatureFlags,
    get_config,
    reset_config
)

# Session Management
from .session import (
    SessionManager,
    get_session_manager,
    SessionContext,
    ChatMessage,
    SceneState,
    StorageFactory,
    PathManager,
    PathConfig,
    get_path_manager
)

__all__ = [
    'SuccessResponse',
    'success_response',
    'job_success',
    'resource_success',
    'conversion_success',
    'error_response',
    'BasePlugin',
    'ToolCapability',
    'ToolStatus',
    'ToolMetadata',
    'CommandResult',
    'ToolRegistry',
    'get_registry',
    'reset_registry',
    'Config',
    'FeatureFlags',
    'get_config',
    'reset_config',
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
