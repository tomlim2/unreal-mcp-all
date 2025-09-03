"""
Ultra Dynamic Weather command handler.

Handles weather conditions, precipitation, and atmospheric effects for Unreal Engine's
Ultra Dynamic Weather system. Supports both descriptive and parametric weather controls.
"""

import logging
from typing import Dict, Any, List
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand

logger = logging.getLogger("UnrealMCP")




class UDWCommandHandler(BaseCommandHandler):
    """Handler for Ultra Dynamic Weather commands (weather state, rain control).
    
    Purpose: Control Ultra Dynamic Weather blueprint in Unreal Engine for atmospheric effects
    
    Supported Commands:
    - get_ultra_dynamic_weather: Retrieve current weather state (no parameters)
    - set_current_weather_to_rain: Set weather to rain condition (no parameters)
    
    Input Constraints:
    - Both commands require no parameters
    - Commands work with default UDW blueprint settings
    
    Weather System:
    - get_ultra_dynamic_weather: Returns current weather state, intensity, effects
    - set_current_weather_to_rain: Activates rain weather preset with default intensity
    """
    
    def get_supported_commands(self) -> List[str]:
        return ["get_ultra_dynamic_weather", "set_current_weather_to_rain"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate UDW commands (no parameters required)."""
        errors = []
        
        # Both UDW commands require no parameters
        if command_type in ["get_ultra_dynamic_weather", "set_current_weather_to_rain"]:
            # No parameter validation needed - commands work without parameters
            pass
        
        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """No preprocessing needed for UDW commands."""
        return params.copy()
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute UDW commands."""
        logger.info(f"UDW Handler: Executing {command_type} with params: {params}")
        
        # Send command to Unreal Engine (no parameter processing needed)
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", "Unknown Unreal weather error"))
        
        return response