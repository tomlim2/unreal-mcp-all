"""
Core infrastructure for modular command handlers.

Contains the base handler class and command registry for the Unreal MCP NLP system.
All specialized handlers extend BaseCommandHandler and register with CommandRegistry.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger("UnrealMCP")


class BaseCommandHandler(ABC):
    """Base class for all command handlers with common interface.
    
    Defines the contract that all command handlers must implement:
    - get_supported_commands(): List command types this handler manages
    - validate_command(): Schema-based parameter validation
    - execute_command(): Execute validated command via Unreal connection
    - preprocess_params(): Optional parameter normalization (override if needed)
    
    Input Format: {"type": str, "params": Dict[str, Any]}
    Output Format: Any (typically Dict from Unreal Engine response)
    
    Validation Flow:
    1. Check command_type is supported
    2. Validate required parameters exist and have correct types
    3. Check parameter value constraints (ranges, formats)
    4. Return ValidatedCommand with success/failure status
    
    Execution Flow:
    1. Preprocess parameters (apply defaults, normalize)
    2. Send TCP command to Unreal Engine
    3. Handle error responses
    4. Return raw response from Unreal Engine
    """
    
    @abstractmethod
    def get_supported_commands(self) -> List[str]:
        """Return list of command types this handler supports.
        
        Returns:
            List[str]: Command type strings (e.g., ['set_time_of_day', 'get_ultra_dynamic_sky'])
        """
        pass
    
    @abstractmethod
    def validate_command(self, command_type: str, params: Dict[str, Any]):
        """Validate command parameters using schema validation.
        
        Args:
            command_type (str): The command to validate (must be in get_supported_commands())
            params (Dict[str, Any]): Raw parameters from user input
            
        Returns:
            ValidatedCommand: Object containing:
                - type: str (command type)
                - params: Dict[str, Any] (validated/normalized parameters)
                - is_valid: bool (validation success)
                - validation_errors: List[str] (error messages if validation failed)
        """
        pass
    
    @abstractmethod
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute the validated command using the Unreal connection.
        
        Args:
            connection: Unreal TCP connection object with send_command() method
            command_type (str): Validated command type
            params (Dict[str, Any]): Preprocessed and validated parameters
            
        Returns:
            Any: Raw response from Unreal Engine (typically Dict with success/result/error)
            
        Raises:
            Exception: If TCP communication fails or Unreal returns error status
        """
        pass
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Override to add command-specific parameter preprocessing.
        
        Default implementation creates a shallow copy. Override in subclasses to:
        - Apply default values for optional parameters
        - Normalize parameter formats (e.g., string descriptions to numeric values)
        - Transform coordinate systems or units
        - Add computed parameters
        
        Args:
            command_type (str): The command being preprocessed
            params (Dict[str, Any]): Validated parameters
            
        Returns:
            Dict[str, Any]: Preprocessed parameters ready for execution
        """
        return params.copy()


class CommandRegistry:
    """Registry for managing command handlers with unified execution interface.
    
    Purpose: Central coordinator for all command handlers with validation pipeline
    
    Responsibilities:
    - Register and manage command handlers by command type
    - Route commands to appropriate handlers
    - Execute full validation pipeline: validate → preprocess → execute
    - Provide unified error handling and logging
    
    Execution Pipeline:
    1. Extract command_type and params from input
    2. Locate appropriate handler via command_type mapping
    3. Validate parameters using handler's validation rules
    4. Preprocess parameters (defaults, normalization)
    5. Execute via handler with Unreal TCP connection
    6. Return raw Unreal response or raise Exception on error
    
    Input Format: {"type": str, "params": Dict[str, Any]}
    Output Format: Any (raw response from Unreal Engine)
    
    Thread Safety: Not thread-safe (single global instance expected)
    """
    
    def __init__(self):
        self._handlers: Dict[str, BaseCommandHandler] = {}
        self._initialize_default_handlers()
    
    def _initialize_default_handlers(self):
        """Register default command handlers."""
        # Import handlers here to avoid circular imports
        from .actor.uds import UDSCommandHandler
        from .actor.udw import UDWCommandHandler
        from .actor.cesium import CesiumCommandHandler
        from .actor.light import LightCommandHandler
        from .actor.actor import ActorCommandHandler
        from .rendering.screenshot import ScreenshotCommandHandler
        from .nano_banana.image_edit import NanoBananaImageEditHandler
        
        handlers = [
            UDSCommandHandler(),
            UDWCommandHandler(),
            CesiumCommandHandler(), 
            LightCommandHandler(),
            ActorCommandHandler(),
            ScreenshotCommandHandler(),
            NanoBananaImageEditHandler()
        ]
        
        for handler in handlers:
            for command_type in handler.get_supported_commands():
                self._handlers[command_type] = handler
                logger.info(f"Registered handler for command: {command_type}")
    
    def register_handler(self, command_type: str, handler: BaseCommandHandler):
        """Register a custom handler for a command type."""
        self._handlers[command_type] = handler
        logger.info(f"Registered custom handler for command: {command_type}")
    
    def get_handler(self, command_type: str) -> Optional[BaseCommandHandler]:
        """Get handler for a specific command type."""
        return self._handlers.get(command_type)
    
    def get_supported_commands(self) -> List[str]:
        """Get list of all supported command types."""
        return list(self._handlers.keys())
    
    def execute_command(self, command: Dict[str, Any], connection) -> Any:
        """Execute command using appropriate handler with full validation pipeline.
        
        Args:
            command (Dict[str, Any]): Command object with 'type' and 'params' keys
            connection: Unreal TCP connection with send_command(type, params) method
            
        Returns:
            Any: Raw response from Unreal Engine (typically Dict)
            
        Raises:
            Exception: For validation failures, unknown commands, or Unreal errors
            
        Pipeline Steps:
        1. Extract and validate command structure
        2. Find handler for command_type
        3. Validate parameters via handler
        4. Preprocess parameters via handler
        5. Execute via handler with connection
        6. Return response or raise on error
        """
        # Extract command info
        command_type = command.get("type")
        if not command_type:
            raise Exception("Command must have a 'type' property")
        
        params = command.get("params", {})
        if not isinstance(params, dict):
            raise Exception("Command params must be an object")
        
        # Get handler
        handler = self.get_handler(command_type)
        if not handler:
            raise Exception(f"Unknown command type: {command_type}")
        
        logger.info(f"Registry: Processing {command_type} with handler: {handler.__class__.__name__}")
        
        # Validate command
        validated_cmd = handler.validate_command(command_type, params)
        if not validated_cmd.is_valid:
            raise Exception(f"Command validation failed: {'; '.join(validated_cmd.validation_errors)}")
        
        # Preprocess parameters
        processed_params = handler.preprocess_params(command_type, validated_cmd.params)
        
        # Execute command
        return handler.execute_command(connection, command_type, processed_params)


# Global registry instance - initialized once with default handlers
# Handlers registered: UDS, Cesium, Light, Actor (total ~14 commands)
_command_registry = CommandRegistry()


def get_command_registry() -> CommandRegistry:
    """Get the global command registry instance.
    
    Returns the singleton CommandRegistry with all default handlers registered.
    Handlers are registered once during module import.
    
    Returns:
        CommandRegistry: Global registry instance with UDS, Cesium, Light, and Actor handlers
    """
    return _command_registry