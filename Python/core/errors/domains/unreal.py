"""Unreal Engine-specific error codes and exceptions."""

from ..base import AppError, ErrorCategory
from typing import Optional


class UnrealErrorCodes:
    """Standardized error codes for Unreal Engine operations."""
    # Connection errors
    CONNECTION_FAILED = "UNREAL_CONNECTION_FAILED"
    CONNECTION_TIMEOUT = "UNREAL_CONNECTION_TIMEOUT"
    CONNECTION_REFUSED = "UNREAL_CONNECTION_REFUSED"

    # Command errors
    COMMAND_FAILED = "UNREAL_COMMAND_FAILED"
    COMMAND_TIMEOUT = "UNREAL_COMMAND_TIMEOUT"
    INVALID_COMMAND = "UNREAL_INVALID_COMMAND"

    # Actor errors
    ACTOR_NOT_FOUND = "UNREAL_ACTOR_NOT_FOUND"
    ACTOR_CREATION_FAILED = "UNREAL_ACTOR_CREATION_FAILED"
    ACTOR_DELETION_FAILED = "UNREAL_ACTOR_DELETION_FAILED"

    # Level errors
    LEVEL_NOT_LOADED = "UNREAL_LEVEL_NOT_LOADED"
    LEVEL_LOAD_FAILED = "UNREAL_LEVEL_LOAD_FAILED"

    # Asset errors
    ASSET_NOT_FOUND = "UNREAL_ASSET_NOT_FOUND"
    ASSET_LOAD_FAILED = "UNREAL_ASSET_LOAD_FAILED"
    ASSET_IMPORT_FAILED = "UNREAL_ASSET_IMPORT_FAILED"

    # Plugin errors
    PLUGIN_NOT_FOUND = "UNREAL_PLUGIN_NOT_FOUND"
    PLUGIN_DISABLED = "UNREAL_PLUGIN_DISABLED"

    # Blueprint errors
    BLUEPRINT_COMPILATION_FAILED = "UNREAL_BLUEPRINT_COMPILATION_FAILED"
    BLUEPRINT_NOT_FOUND = "UNREAL_BLUEPRINT_NOT_FOUND"

    # Rendering errors
    SCREENSHOT_FAILED = "UNREAL_SCREENSHOT_FAILED"
    RENDER_FAILED = "UNREAL_RENDER_FAILED"

    # Transform/Property errors
    INVALID_TRANSFORM = "UNREAL_INVALID_TRANSFORM"
    INVALID_PROPERTY = "UNREAL_INVALID_PROPERTY"
    PROPERTY_NOT_FOUND = "UNREAL_PROPERTY_NOT_FOUND"


class UnrealError(AppError):
    """Unreal Engine-specific error."""
    def __init__(self, code: str, message: str, **kwargs):
        super().__init__(
            code=code,
            message=message,
            category=kwargs.pop('category', ErrorCategory.EXTERNAL_API),
            **kwargs
        )


# Helper functions for common Unreal errors

def connection_failed(host: str = "localhost", port: int = 55557, request_id: Optional[str] = None) -> UnrealError:
    """Create connection failed error."""
    return UnrealError(
        code=UnrealErrorCodes.CONNECTION_FAILED,
        message=f"Failed to connect to Unreal Engine at {host}:{port}",
        category=ErrorCategory.EXTERNAL_API,
        details={"host": host, "port": port},
        suggestion="Ensure Unreal Engine is running with MCP plugin enabled",
        request_id=request_id
    )


def connection_timeout(timeout_seconds: int = 10, request_id: Optional[str] = None) -> UnrealError:
    """Create connection timeout error."""
    return UnrealError(
        code=UnrealErrorCodes.CONNECTION_TIMEOUT,
        message=f"Connection to Unreal Engine timed out after {timeout_seconds}s",
        category=ErrorCategory.EXTERNAL_API,
        details={"timeout_seconds": timeout_seconds},
        suggestion="Check Unreal Engine is responsive and not busy",
        retry_after=5,
        request_id=request_id
    )


def command_failed(command: str, reason: str, request_id: Optional[str] = None) -> UnrealError:
    """Create command execution failed error."""
    return UnrealError(
        code=UnrealErrorCodes.COMMAND_FAILED,
        message=f"Unreal command '{command}' failed: {reason}",
        category=ErrorCategory.EXTERNAL_API,
        details={"command": command, "reason": reason},
        suggestion="Check command parameters and Unreal Engine logs",
        request_id=request_id
    )


def actor_not_found(actor_name: str, request_id: Optional[str] = None) -> UnrealError:
    """Create actor not found error."""
    return UnrealError(
        code=UnrealErrorCodes.ACTOR_NOT_FOUND,
        message=f"Actor '{actor_name}' not found in level",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        details={"actor_name": actor_name},
        suggestion="Check actor name spelling or use get_actors_in_level to list actors",
        request_id=request_id
    )


def asset_not_found(asset_path: str, request_id: Optional[str] = None) -> UnrealError:
    """Create asset not found error."""
    return UnrealError(
        code=UnrealErrorCodes.ASSET_NOT_FOUND,
        message=f"Asset not found: {asset_path}",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        details={"asset_path": asset_path},
        suggestion="Check asset path spelling or content directory",
        request_id=request_id
    )


def screenshot_failed(reason: str, resolution: Optional[str] = None, request_id: Optional[str] = None) -> UnrealError:
    """Create screenshot failed error."""
    return UnrealError(
        code=UnrealErrorCodes.SCREENSHOT_FAILED,
        message=f"Screenshot failed: {reason}",
        category=ErrorCategory.EXTERNAL_API,
        details={"reason": reason, "resolution": resolution},
        suggestion="Check viewport is active and resolution is valid",
        request_id=request_id
    )


def plugin_not_found(plugin_name: str, request_id: Optional[str] = None) -> UnrealError:
    """Create plugin not found error."""
    return UnrealError(
        code=UnrealErrorCodes.PLUGIN_NOT_FOUND,
        message=f"Plugin '{plugin_name}' not found or disabled",
        category=ErrorCategory.PERMISSION,
        details={"plugin_name": plugin_name},
        suggestion=f"Enable {plugin_name} plugin in Unreal Engine settings",
        request_id=request_id
    )


def invalid_transform(reason: str, request_id: Optional[str] = None) -> UnrealError:
    """Create invalid transform error."""
    return UnrealError(
        code=UnrealErrorCodes.INVALID_TRANSFORM,
        message=f"Invalid transform: {reason}",
        category=ErrorCategory.USER_INPUT,
        details={"reason": reason},
        suggestion="Provide valid location (x,y,z), rotation, or scale values",
        request_id=request_id
    )


def command_timeout(command: str, timeout_seconds: int = 30, request_id: Optional[str] = None) -> UnrealError:
    """Create command timeout error."""
    return UnrealError(
        code=UnrealErrorCodes.COMMAND_TIMEOUT,
        message=f"Command '{command}' timed out after {timeout_seconds}s",
        category=ErrorCategory.EXTERNAL_API,
        details={"command": command, "timeout_seconds": timeout_seconds},
        suggestion="Complex operations may take longer. Try a simpler command or increase timeout",
        retry_after=10,
        request_id=request_id
    )
