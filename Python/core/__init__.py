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
    'reset_config'
]
