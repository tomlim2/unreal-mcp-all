"""
MM Control Light command handler.

Handles CRUD operations for MegaMelange Control Lights (tagged point lights).
Supports creating, updating, deleting, and querying cinematic lighting controls.
"""

import logging
from typing import Dict, Any, List
from ..main import BaseCommandHandler
from ...nlp_schema_validator import (
    validate_command, 
    normalize_light_parameters,
    ValidatedCommand
)

logger = logging.getLogger("UnrealMCP")


class LightCommandHandler(BaseCommandHandler):
    """Handler for MM Control Light commands (CRUD operations).
    
    Purpose: Manage MegaMelange Control Lights (tagged point lights for cinematic control)
    
    Supported Commands:
    - create_mm_control_light: Create new tagged point light
    - get_mm_control_lights: List all MM control lights 
    - update_mm_control_light: Modify existing light properties
    - delete_mm_control_light: Remove light by name
    
    Input Constraints:
    - light_name: Required non-empty string for all operations
    - location: Optional {"x": float, "y": float, "z": float} (default: {0, 0, 100})
    - intensity: Optional non-negative float (default: 1000.0)
    - color: Optional {"r": int(0-255), "g": int(0-255), "b": int(0-255)} (default: white)
    
    Special Behavior:
    - create_mm_control_light applies default values via normalize_light_parameters()
    - All lights tagged with 'MM_Control_Light' for identification
    - Colors in RGB 0-255 format (converted to linear 0-1 internally by Unreal)
    """
    
    def get_supported_commands(self) -> List[str]:
        return ["create_mm_control_light", "get_mm_control_lights", "update_mm_control_light", "delete_mm_control_light"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate light commands using existing schema validation."""
        command = {"type": command_type, "params": params}
        return validate_command(command)
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize light parameters with defaults for create operations.
        
        Preprocessing Rules:
        - create_mm_control_light: Apply default location, intensity, color
        - update_mm_control_light: Preserve existing parameters, no defaults
        - Other commands: No preprocessing needed
        """
        if command_type == "create_mm_control_light":
            normalized = normalize_light_parameters(params)
            logger.info(f"Light: Applied defaults - location: {normalized.get('location')}, "
                       f"intensity: {normalized.get('intensity')}, color: {normalized.get('color')}")
            return normalized
        return params.copy()
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute light commands."""
        logger.info(f"Light Handler: Executing {command_type} with params: {params}")
        
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", "Unknown Unreal error"))
        
        return response