"""
Tool Registry for Creative Hub plugin management.

This module provides automatic tool discovery, loading, and routing based on
tool capabilities and command requirements.
"""

import os
import json
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from ..plugin_base import BasePlugin, ToolCapability, ToolStatus, ToolMetadata, CommandResult


logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for managing Creative Hub tool plugins.

    Provides:
    - Auto-discovery of tools from filesystem
    - Lazy loading of tool plugins
    - Command routing to appropriate tools
    - Tool health monitoring
    """

    def __init__(self, tools_directory: Optional[str] = None):
        """
        Initialize the tool registry.

        Args:
            tools_directory: Path to tools directory (defaults to Python/tools/)
        """
        self._tools: Dict[str, BasePlugin] = {}  # tool_id -> plugin instance
        self._metadata: Dict[str, ToolMetadata] = {}  # tool_id -> metadata
        self._command_map: Dict[str, str] = {}  # command_type -> tool_id
        self._tools_directory = tools_directory or self._get_default_tools_dir()
        self._initialized = False

    def _get_default_tools_dir(self) -> str:
        """Get default tools directory path."""
        current_file = Path(__file__).resolve()
        # From core/registry/tool_registry.py -> Python/tools/
        return str(current_file.parent.parent.parent / "tools")

    def discover_tools(self) -> List[str]:
        """
        Discover available tools by scanning for metadata.json files.

        Returns:
            List of discovered tool IDs
        """
        discovered = []
        tools_path = Path(self._tools_directory)

        if not tools_path.exists():
            logger.warning(f"Tools directory not found: {self._tools_directory}")
            return discovered

        # Scan for tool directories with metadata.json
        for item in tools_path.iterdir():
            if item.is_dir():
                metadata_path = item / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata_dict = json.load(f)
                            tool_id = metadata_dict.get('tool_id')
                            if tool_id:
                                # Parse capabilities from strings to enum
                                capabilities = [
                                    ToolCapability(cap) for cap in metadata_dict.get('capabilities', [])
                                ]
                                metadata = ToolMetadata(
                                    tool_id=tool_id,
                                    display_name=metadata_dict.get('display_name', tool_id),
                                    version=metadata_dict.get('version', '0.0.0'),
                                    capabilities=capabilities,
                                    description=metadata_dict.get('description', ''),
                                    author=metadata_dict.get('author', 'Unknown'),
                                    requires_connection=metadata_dict.get('requires_connection', False),
                                    icon=metadata_dict.get('icon'),
                                    pricing_tier=metadata_dict.get('pricing_tier')
                                )
                                self._metadata[tool_id] = metadata
                                discovered.append(tool_id)
                                logger.info(f"Discovered tool: {tool_id} ({metadata.display_name})")
                    except Exception as e:
                        logger.error(f"Error loading metadata from {metadata_path}: {e}")

        return discovered

    def load_tool(self, tool_id: str) -> bool:
        """
        Lazy load a tool plugin by ID.

        Args:
            tool_id: Tool identifier (e.g., "nano_banana")

        Returns:
            True if loaded successfully, False otherwise
        """
        if tool_id in self._tools:
            return True  # Already loaded

        if tool_id not in self._metadata:
            logger.error(f"Tool {tool_id} not found in registry")
            return False

        try:
            # Import tool's plugin module
            # Expected: tools/{tool_id}/plugin.py with Plugin class
            module_path = f"tools.{tool_id}.plugin"
            module = importlib.import_module(module_path)

            if not hasattr(module, 'Plugin'):
                logger.error(f"Tool {tool_id} missing Plugin class in {module_path}")
                return False

            # Instantiate plugin
            plugin_class: Type[BasePlugin] = module.Plugin
            plugin = plugin_class()

            # Initialize plugin
            if not plugin.initialize():
                logger.error(f"Failed to initialize tool: {tool_id}")
                return False

            # Register plugin
            self._tools[tool_id] = plugin

            # Build command map
            for command in plugin.get_supported_commands():
                if command in self._command_map:
                    logger.warning(
                        f"Command '{command}' already mapped to {self._command_map[command]}, "
                        f"overriding with {tool_id}"
                    )
                self._command_map[command] = tool_id

            logger.info(f"Loaded tool: {tool_id}")
            return True

        except Exception as e:
            logger.error(f"Error loading tool {tool_id}: {e}")
            return False

    def initialize(self) -> bool:
        """
        Initialize the registry by discovering and optionally loading tools.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        discovered_tools = self.discover_tools()
        logger.info(f"Discovered {len(discovered_tools)} tools: {discovered_tools}")

        # Optionally auto-load all tools (or load on-demand)
        # For now, we'll load on-demand to save resources
        self._initialized = True
        return True

    def get_tool(self, tool_id: str) -> Optional[BasePlugin]:
        """
        Get a loaded tool plugin by ID (loads if not already loaded).

        Args:
            tool_id: Tool identifier

        Returns:
            BasePlugin instance or None if not available
        """
        if tool_id not in self._tools:
            if not self.load_tool(tool_id):
                return None
        return self._tools.get(tool_id)

    def get_tool_for_command(self, command_type: str) -> Optional[BasePlugin]:
        """
        Get the appropriate tool plugin for a command type.

        Args:
            command_type: Command type string

        Returns:
            BasePlugin instance or None if no tool supports this command
        """
        tool_id = self._command_map.get(command_type)
        if not tool_id:
            logger.warning(f"No tool registered for command: {command_type}")
            return None
        return self.get_tool(tool_id)

    def get_tools_by_capability(self, capability: ToolCapability) -> List[str]:
        """
        Find all tools that support a specific capability.

        Args:
            capability: ToolCapability to search for

        Returns:
            List of tool IDs supporting this capability
        """
        matching = []
        for tool_id, metadata in self._metadata.items():
            if capability in metadata.capabilities:
                matching.append(tool_id)
        return matching

    def execute_command(self, command_type: str, params: Dict[str, Any]) -> CommandResult:
        """
        Route and execute a command using the appropriate tool.

        Args:
            command_type: Command type to execute
            params: Command parameters

        Returns:
            CommandResult from tool execution
        """
        tool = self.get_tool_for_command(command_type)
        if not tool:
            return CommandResult(
                success=False,
                error=f"No tool available for command: {command_type}",
                error_code="TOOL_NOT_FOUND"
            )

        # Validate command
        validation = tool.validate_command(command_type, params)
        if not validation.get('valid', False):
            return CommandResult(
                success=False,
                error="Command validation failed",
                error_code="VALIDATION_ERROR",
                error_details={'errors': validation.get('errors', [])}
            )

        # Execute command
        try:
            return tool.execute_command(command_type, params)
        except Exception as e:
            logger.error(f"Error executing {command_type}: {e}")
            return CommandResult(
                success=False,
                error=str(e),
                error_code="EXECUTION_ERROR"
            )

    def get_all_metadata(self) -> Dict[str, ToolMetadata]:
        """
        Get metadata for all discovered tools.

        Returns:
            Dict mapping tool_id to ToolMetadata
        """
        return self._metadata.copy()

    def get_health_status(self) -> Dict[str, ToolStatus]:
        """
        Get health status for all loaded tools.

        Returns:
            Dict mapping tool_id to ToolStatus
        """
        status = {}
        for tool_id, plugin in self._tools.items():
            status[tool_id] = plugin.health_check()
        return status

    def shutdown_all(self) -> None:
        """Shutdown all loaded tools gracefully."""
        for tool_id, plugin in self._tools.items():
            try:
                plugin.shutdown()
                logger.info(f"Shutdown tool: {tool_id}")
            except Exception as e:
                logger.error(f"Error shutting down {tool_id}: {e}")
        self._tools.clear()
        self._command_map.clear()


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """
    Get the global tool registry instance (singleton pattern).

    Returns:
        ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.initialize()
    return _registry


def reset_registry() -> None:
    """Reset the global registry (primarily for testing)."""
    global _registry
    if _registry:
        _registry.shutdown_all()
    _registry = None
