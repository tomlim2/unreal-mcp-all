"""
Screenshot command handler.

Handles Unreal Engine screenshot operations.
"""

import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
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
        """Execute screenshot commands synchronously."""
        logger.info(f"Screenshot Handler: Executing {command_type} with params: {params}")
        
        # Take screenshot via Unreal connection
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", f"Unknown Unreal {command_type} error"))
        
        # Wait a moment for file to be created
        time.sleep(0.5)
        
        # Find newest screenshot file
        screenshot_file = self._find_newest_screenshot()
        
        if screenshot_file:
            # Return success with direct file URL
            filename = screenshot_file.name
            return {
                "success": True,
                "message": f"Screenshot saved: {filename}",
                "image_url": f"/api/screenshot-file/{filename}"
            }
        else:
            # Return success but no file found (fallback)
            return {
                "success": True,
                "message": "Screenshot command executed (file not immediately available)",
                "image_url": None
            }

    def _find_newest_screenshot(self) -> Optional[Path]:
        """Find the newest screenshot file in the WindowsEditor directory."""
        try:
            project_path = os.getenv('UNREAL_PROJECT_PATH')
            if not project_path:
                logger.warning("UNREAL_PROJECT_PATH not set - cannot find screenshot files")
                return None
            
            # Look in WindowsEditor subdirectory where Unreal saves high-res screenshots
            screenshot_dir = Path(project_path) / "Saved" / "Screenshots" / "WindowsEditor"
            
            if not screenshot_dir.exists():
                logger.warning(f"Screenshot directory not found: {screenshot_dir}")
                return None
            
            # Find all PNG files
            png_files = list(screenshot_dir.glob("*.png"))
            
            if not png_files:
                logger.warning("No PNG files found in screenshot directory")
                return None
            
            # Return the newest file by modification time
            newest_file = max(png_files, key=lambda f: f.stat().st_mtime)
            logger.info(f"Found newest screenshot: {newest_file.name}")
            return newest_file
            
        except Exception as e:
            logger.error(f"Error finding newest screenshot: {e}")
            return None