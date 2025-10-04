"""
Base plugin interface for Creative Hub tools.

This module defines the core plugin architecture that enables modular tool integration
for various creative applications (Unreal Engine, Nano Banana, Blender, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ToolCapability(Enum):
    """Enumeration of tool capabilities for routing commands."""
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    IMAGE_STYLE_TRANSFER = "image_style_transfer"
    VIDEO_GENERATION = "video_generation"
    VIDEO_EDITING = "video_editing"
    MESH_3D_CREATION = "mesh_3d_creation"
    MESH_3D_EDITING = "mesh_3d_editing"
    SCENE_MANAGEMENT = "scene_management"
    RENDERING = "rendering"
    LIGHTING_CONTROL = "lighting_control"
    CAMERA_CONTROL = "camera_control"
    ANIMATION = "animation"
    GEOSPATIAL = "geospatial"


class ToolStatus(Enum):
    """Tool availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ToolMetadata:
    """Metadata describing a creative tool."""
    tool_id: str  # Unique identifier (e.g., "nano_banana", "unreal_engine")
    display_name: str  # Human-readable name
    version: str  # Tool version
    capabilities: List[ToolCapability]  # What the tool can do
    description: str  # Brief description
    author: str  # Tool developer/maintainer
    requires_connection: bool  # Whether tool needs external connection (TCP, API, etc.)
    icon: Optional[str] = None  # Icon identifier for UI
    pricing_tier: Optional[str] = None  # Pricing category if applicable


@dataclass
class CommandResult:
    """Standardized command execution result."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    category: Optional[str] = None


class BasePlugin(ABC):
    """
    Base class for all Creative Hub tool plugins.

    Each tool (Unreal Engine, Nano Banana, Blender, etc.) implements this interface
    to enable standardized integration with the Creative Hub system.
    """

    def __init__(self):
        """Initialize the plugin."""
        self._metadata: Optional[ToolMetadata] = None
        self._status: ToolStatus = ToolStatus.UNAVAILABLE

    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """
        Return metadata describing this tool's capabilities.

        Returns:
            ToolMetadata object with tool information
        """
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the tool plugin (establish connections, load resources, etc.).

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        Gracefully shutdown the tool plugin (close connections, cleanup resources).

        Returns:
            True if shutdown successful, False otherwise
        """
        pass

    @abstractmethod
    def health_check(self) -> ToolStatus:
        """
        Check if the tool is currently available and operational.

        Returns:
            ToolStatus indicating current availability
        """
        pass

    @abstractmethod
    def get_supported_commands(self) -> List[str]:
        """
        Return list of command types this tool can handle.

        Returns:
            List of command type strings (e.g., ["create_actor", "take_screenshot"])
        """
        pass

    @abstractmethod
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate command parameters before execution.

        Args:
            command_type: Type of command to validate
            params: Command parameters

        Returns:
            Validation result dict with 'valid' (bool) and optional 'errors' (list)
        """
        pass

    @abstractmethod
    def execute_command(self, command_type: str, params: Dict[str, Any]) -> CommandResult:
        """
        Execute a command with the given parameters.

        Args:
            command_type: Type of command to execute
            params: Command parameters

        Returns:
            CommandResult with execution outcome
        """
        pass

    def get_status(self) -> ToolStatus:
        """
        Get current tool status.

        Returns:
            Current ToolStatus
        """
        return self._status

    def set_status(self, status: ToolStatus) -> None:
        """
        Update tool status.

        Args:
            status: New ToolStatus to set
        """
        self._status = status

    def has_capability(self, capability: ToolCapability) -> bool:
        """
        Check if this tool supports a specific capability.

        Args:
            capability: ToolCapability to check

        Returns:
            True if capability is supported, False otherwise
        """
        if not self._metadata:
            self._metadata = self.get_metadata()
        return capability in self._metadata.capabilities

    def get_command_schema(self, command_type: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON schema for a specific command's parameters (optional override).

        Args:
            command_type: Command type to get schema for

        Returns:
            JSON schema dict or None if not implemented
        """
        return None
