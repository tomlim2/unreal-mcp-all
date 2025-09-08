"""
Nano Banana image editing handler.

Handles Google Gemini Nano Banana image editing operations.
"""

import logging
import os
import base64
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand

logger = logging.getLogger("UnrealMCP")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google.generativeai not available - Nano Banana features disabled")


class NanoBananaImageEditHandler(BaseCommandHandler):
    """Handler for Nano Banana image editing commands.
    
    Supported Commands:
    - transform_image_style: Apply style to existing screenshot
    - take_styled_screenshot: Take screenshot and apply style transformation
    
    Input Constraints:
    - style_prompt: Required string describing the desired style
    - image_path: Required string for transform_image_style
    - intensity: Optional float (0.1-1.0), defaults to 0.8
    - resolution_multiplier: Optional float for screenshots (1.0-8.0), defaults to 1.0
    
    Output:
    - Returns styled image path and transformation details
    """
    
    def __init__(self):
        super().__init__()
        self._model = None
        self._model_initialized = False
    
    def _ensure_gemini_initialized(self):
        """Initialize Gemini API lazily when needed."""
        if self._model_initialized:
            return self._model is not None
            
        self._model_initialized = True
        
        if not GEMINI_AVAILABLE:
            logger.warning("google.generativeai package not available")
            self._model = None
            return False
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set - Nano Banana features will not work")
            self._model = None
            return False
        
        try:
            genai.configure(api_key=api_key)
            # Use Gemini's official image generation model
            self._model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
            logger.info("Nano Banana (Gemini) initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self._model = None
            return False
    
    def get_supported_commands(self) -> List[str]:
        return ["transform_image_style", "take_styled_screenshot"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate Nano Banana commands with parameter checks."""
        errors = []
        
        # Check if Gemini is available (lazy initialization)
        if not self._ensure_gemini_initialized():
            if not GEMINI_AVAILABLE:
                errors.append("google.generativeai package not available")
            else:
                errors.append("Gemini API not properly configured (check GOOGLE_API_KEY)")
        
        if command_type == "transform_image_style":
            # Required parameters
            if not params.get("style_prompt"):
                errors.append("style_prompt is required")
            if not params.get("image_path"):
                errors.append("image_path is required")
            
            # Validate optional parameters
            if "intensity" in params:
                intensity = params["intensity"]
                if not isinstance(intensity, (int, float)):
                    errors.append("intensity must be a number")
                elif intensity < 0.1 or intensity > 1.0:
                    errors.append("intensity must be between 0.1 and 1.0")
        
        elif command_type == "take_styled_screenshot":
            # Required parameters
            if not params.get("style_prompt"):
                errors.append("style_prompt is required")
            
            # Validate screenshot parameters
            if "resolution_multiplier" in params:
                multiplier = params["resolution_multiplier"]
                if not isinstance(multiplier, (int, float)):
                    errors.append("resolution_multiplier must be a number")
                elif multiplier < 1.0 or multiplier > 8.0:
                    errors.append("resolution_multiplier must be between 1.0 and 8.0")
            
            if "intensity" in params:
                intensity = params["intensity"]
                if not isinstance(intensity, (int, float)):
                    errors.append("intensity must be a number")
                elif intensity < 0.1 or intensity > 1.0:
                    errors.append("intensity must be between 0.1 and 1.0")
        
        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values and normalize parameters."""
        processed = params.copy()
        
        # Apply common defaults
        processed.setdefault("intensity", 0.8)
        
        if command_type == "take_styled_screenshot":
            processed.setdefault("resolution_multiplier", 1.0)
            processed.setdefault("include_ui", False)
        
        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute Nano Banana commands."""
        logger.info(f"Nano Banana Handler: Executing {command_type} with params: {params}")
        
        if command_type == "transform_image_style":
            return self._transform_existing_image(params)
        elif command_type == "take_styled_screenshot":
            return self._take_and_transform_screenshot(connection, params)
        else:
            raise Exception(f"Unsupported command: {command_type}")
    
    def _transform_existing_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform an existing image with style."""
        image_path_param = params["image_path"]
        style_prompt = params["style_prompt"]
        intensity = params["intensity"]
        
        # Resolve the image path (could be filename or full path)
        resolved_image_path = self._resolve_image_path(image_path_param)
        if not resolved_image_path:
            raise Exception(f"Image file not found: {image_path_param}")
        
        # Apply style transformation
        styled_image_path = self._apply_nano_banana_style(
            resolved_image_path, style_prompt, intensity
        )
        
        if styled_image_path:
            filename = Path(styled_image_path).name
            return {
                "success": True,
                "message": f"Image styled successfully: {filename}",
                "original_image": resolved_image_path,
                "styled_image_path": styled_image_path,
                "style_prompt": style_prompt,
                "intensity": intensity,
                "image_url": f"/api/screenshot-file/{filename}"
            }
        else:
            raise Exception("Failed to apply style transformation")
    
    def _take_and_transform_screenshot(self, connection, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot and apply style transformation."""
        style_prompt = params["style_prompt"]
        intensity = params["intensity"]
        
        # Prepare screenshot parameters
        screenshot_params = {
            "resolution_multiplier": params["resolution_multiplier"],
            "include_ui": params["include_ui"]
        }
        
        # Take screenshot via Unreal connection
        logger.info("Taking screenshot before styling...")
        response = connection.send_command("take_highresshot", screenshot_params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", "Unknown screenshot error"))
        
        # Wait for screenshot to be saved
        time.sleep(1.0)
        
        # Find newest screenshot
        screenshot_path = self._find_newest_screenshot()
        if not screenshot_path:
            raise Exception("Screenshot was taken but file not found")
        
        logger.info(f"Screenshot taken: {screenshot_path}")
        
        # Apply style transformation
        styled_image_path = self._apply_nano_banana_style(
            str(screenshot_path), style_prompt, intensity
        )
        
        if styled_image_path:
            filename = Path(styled_image_path).name
            return {
                "success": True,
                "message": f"Screenshot taken and styled: {filename}",
                "original_screenshot": str(screenshot_path),
                "styled_image_path": styled_image_path,
                "style_prompt": style_prompt,
                "intensity": intensity,
                "image_url": f"/api/screenshot-file/{filename}"
            }
        else:
            raise Exception("Screenshot taken but style transformation failed")
    
    def _apply_nano_banana_style(self, image_path: str, style_prompt: str, intensity: float) -> Optional[str]:
        """Apply Gemini image generation style transformation to image."""
        if not self._ensure_gemini_initialized():
            raise Exception("Gemini image generation not available")
        
        try:
            logger.info(f"Applying Gemini image transformation: {style_prompt} (intensity: {intensity})")
            
            # Read the original image
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()
                image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Build the transformation prompt
            transformation_prompt = self._build_gemini_image_prompt(style_prompt, intensity)
            
            # Prepare image part for Gemini
            image_part = {
                'inline_data': {
                    'mime_type': 'image/png',
                    'data': image_b64
                }
            }
            
            # Generate styled image using Gemini
            logger.info("Sending image transformation request to Gemini...")
            response = self._model.generate_content([image_part, transformation_prompt])
            
            if not response or not response.candidates:
                raise Exception("No response from Gemini image generation")
            
            # Save the generated image
            styled_image_path = self._save_gemini_generated_image(
                response, image_path, style_prompt
            )
            
            return styled_image_path
            
        except Exception as e:
            logger.error(f"Gemini image transformation failed: {e}")
            raise Exception(f"Style transformation failed: {str(e)}")
    
    def _build_gemini_image_prompt(self, style_prompt: str, intensity: float) -> str:
        """Build the image generation prompt for Gemini."""
        intensity_description = "subtle" if intensity < 0.4 else "moderate" if intensity < 0.7 else "strong"
        
        return f"""Transform this image to have {style_prompt} style. 
Apply a {intensity_description} transformation that maintains the original composition and key elements 
while changing the visual style, colors, textures, and aesthetic to match {style_prompt}. 
Keep the image recognizable but with clear stylistic changes. Generate the transformed image."""
    
    def _create_placeholder_styled_image(self, original_path: str, style_prompt: str, intensity: float) -> str:
        """Create a placeholder styled image by copying the original."""
        try:
            # Create styled directory
            project_path = os.getenv('UNREAL_PROJECT_PATH')
            if not project_path:
                raise Exception("UNREAL_PROJECT_PATH not set")
            
            styled_dir = Path(project_path) / "Saved" / "Screenshots" / "styled"
            styled_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            original_name = Path(original_path).stem
            style_safe = "".join(c for c in style_prompt[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
            style_safe = style_safe.replace(' ', '_')
            timestamp = int(time.time())
            
            styled_filename = f"{original_name}_{style_safe}_{timestamp}.png"
            styled_path = styled_dir / styled_filename
            
            # For now, just copy the original image as a placeholder
            # In real implementation, this would be the transformed image
            import shutil
            shutil.copy2(original_path, styled_path)
            
            logger.info(f"Placeholder styled image created: {styled_path}")
            logger.info(f"Note: This is a copy of the original. Real implementation would apply {style_prompt} transformation")
            
            return str(styled_path)
            
        except Exception as e:
            logger.error(f"Failed to create placeholder styled image: {e}")
            raise Exception(f"Failed to create styled image: {str(e)}")

    def _save_gemini_generated_image(self, response, original_path: str, style_prompt: str) -> str:
        """Save the Gemini generated image to the styled screenshots directory."""
        try:
            # Create styled directory
            project_path = os.getenv('UNREAL_PROJECT_PATH')
            if not project_path:
                raise Exception("UNREAL_PROJECT_PATH not set")
            
            styled_dir = Path(project_path) / "Saved" / "Screenshots" / "styled"
            styled_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            original_name = Path(original_path).stem
            style_safe = "".join(c for c in style_prompt[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
            style_safe = style_safe.replace(' ', '_')
            timestamp = int(time.time())
            
            styled_filename = f"{original_name}_{style_safe}_{timestamp}.png"
            styled_path = styled_dir / styled_filename
            
            # Extract image data from Gemini response
            logger.info(f"Processing Gemini response with {len(response.candidates)} candidates")
            
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        logger.info(f"Processing part: {type(part)}, hasattr inline_data: {hasattr(part, 'inline_data')}")
                        
                        if hasattr(part, 'inline_data') and part.inline_data:
                            mime_type = part.inline_data.mime_type
                            logger.info(f"Found inline_data with mime_type: {mime_type}")
                            
                            if mime_type and mime_type.startswith('image/'):
                                # Gemini returns image data as bytes, not base64
                                raw_data = part.inline_data.data
                                if isinstance(raw_data, bytes):
                                    image_data = raw_data
                                    logger.info(f"Using raw bytes: {len(image_data)} bytes of image data")
                                else:
                                    # Fallback to base64 decode if needed
                                    image_data = base64.b64decode(raw_data)
                                    logger.info(f"Base64 decoded: {len(image_data)} bytes of image data")
                                
                                with open(styled_path, 'wb') as f:
                                    f.write(image_data)
                                
                                logger.info(f"Gemini generated image saved: {styled_path}")
                                return str(styled_path)
            
            # If no image data found, log detailed response structure for debugging
            logger.error("No image data found in Gemini response")
            logger.error(f"Response structure: candidates={len(response.candidates) if response.candidates else 0}")
            
            if response.candidates:
                candidate = response.candidates[0]
                logger.error(f"First candidate has content: {hasattr(candidate, 'content')}")
                if hasattr(candidate, 'content') and candidate.content:
                    logger.error(f"Content has parts: {hasattr(candidate.content, 'parts')}")
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        logger.error(f"Number of parts: {len(candidate.content.parts)}")
                        for i, part in enumerate(candidate.content.parts):
                            logger.error(f"Part {i}: type={type(part)}, has_inline_data={hasattr(part, 'inline_data')}")
            
            raise Exception("No image data found in Gemini response")
            
        except Exception as e:
            logger.error(f"Failed to save Gemini generated image: {e}")
            raise Exception(f"Failed to save generated image: {str(e)}")
    
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
    
    def _resolve_image_path(self, image_path_param: str) -> Optional[str]:
        """Resolve image path - handles both full paths and filenames from session context."""
        # If it's already a full path and exists, use it
        if os.path.isabs(image_path_param) and os.path.exists(image_path_param):
            return image_path_param
        
        # Otherwise, treat it as a filename and search for it
        project_path = os.getenv('UNREAL_PROJECT_PATH')
        if not project_path:
            logger.warning("UNREAL_PROJECT_PATH not set - cannot resolve image path")
            return None
        
        # Search locations in order of preference
        search_locations = [
            # Styled images directory (most recent transformations)
            Path(project_path) / "Saved" / "Screenshots" / "styled",
            # Original screenshots directory
            Path(project_path) / "Saved" / "Screenshots" / "WindowsEditor",
        ]
        
        filename = Path(image_path_param).name  # Extract just the filename
        
        for location in search_locations:
            if location.exists():
                potential_path = location / filename
                if potential_path.exists():
                    logger.info(f"Resolved image path: {potential_path}")
                    return str(potential_path)
        
        logger.warning(f"Could not resolve image path for: {image_path_param}")
        return None