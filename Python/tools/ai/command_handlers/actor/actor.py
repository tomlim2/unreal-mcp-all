"""
Generic actor command handler.

Handles general-purpose Unreal Engine actor operations including creation, deletion,
transformation, and property queries for any actor type.
"""

import logging
from typing import Dict, Any, List
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand

logger = logging.getLogger("UnrealMCP")


class ActorCommandHandler(BaseCommandHandler):
    """Handler for generic actor commands (get, create, delete, transform, properties).
    
    Purpose: General-purpose Unreal Engine actor manipulation for any actor type
    
    Supported Commands:
    - get_actors_in_level: List all actors in current level (no parameters)
    - create_actor: Spawn new actor of specified type
    - delete_actor: Remove actor by name
    - set_actor_transform: Modify actor position/rotation/scale  
    - get_actor_properties: Retrieve actor property values
    
    Input Constraints:
    - name: Required non-empty string (actor identifier)
    - type: Required for create_actor (e.g., 'StaticMeshActor', 'PointLight')
    - location/rotation/scale: Optional Vector3 {"x": float, "y": float, "z": float}
    
    Coordinate System:
    - Units: Centimeters for distance, degrees for rotation
    - Axes: X=forward(red), Y=right(green), Z=up(blue)
    - Left-handed coordinate system
    """
    
    def get_supported_commands(self) -> List[str]:
        return ["get_actors_in_level", "create_actor", "delete_actor", "set_actor_transform", "get_actor_properties"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate actor commands with basic parameter checks."""
        errors = []
        
        if command_type == "create_actor":
            if "name" not in params:
                errors.append("Missing required parameter: name")
            elif not isinstance(params["name"], str) or not params["name"].strip():
                errors.append("name must be a non-empty string")
            
            if "type" not in params:
                errors.append("Missing required parameter: type")
            elif not isinstance(params["type"], str) or not params["type"].strip():
                errors.append("type must be a non-empty string")
        
        elif command_type in ["delete_actor", "set_actor_transform", "get_actor_properties"]:
            if "name" not in params:
                errors.append("Missing required parameter: name")
            elif not isinstance(params["name"], str) or not params["name"].strip():
                errors.append("name must be a non-empty string")
        
        # get_actors_in_level requires no parameters
        
        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute actor commands."""
        logger.info(f"Actor Handler: Executing {command_type} with params: {params}")
        
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", "Unknown Unreal error"))
        
        return response