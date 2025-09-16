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
from ...image_schema_utils import (
    build_screenshot_response,
    build_error_response,
    generate_request_id
)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL/Pillow not available - image metadata extraction disabled")

logger = logging.getLogger("UnrealMCP")


class ScreenshotCommandHandler(BaseCommandHandler):
    """Handler for screenshot commands.
    
    Supported Commands:
    - take_screenshot: Execute screenshot command
    
    Input Constraints:
    - resolution_multiplier: Optional float (1.0-8.0), defaults to 1.0
    - include_ui: Optional boolean, defaults to false
    
    Output:
    - Returns success confirmation with image UID and metadata
    """
    
    def __init__(self):
        super().__init__()
        self._uid_counter = 0
        self._uid_to_path_map = {}
    
    def get_supported_commands(self) -> List[str]:
        return ["take_screenshot"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate screenshot commands with parameter checks."""
        errors = []
        
        if command_type == "take_screenshot":
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
        
        if command_type == "take_screenshot":
            # Apply defaults
            processed.setdefault("resolution_multiplier", 1.0)
            processed.setdefault("include_ui", False)
            
            # Keep filename parameter if provided - let C++ handle it
        
        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute screenshot commands synchronously."""
        start_time = time.time()
        request_id = generate_request_id()
        
        logger.info(f"Screenshot Handler: Executing {command_type} with params: {params} [req_id: {request_id}]")
        
        try:
            # Take screenshot via Unreal connection
            response = connection.send_command(command_type, params)
            
            if response and response.get("status") == "error":
                return build_error_response(
                    response.get("error", f"Unknown Unreal {command_type} error"),
                    "unreal_command_error",
                    request_id,
                    start_time
                )
            
            # Wait a moment for file to be created
            time.sleep(0.5)
            
            # Find newest screenshot file
            screenshot_file = self._find_newest_screenshot()
            
            if screenshot_file:
                # Generate UID for screenshot
                image_uid = self._get_uid_for_path(str(screenshot_file))
                filename = screenshot_file.name
                
                # Extract image dimensions
                width, height = self._get_image_dimensions(str(screenshot_file))
                
                # Build standardized response
                return build_screenshot_response(
                    image_uid=image_uid,
                    filename=filename,
                    image_path=str(screenshot_file),
                    width=width,
                    height=height,
                    request_id=request_id,
                    start_time=start_time
                )
            else:
                return build_error_response(
                    "Screenshot command executed but file not found",
                    "file_not_found",
                    request_id,
                    start_time
                )
                
        except Exception as e:
            logger.error(f"Screenshot execution failed: {e}")
            return build_error_response(
                f"Screenshot execution failed: {str(e)}",
                "execution_error",
                request_id,
                start_time
            )

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
    
    def _generate_uid(self) -> str:
        """Generate sequential UID for images."""
        self._uid_counter += 1
        return f"img_{self._uid_counter:03d}"
    
    def _get_uid_for_path(self, file_path: str) -> str:
        """Get or create UID for a file path."""
        # Check if we already have a UID for this path
        for uid, path in self._uid_to_path_map.items():
            if path == file_path:
                return uid
        
        # Generate new UID
        uid = self._generate_uid()
        self._uid_to_path_map[uid] = file_path
        return uid
    
    def _get_image_dimensions(self, image_path: str) -> tuple[int, int]:
        """Get image dimensions using PIL if available."""
        try:
            if PIL_AVAILABLE:
                with Image.open(image_path) as img:
                    return img.width, img.height
        except Exception as e:
            logger.warning(f"Failed to get image dimensions from {image_path}: {e}")
        
        return 0, 0