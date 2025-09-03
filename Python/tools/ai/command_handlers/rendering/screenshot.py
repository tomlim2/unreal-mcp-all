"""
Screenshot command handler.

Handles Unreal Engine screenshot operations.
"""

import logging
from typing import Dict, Any, List
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand

logger = logging.getLogger("UnrealMCP")


class ScreenshotCommandHandler(BaseCommandHandler):
    """Handler for screenshot commands.
    
    Supported Commands:
    - take_highresshot: Execute screenshot command
    
    Input Constraints:
    - resolution_multiplier: Optional float (1.0-8.0), defaults to 1.0
    - include_ui: Optional boolean, defaults to false
    
    Output:
    - Returns success confirmation when command executes
    """
    
    def get_supported_commands(self) -> List[str]:
        return ["take_highresshot"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate screenshot commands with parameter checks."""
        errors = []
        
        if command_type == "take_highresshot":
            # Validate optional parameters
            if "resolution_multiplier" in params:
                multiplier = params["resolution_multiplier"]
                if not isinstance(multiplier, (int, float)):
                    errors.append("resolution_multiplier must be a number")
                elif multiplier < 1.0 or multiplier > 8.0:
                    errors.append("resolution_multiplier must be between 1.0 and 8.0")
            
            if "include_ui" in params:
                if not isinstance(params["include_ui"], bool):
                    errors.append("include_ui must be a boolean")
        
        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values and normalize parameters."""
        processed = params.copy()
        
        if command_type == "take_highresshot":
            # Apply defaults
            processed.setdefault("resolution_multiplier", 1.0)
            processed.setdefault("include_ui", False)
            
            # Remove filename parameter - let Unreal handle naming
            if "filename" in processed:
                del processed["filename"]
        
        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute screenshot commands."""
        logger.info(f"Screenshot Handler: Executing {command_type} with params: {params}")
        
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", f"Unknown Unreal {command_type} error"))
        
        return response