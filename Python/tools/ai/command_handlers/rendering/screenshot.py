"""
Screenshot and high-resolution rendering command handler.

Handles Unreal Engine screenshot and rendering capture operations including
high-resolution shots, viewport captures, and rendering configuration.
"""

import logging
from typing import Dict, Any, List
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand

logger = logging.getLogger("UnrealMCP")


class ScreenshotCommandHandler(BaseCommandHandler):
    """Handler for screenshot and rendering capture commands.
    
    Purpose: High-resolution screenshot and viewport capture functionality
    
    Supported Commands:
    - take_highresshot: Capture high-resolution screenshot with configurable settings
    
    Input Constraints:
    - resolution_multiplier: Optional float (1.0-8.0), defaults to 2.0 for 2x resolution
    - filename: Optional string, auto-generated if not provided
    - format: Optional string ('png', 'jpg', 'exr'), defaults to 'png'
    - include_ui: Optional boolean, defaults to false
    - capture_hdr: Optional boolean, defaults to false for HDR capture
    
    Output:
    - Saves screenshot to project's Saved/Screenshots/ directory
    - Returns file path and capture settings in response
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
            
            if "format" in params:
                format_val = params["format"]
                if not isinstance(format_val, str):
                    errors.append("format must be a string")
                elif format_val.lower() not in ["png", "jpg", "jpeg", "exr"]:
                    errors.append("format must be 'png', 'jpg', 'jpeg', or 'exr'")
            
            if "filename" in params:
                filename = params["filename"]
                if not isinstance(filename, str):
                    errors.append("filename must be a string")
                elif not filename.strip():
                    errors.append("filename cannot be empty")
            
            if "include_ui" in params:
                if not isinstance(params["include_ui"], bool):
                    errors.append("include_ui must be a boolean")
            
            if "capture_hdr" in params:
                if not isinstance(params["capture_hdr"], bool):
                    errors.append("capture_hdr must be a boolean")
        
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
            processed.setdefault("resolution_multiplier", 2.0)
            processed.setdefault("format", "png")
            processed.setdefault("include_ui", False)
            processed.setdefault("capture_hdr", False)
            
            # Normalize format
            if "format" in processed:
                processed["format"] = processed["format"].lower()
                if processed["format"] == "jpeg":
                    processed["format"] = "jpg"
        
        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute screenshot commands."""
        logger.info(f"Screenshot Handler: Executing {command_type} with params: {params}")
        
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", "Unknown Unreal screenshot error"))
        
        return response