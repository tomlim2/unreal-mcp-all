"""
Cesium geospatial command handler.

Handles geographic coordinate commands for Unreal Engine's Cesium Georeference system.
Supports setting and retrieving latitude/longitude coordinates for real-world positioning.
"""

import logging
from typing import Dict, Any, List
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand

logger = logging.getLogger("UnrealMCP")


class CesiumCommandHandler(BaseCommandHandler):
    """Handler for Cesium geospatial commands (latitude, longitude, properties).
    
    Purpose: Control Cesium Georeference actor for real-world geographic positioning
    
    Supported Commands:
    - set_cesium_latitude_longitude: Set geographic coordinates
    - get_cesium_properties: Retrieve current geographic position
    
    Input Constraints:
    - latitude: Float between -90 and 90 degrees (required)
    - longitude: Float between -180 and 180 degrees (required)
    
    Geographic References:
    - San Francisco: (37.7749, -122.4194)
    - New York City: (40.7128, -74.0060) 
    - Tokyo: (35.6804, 139.6917)
    
    Output Format:
    - Success: {"success": true, "latitude": float, "longitude": float, ...}
    - Error: {"status": "error", "error": "error message"}
    """
    
    def get_supported_commands(self) -> List[str]:
        return ["set_cesium_latitude_longitude", "get_cesium_properties"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate Cesium commands using basic validation."""
        errors = []
        
        if command_type == "set_cesium_latitude_longitude":
            if "latitude" not in params:
                errors.append("Missing required parameter: latitude")
            elif not isinstance(params["latitude"], (int, float)):
                errors.append("latitude must be a number")
            elif not (-90 <= params["latitude"] <= 90):
                errors.append("latitude must be between -90 and 90 degrees")
            
            if "longitude" not in params:
                errors.append("Missing required parameter: longitude")  
            elif not isinstance(params["longitude"], (int, float)):
                errors.append("longitude must be a number")
            elif not (-180 <= params["longitude"] <= 180):
                errors.append("longitude must be between -180 and 180 degrees")
        
        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute Cesium commands."""
        logger.info(f"Cesium Handler: Executing {command_type} with params: {params}")
        
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", "Unknown Unreal error"))
        
        return response