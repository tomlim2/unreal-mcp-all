"""
Ultra Dynamic Sky command handler.

Handles time of day, color temperature, and sky property commands for Unreal Engine's
Ultra Dynamic Sky system. Supports both numeric and descriptive color temperature inputs.
"""

import logging
from typing import Dict, Any, List
from ..main import BaseCommandHandler
from ...nlp_schema_validator import (
    validate_command, 
    normalize_sky_parameters,
    ValidatedCommand
)
logger = logging.getLogger("UnrealMCP")


def map_temperature_description(description: str, current_temp: float = 6500.0) -> float:
    """Map descriptive color temperature strings to Kelvin values.
    
    Args:
        description: Temperature description ('warm', 'cool', 'warmer', etc.)
        current_temp: Current temperature for relative adjustments
        
    Returns:
        float: Temperature in Kelvin (1500-15000)
        
    Note: Lower Kelvin = warmer (more red/orange), Higher Kelvin = cooler (more blue/white)
    """
    desc_lower = description.lower().strip()
    
    if "very warm" in desc_lower or "extremely warm" in desc_lower:
        return 2700.0  # Very warm candle light
    elif "warm" in desc_lower and ("more" in desc_lower or "er" in desc_lower):
        return max(1500.0, current_temp - 1000.0)  # Make warmer
    elif "warm" in desc_lower:
        return 3200.0  # Standard warm white
    elif "very cold" in desc_lower or "extremely cold" in desc_lower:
        return 10000.0  # Very cold blue
    elif "cold" in desc_lower and ("more" in desc_lower or "er" in desc_lower):
        return min(15000.0, current_temp + 1000.0)  # Make cooler  
    elif "cooler" in desc_lower or "more cool" in desc_lower:
        return min(15000.0, current_temp + 1000.0)  # Make cooler by +1000K
    elif "cold" in desc_lower or "cool" in desc_lower:
        return 8000.0  # Standard cool white
    elif "daylight" in desc_lower or "neutral" in desc_lower:
        return 6500.0  # Standard daylight
    elif "sunset" in desc_lower or "golden" in desc_lower:
        return 2200.0  # Sunset/golden hour
    elif "noon" in desc_lower or "bright" in desc_lower:
        return 5600.0  # Noon daylight
    else:
        raise ValueError(f"Could not interpret color description: '{description}'. Try 'warm', 'cold', 'warmer', 'cooler', 'daylight', 'sunset', etc.")


class UDSCommandHandler(BaseCommandHandler):
    def get_supported_commands(self) -> List[str]:
        return ["get_ultra_dynamic_sky", "set_time_of_day", "set_color_temperature"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate UDS commands using existing schema validation."""
        command = {"type": command_type, "params": params}
        return validate_command(command)
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize sky parameters and handle color temperature descriptions.
        
        Preprocessing Rules:
        - Apply default sky_name if not provided
        - Mark string color temperatures for runtime conversion
        - Preserve numeric color temperatures as-is
        """
        processed_params = normalize_sky_parameters(params)
        
        # Handle color temperature string descriptions  
        if command_type == "set_color_temperature" and "color_temperature" in processed_params:
            color_temp = processed_params["color_temperature"]
            if isinstance(color_temp, str):
                # Mark for runtime conversion (requires current temperature lookup)
                processed_params["_color_temp_description"] = color_temp
                logger.info(f"UDS: Marked color temperature '{color_temp}' for runtime conversion")
        
        return processed_params
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute UDS commands with proper parameter handling."""
        logger.info(f"UDS Handler: Executing {command_type} with params: {params}")
        
        # Handle color temperature descriptions that need current value
        if command_type == "set_color_temperature" and "_color_temp_description" in params:
            description = params.pop("_color_temp_description")
            
            # Get current temperature for relative adjustments
            current_response = connection.send_command("get_ultra_dynamic_sky", {})
            current_temp = 6500.0
            if current_response and "result" in current_response and "color_temperature" in current_response["result"]:
                current_temp = float(current_response["result"]["color_temperature"])
            elif current_response and "color_temperature" in current_response:
                current_temp = float(current_response["color_temperature"])
            
            # Convert description to numeric value
            try:
                final_temp = map_temperature_description(description, current_temp)
                params["color_temperature"] = final_temp
                logger.info(f"Converted '{description}' to {final_temp}K (from current {current_temp}K)")
            except ValueError as e:
                raise Exception(str(e))
        
        # Send command to Unreal Engine
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", "Unknown Unreal error"))
        
        return response