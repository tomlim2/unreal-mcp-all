"""
Camera and viewport rendering command handler.

Handles Unreal Engine camera operations including viewport control, camera positioning,
and rendering view configuration for cinematic and capture purposes.
"""

import logging
from typing import Dict, Any, List
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand

logger = logging.getLogger("UnrealMCP")


class CameraCommandHandler(BaseCommandHandler):
    """Handler for camera and viewport rendering commands.
    
    Purpose: Camera positioning, viewport control, and rendering view management
    
    Supported Commands:
    - set_camera_position: Position camera at specific location and rotation
    - get_camera_transform: Retrieve current camera transform (location, rotation)
    - set_viewport_size: Configure viewport resolution for rendering
    - set_camera_fov: Adjust field of view for perspective rendering
    - focus_camera_on_actor: Point camera at specific actor with optional distance
    
    Input Constraints:
    - location: Optional Vector3 {"x": float, "y": float, "z": float} in centimeters
    - rotation: Optional Vector3 {"x": float, "y": float, "z": float} in degrees (pitch, yaw, roll)
    - fov: Optional float (10.0-170.0 degrees, defaults to 90.0)
    - width: Integer viewport width in pixels (128-7680)
    - height: Integer viewport height in pixels (128-4320)
    - actor_name: Required string for focus operations
    - distance: Optional float for focus distance in centimeters (defaults to 500.0)
    
    Coordinate System:
    - Units: Centimeters for distance, degrees for rotation
    - Axes: X=forward(red), Y=right(green), Z=up(blue)
    - Rotation: Pitch=X(up/down), Yaw=Z(left/right), Roll=Y(tilt)
    """
    
    def get_supported_commands(self) -> List[str]:
        return [
            "set_camera_position",
            "get_camera_transform",
            "set_viewport_size", 
            "set_camera_fov",
            "focus_camera_on_actor"
        ]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate camera commands with parameter checks."""
        errors = []
        
        if command_type == "set_camera_position":
            # Validate location if provided
            if "location" in params:
                location = params["location"]
                if not isinstance(location, dict):
                    errors.append("location must be an object with x, y, z properties")
                elif not all(k in location for k in ["x", "y", "z"]):
                    errors.append("location must have x, y, z properties")
                elif not all(isinstance(location[k], (int, float)) for k in ["x", "y", "z"]):
                    errors.append("location x, y, z must be numbers")
            
            # Validate rotation if provided
            if "rotation" in params:
                rotation = params["rotation"]
                if not isinstance(rotation, dict):
                    errors.append("rotation must be an object with x, y, z properties")
                elif not all(k in rotation for k in ["x", "y", "z"]):
                    errors.append("rotation must have x, y, z properties")
                elif not all(isinstance(rotation[k], (int, float)) for k in ["x", "y", "z"]):
                    errors.append("rotation x, y, z must be numbers")
        
        elif command_type == "set_viewport_size":
            if "width" not in params:
                errors.append("Missing required parameter: width")
            elif not isinstance(params["width"], int) or params["width"] < 128 or params["width"] > 7680:
                errors.append("width must be an integer between 128 and 7680")
            
            if "height" not in params:
                errors.append("Missing required parameter: height")
            elif not isinstance(params["height"], int) or params["height"] < 128 or params["height"] > 4320:
                errors.append("height must be an integer between 128 and 4320")
        
        elif command_type == "set_camera_fov":
            if "fov" not in params:
                errors.append("Missing required parameter: fov")
            elif not isinstance(params["fov"], (int, float)) or params["fov"] < 10.0 or params["fov"] > 170.0:
                errors.append("fov must be a number between 10.0 and 170.0 degrees")
        
        elif command_type == "focus_camera_on_actor":
            if "actor_name" not in params:
                errors.append("Missing required parameter: actor_name")
            elif not isinstance(params["actor_name"], str) or not params["actor_name"].strip():
                errors.append("actor_name must be a non-empty string")
            
            if "distance" in params:
                distance = params["distance"]
                if not isinstance(distance, (int, float)) or distance <= 0:
                    errors.append("distance must be a positive number")
        
        # get_camera_transform requires no parameters
        
        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values and normalize camera parameters."""
        processed = params.copy()
        
        # Apply defaults
        if command_type == "set_camera_fov":
            processed.setdefault("fov", 90.0)
        
        elif command_type == "focus_camera_on_actor":
            processed.setdefault("distance", 500.0)
        
        # Normalize vector values to floats
        if command_type == "set_camera_position":
            if "location" in processed:
                location = processed["location"]
                processed["location"] = {
                    "x": float(location["x"]),
                    "y": float(location["y"]),
                    "z": float(location["z"])
                }
            
            if "rotation" in processed:
                rotation = processed["rotation"]
                processed["rotation"] = {
                    "x": float(rotation["x"]),  # Pitch
                    "y": float(rotation["y"]),  # Roll
                    "z": float(rotation["z"])   # Yaw
                }
        
        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute camera commands."""
        logger.info(f"Camera Handler: Executing {command_type} with params: {params}")
        
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", "Unknown camera operation error"))
        
        return response