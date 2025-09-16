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
from ...pricing_manager import get_pricing_manager

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
            # Generate UID for screenshot
            image_uid = self._get_uid_for_path(str(screenshot_file))
            filename = screenshot_file.name
            
            # Extract image metadata
            resolution_multiplier = params.get("resolution_multiplier", 1.0)
            model = params.get("model", "gemini-2")
            metadata = self._extract_image_metadata(str(screenshot_file), resolution_multiplier, model)
            
            return {
                "success": True,
                "message": f"Screenshot saved: {filename}",
                "image_uid": image_uid,
                "image_url": f"/api/screenshot-file/{filename}",
                "image_metadata": {
                    "size": f"{metadata['width']}x{metadata['height']}",
                    "file_size": f"{metadata['file_size_mb']} MB",
                    "resolution_multiplier": resolution_multiplier,
                    "tokens": metadata['tokens'],
                    "estimated_cost": metadata['estimated_cost']
                }
            }
        else:
            # Return success but no file found (fallback)
            return {
                "success": True,
                "message": "Screenshot command executed (file not immediately available)",
                "image_uid": None,
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
    
    def _extract_image_metadata(self, image_path: str, resolution_multiplier: float = 1.0, model: str = "gemini-2") -> Dict[str, Any]:
        """Extract image metadata with accurate Google tile-based token calculation."""
        metadata = {
            "width": 0,
            "height": 0,
            "file_size_mb": 0.0,
            "tokens": 0,
            "estimated_cost": "$0.000",
            "resolution_multiplier": resolution_multiplier,
            "model": model
        }
        
        try:
            # Get file size
            file_path = Path(image_path)
            if file_path.exists():
                file_size_bytes = file_path.stat().st_size
                metadata["file_size_mb"] = round(file_size_bytes / (1024 * 1024), 1)
            
            # Extract image dimensions and calculate tokens using PIL if available
            if PIL_AVAILABLE:
                pricing_manager = get_pricing_manager()
                
                with Image.open(image_path) as img:
                    metadata["width"] = img.width
                    metadata["height"] = img.height
                    
                    # Use accurate Google tile-based calculation from pricing manager
                    tokens = pricing_manager.calculate_image_tokens(
                        img.width, img.height, resolution_multiplier
                    )
                    metadata["tokens"] = tokens
                    
                    # Calculate cost using pricing config
                    cost = pricing_manager.calculate_token_cost(tokens, model, "image_processing")
                    metadata["estimated_cost"] = f"${cost:.3f}"
            
        except Exception as e:
            logger.warning(f"Failed to extract image metadata from {image_path}: {e}")
        
        return metadata