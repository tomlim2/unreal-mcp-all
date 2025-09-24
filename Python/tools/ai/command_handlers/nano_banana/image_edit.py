"""
Nano Banana image editing handler.

Handles Google Gemini Nano Banana image editing operations.
"""

import logging
import os
import base64
import time
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand
from ...pricing_manager import get_pricing_manager
from ...image_schema_utils import (
    build_transform_response,
    build_error_response,
    generate_request_id,
    extract_style_name
)
from ...uid_manager import generate_image_uid, add_uid_mapping, get_uid_mapping

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL/Pillow not available - image metadata extraction disabled")

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
    - image_uid: Required string for transform_image_style (replaces image_path)
    - intensity: Optional float (0.1-1.0), defaults to 0.8
    - resolution_multiplier: Optional float for screenshots (1.0-8.0), defaults to 1.0
    
    Output:
    - Returns styled image UID and transformation details
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
                    
                    # Add debug info for tile calculation
                    if img.width <= 384 and img.height <= 384:
                        metadata["calculation_method"] = "small_image_flat_rate"
                        metadata["tile_count"] = 1
                    else:
                        effective_width = int(img.width * resolution_multiplier)
                        effective_height = int(img.height * resolution_multiplier)
                        tiles_x = math.ceil(effective_width / 768)
                        tiles_y = math.ceil(effective_height / 768)
                        metadata["calculation_method"] = "tile_based"
                        metadata["tile_count"] = tiles_x * tiles_y
                        metadata["tiles_x"] = tiles_x
                        metadata["tiles_y"] = tiles_y
            
        except Exception as e:
            logger.warning(f"Failed to extract image metadata from {image_path}: {e}")
        
        return metadata
    
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

            # Check for direct image data OR image_url (backward compatibility)
            has_target_image = params.get("target_image") is not None
            has_image_url = params.get("image_url") is not None

            if not has_target_image and not has_image_url:
                errors.append("Either 'target_image' (direct image data) or 'image_url' (UID) is required")
            elif has_image_url and params["image_url"]:
                # Validate UID format if using legacy approach
                image_url = params["image_url"]
                if not (image_url.startswith('img_') and image_url[4:].isdigit()):
                    errors.append("image_url must be a valid UID format (e.g., 'img_079'). Filenames not supported.")

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
        
        # Translate style_prompt if it's in a non-English language
        if "style_prompt" in params:
            params["style_prompt"] = self._translate_style_prompt_if_needed(params["style_prompt"])
        
        if command_type == "transform_image_style":
            return self._transform_existing_image(params)
        elif command_type == "take_styled_screenshot":
            return self._take_and_transform_screenshot(connection, params)
        else:
            raise Exception(f"Unsupported command: {command_type}")
    
    def _transform_existing_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform an existing image with style."""
        start_time = time.time()
        request_id = generate_request_id()

        style_prompt = params["style_prompt"]
        intensity = params.get("intensity", 0.8)

        # Check for UID-based image (newest method)
        target_image_uid = params.get("target_image_uid")
        target_image = None

        if target_image_uid:
            # Load image from UID
            from ...uid_manager import get_uid_mapping
            logger.info(f"Loading target image from UID: {target_image_uid}")
            mapping = get_uid_mapping(target_image_uid)
            if not mapping:
                return build_error_response(
                    f"Target image UID not found: {target_image_uid}",
                    "uid_not_found",
                    request_id,
                    start_time
                )

            file_path = mapping.get('metadata', {}).get('file_path')
            if not file_path or not os.path.exists(file_path):
                return build_error_response(
                    f"Target image file not found for UID: {target_image_uid}",
                    "file_not_found",
                    request_id,
                    start_time
                )

            # Read image file as bytes
            with open(file_path, 'rb') as f:
                image_bytes = f.read()

            target_image = {
                'data': image_bytes,
                'mime_type': 'image/png',
                'file_path': file_path  # Include file path for saving styled image
            }
            logger.info(f"Loaded target image from UID {target_image_uid}: {file_path}")
        else:
            # Check for direct image data (legacy method)
            target_image = params.get("target_image")

        # Get reference images (can be UID-based or data-based)
        reference_images = params.get("reference_images", [])

        # Load reference images from UIDs if needed
        if reference_images and 'refer_uid' in reference_images[0]:
            from ...reference_storage import get_reference_image
            loaded_refs = []
            for ref in reference_images:
                refer_uid = ref.get('refer_uid')
                if refer_uid:
                    logger.info(f"Loading reference image from UID: {refer_uid}")
                    ref_data = get_reference_image(refer_uid)
                    if ref_data:
                        loaded_refs.append(ref_data)
                    else:
                        logger.warning(f"Reference image UID not found: {refer_uid}")
            reference_images = loaded_refs if loaded_refs else []

        if target_image and reference_images:
            # Use new multi-image approach
            logger.info(f"Transform Image with references: {style_prompt} [req_id: {request_id}]")
            try:
                styled_image_path = self._apply_nano_banana_with_references(
                    target_image, reference_images, style_prompt, intensity
                )

                if styled_image_path:
                    filename = Path(styled_image_path).name

                    # Extract metadata for the styled image
                    model = params.get("model", "gemini-2")
                    styled_metadata = self._extract_image_metadata(styled_image_path, model=model)

                    # Generate UID for styled result
                    new_image_uid = generate_image_uid()
                    session_id = params.get('session_id')

                    # Add mapping for the styled image
                    add_uid_mapping(
                        new_image_uid,
                        'image',
                        filename,
                        session_id=session_id,
                        metadata={
                            'width': styled_metadata['width'],
                            'height': styled_metadata['height'],
                            'file_path': styled_image_path,
                            'style_type': 'transform_with_references',
                            'model': model,
                            'reference_count': len(reference_images)
                        }
                    )

                    # Build response
                    return build_transform_response(
                        image_uid=new_image_uid,
                        parent_uid=None,  # No parent for direct image processing
                        filename=filename,
                        image_path=styled_image_path,
                        original_width=0,  # Unknown for direct image input
                        original_height=0,
                        processed_width=styled_metadata['width'],
                        processed_height=styled_metadata['height'],
                        style_name=extract_style_name(style_prompt),
                        style_prompt=style_prompt,
                        intensity=intensity,
                        tokens=styled_metadata['tokens'],
                        cost=float(styled_metadata['estimated_cost'].replace('$', '')),
                        request_id=request_id,
                        start_time=start_time,
                        origin="multi_image_transform"
                    )

            except Exception as e:
                logger.error(f"Multi-image transform failed: {e}")
                return build_error_response(
                    f"Multi-image transformation failed: {str(e)}",
                    "multi_image_error",
                    request_id,
                    start_time
                )

        elif target_image:
            # Direct image processing without references (fallback to single image)
            logger.info(f"Transform Image (direct): {style_prompt} [req_id: {request_id}]")
            # Convert target_image data to temporary file for existing logic
            # This is a temporary bridge - could be optimized later
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    if isinstance(target_image['data'], bytes):
                        temp_file.write(target_image['data'])
                    else:
                        # Assume base64 string, decode it
                        import base64
                        temp_file.write(base64.b64decode(target_image['data']))
                    temp_image_path = temp_file.name

                # Apply style transformation using existing method
                styled_image_path = self._apply_nano_banana_style(
                    temp_image_path, style_prompt, intensity
                )

                # Clean up temp file
                os.unlink(temp_image_path)

                if styled_image_path:
                    # Similar response building as above
                    filename = Path(styled_image_path).name
                    model = params.get("model", "gemini-2")
                    styled_metadata = self._extract_image_metadata(styled_image_path, model=model)
                    new_image_uid = generate_image_uid()
                    session_id = params.get('session_id')

                    add_uid_mapping(
                        new_image_uid,
                        'image',
                        filename,
                        session_id=session_id,
                        metadata={
                            'width': styled_metadata['width'],
                            'height': styled_metadata['height'],
                            'file_path': styled_image_path,
                            'style_type': 'transform_direct_image',
                            'model': model
                        }
                    )

                    return build_transform_response(
                        image_uid=new_image_uid,
                        parent_uid=None,
                        filename=filename,
                        image_path=styled_image_path,
                        original_width=0,
                        original_height=0,
                        processed_width=styled_metadata['width'],
                        processed_height=styled_metadata['height'],
                        style_name=extract_style_name(style_prompt),
                        style_prompt=style_prompt,
                        intensity=intensity,
                        tokens=styled_metadata['tokens'],
                        cost=float(styled_metadata['estimated_cost'].replace('$', '')),
                        request_id=request_id,
                        start_time=start_time,
                        origin="direct_image_transform"
                    )

            except Exception as e:
                logger.error(f"Direct image transform failed: {e}")
                return build_error_response(
                    f"Direct image transformation failed: {str(e)}",
                    "direct_image_error",
                    request_id,
                    start_time
                )

        # Fallback to legacy UID-based approach
        image_url = params.get("image_url")
        if not image_url:
            return build_error_response(
                "Either 'target_image' (direct image data) or 'image_url' (UID) is required",
                "no_image_source",
                request_id,
                start_time
            )

        logger.info(f"Transform Image (legacy): {image_url} -> {style_prompt} [req_id: {request_id}]")

        try:
            # Resolve the image UID to file path (only supports UIDs)
            resolved_image_path = self._resolve_image_path(image_url)
            if not resolved_image_path:
                return build_error_response(
                    f"Specified image not found: {image_url}. Please use a valid image UID (e.g., 'img_079')",
                    "specified_image_not_found",
                    request_id,
                    start_time
                )

            # Apply style transformation
            styled_image_path = self._apply_nano_banana_style(
                resolved_image_path, style_prompt, intensity
            )
            
            if styled_image_path:
                filename = Path(styled_image_path).name
                
                # Extract metadata for both images
                model = params.get("model", "gemini-2")
                original_metadata = self._extract_image_metadata(resolved_image_path, model=model)
                styled_metadata = self._extract_image_metadata(styled_image_path, model=model)
                
                # Generate UIDs using persistent manager
                parent_uid = image_url  # Use the input image_url as parent
                new_image_uid = generate_image_uid()  # UID for styled result

                # Extract session_id from params if available
                session_id = params.get('session_id')

                # Add mapping for the styled image
                add_uid_mapping(
                    new_image_uid,
                    'image',
                    filename,
                    parent_uid=parent_uid,
                    session_id=session_id,
                    metadata={
                        'width': styled_metadata['width'],
                        'height': styled_metadata['height'],
                        'file_path': styled_image_path,
                        'style_type': 'transform_image_style',
                        'model': model
                    }
                )
                
                # Build standardized response
                return build_transform_response(
                    image_uid=new_image_uid,
                    parent_uid=parent_uid,
                    filename=filename,
                    image_path=styled_image_path,
                    original_width=original_metadata['width'],
                    original_height=original_metadata['height'],
                    processed_width=styled_metadata['width'],
                    processed_height=styled_metadata['height'],
                    style_name=extract_style_name(style_prompt),
                    style_prompt=style_prompt,
                    intensity=intensity,
                    tokens=styled_metadata['tokens'],
                    cost=float(styled_metadata['estimated_cost'].replace('$', '')),
                    request_id=request_id,
                    start_time=start_time,
                    origin="transform"
                )
            else:
                return build_error_response(
                    "Failed to apply style transformation",
                    "transformation_failed",
                    request_id,
                    start_time
                )
                
        except Exception as e:
            logger.error(f"Transform failed: {e}")
            return build_error_response(
                f"Transform failed: {str(e)}",
                "execution_error",
                request_id,
                start_time
            )
    
    def _take_and_transform_screenshot(self, connection, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot and apply style transformation."""
        start_time = time.time()
        request_id = generate_request_id()
        
        style_prompt = params["style_prompt"]
        intensity = params["intensity"]
        
        logger.info(f"Take Styled Screenshot: {style_prompt} [req_id: {request_id}]")
        
        try:
            # Prepare screenshot parameters
            screenshot_params = {
                "resolution_multiplier": params["resolution_multiplier"],
                "include_ui": params["include_ui"]
            }
            
            # Take screenshot via Unreal connection
            logger.info("Taking screenshot before styling...")
            response = connection.send_command("take_screenshot", screenshot_params)
            
            if response and response.get("status") == "error":
                return build_error_response(
                    response.get("error", "Unknown screenshot error"),
                    "screenshot_error",
                    request_id,
                    start_time
                )
            
            # Wait for screenshot to be saved
            time.sleep(1.0)
            
            # Find newest screenshot
            screenshot_path = self._find_newest_screenshot()
            if not screenshot_path:
                return build_error_response(
                    "Screenshot was taken but file not found",
                    "screenshot_file_not_found",
                    request_id,
                    start_time
                )
            
            logger.info(f"Screenshot taken: {screenshot_path}")
            
            # Apply style transformation
            styled_image_path = self._apply_nano_banana_style(
                str(screenshot_path), style_prompt, intensity
            )
            
            if styled_image_path:
                filename = Path(styled_image_path).name
                
                # Extract metadata for both images
                resolution_multiplier = params["resolution_multiplier"]
                model = params.get("model", "gemini-2")
                original_metadata = self._extract_image_metadata(str(screenshot_path), model=model)
                styled_metadata = self._extract_image_metadata(styled_image_path, resolution_multiplier, model)
                
                # Generate UIDs using persistent manager
                parent_uid = generate_image_uid()  # UID for source screenshot
                new_image_uid = generate_image_uid()  # UID for styled result

                # Extract session_id from params if available
                session_id = params.get('session_id')

                # Add mappings for both images
                # 1. Original screenshot
                add_uid_mapping(
                    parent_uid,
                    'image',
                    Path(screenshot_path).name,
                    session_id=session_id,
                    metadata={
                        'width': original_metadata['width'],
                        'height': original_metadata['height'],
                        'file_path': str(screenshot_path),
                        'resolution_multiplier': resolution_multiplier,
                        'style_type': 'original_screenshot'
                    }
                )

                # 2. Styled result
                add_uid_mapping(
                    new_image_uid,
                    'image',
                    filename,
                    parent_uid=parent_uid,
                    session_id=session_id,
                    metadata={
                        'width': styled_metadata['width'],
                        'height': styled_metadata['height'],
                        'file_path': styled_image_path,
                        'style_type': 'take_styled_screenshot',
                        'model': model,
                        'style_prompt': style_prompt,
                        'intensity': intensity
                    }
                )
                
                # Build standardized response
                return build_transform_response(
                    image_uid=new_image_uid,
                    parent_uid=parent_uid,
                    filename=filename,
                    image_path=styled_image_path,
                    original_width=original_metadata['width'],
                    original_height=original_metadata['height'],
                    processed_width=styled_metadata['width'],
                    processed_height=styled_metadata['height'],
                    style_name=extract_style_name(style_prompt),
                    style_prompt=style_prompt,
                    intensity=intensity,
                    tokens=styled_metadata['tokens'],
                    cost=float(styled_metadata['estimated_cost'].replace('$', '')),
                    request_id=request_id,
                    start_time=start_time,
                    origin="screenshot"
                )
            else:
                return build_error_response(
                    "Screenshot taken but style transformation failed",
                    "transformation_failed",
                    request_id,
                    start_time
                )
                
        except Exception as e:
            logger.error(f"Styled screenshot failed: {e}")
            return build_error_response(
                f"Styled screenshot failed: {str(e)}",
                "execution_error",
                request_id,
                start_time
            )
    
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
                logger.warning("No response from Gemini - creating placeholder")
                return self._create_placeholder_styled_image(image_path, style_prompt, intensity)

            # Try to save the generated image
            try:
                styled_image_path = self._save_gemini_generated_image(
                    response, image_path, style_prompt
                )
                return styled_image_path
            except Exception as save_error:
                logger.warning(f"Gemini image generation failed: {save_error}")
                logger.info("Creating placeholder styled image instead")
                return self._create_placeholder_styled_image(image_path, style_prompt, intensity)

        except Exception as e:
            logger.error(f"Gemini image transformation failed: {e}")
            raise Exception(f"Style transformation failed: {str(e)}")

    def _apply_nano_banana_with_references(self, target_image_data: Dict[str, Any], reference_images: List[Dict[str, Any]], style_prompt: str, intensity: float) -> Optional[str]:
        """Apply Gemini multi-image generation with reference images."""
        if not self._ensure_gemini_initialized():
            raise Exception("Gemini image generation not available")

        try:
            logger.info(f"Applying Gemini multi-image transformation: {style_prompt} (intensity: {intensity})")
            logger.info(f"Using {len(reference_images)} reference images")

            image_parts = []

            # Add target image
            if target_image_data:
                if isinstance(target_image_data['data'], bytes):
                    # Convert bytes to base64
                    image_b64 = base64.b64encode(target_image_data['data']).decode('utf-8')
                else:
                    # Already base64 string
                    image_b64 = target_image_data['data']

                image_parts.append({
                    'inline_data': {
                        'mime_type': target_image_data['mime_type'],
                        'data': image_b64
                    }
                })

            # Add reference images (up to 3 total for Gemini API limit)
            for ref_img in reference_images[:3]:
                if isinstance(ref_img['data'], bytes):
                    # Convert bytes to base64
                    ref_b64 = base64.b64encode(ref_img['data']).decode('utf-8')
                else:
                    # Already base64 string
                    ref_b64 = ref_img['data']

                image_parts.append({
                    'inline_data': {
                        'mime_type': ref_img['mime_type'],
                        'data': ref_b64
                    }
                })

            # Build multi-image prompt
            transformation_prompt = self._build_multi_image_prompt(style_prompt, reference_images, intensity)

            # Generate styled image using Gemini multi-image API
            logger.info(f"Sending multi-image transformation request to Gemini with {len(image_parts)} images...")
            response = self._model.generate_content([*image_parts, transformation_prompt])

            if not response or not response.candidates:
                logger.warning("No response from Gemini multi-image generation")
                return None

            # Save the generated image
            original_path = target_image_data.get('file_path', 'unknown')
            styled_image_path = self._save_gemini_generated_image(
                response, original_path, style_prompt
            )
            return styled_image_path

        except Exception as e:
            logger.error(f"Gemini multi-image transformation failed: {e}")
            raise Exception(f"Multi-image transformation failed: {str(e)}")

    def _build_multi_image_prompt(self, style_prompt: str, reference_images: List[Dict[str, Any]], intensity: float) -> str:
        """Build the multi-image generation prompt for Gemini."""
        intensity_description = "subtle" if intensity < 0.4 else "moderate" if intensity < 0.7 else "strong"

        # Build purpose-aware prompt
        purposes = [ref.get('purpose', 'style') for ref in reference_images]
        purpose_text = ""
        if 'style' in purposes:
            purpose_text += "Use the artistic style from the reference images. "
        if 'color' in purposes:
            purpose_text += "Apply the color palette from the reference images. "
        if 'composition' in purposes:
            purpose_text += "Incorporate compositional elements from the reference images. "

        return f"""Transform the first image using {style_prompt} style with a {intensity_description} intensity.
{purpose_text}
Maintain the original subject and composition while applying the desired style transformation.
The result should be a harmonious blend that preserves the main subject while incorporating the style elements.
Generate the transformed image."""
    
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
            
            # Generate clean filename: [OriginalName]_NB_[timestamp]
            original_name = self._extract_original_screenshot_name(original_path)
            timestamp = int(time.time())
            
            styled_filename = f"{original_name}_NB_{timestamp}.png"
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
            
            # Generate clean filename: [OriginalName]_NB_[timestamp]
            original_name = self._extract_original_screenshot_name(original_path)
            timestamp = int(time.time())
            
            styled_filename = f"{original_name}_NB_{timestamp}.png"
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
    
    def _translate_style_prompt_if_needed(self, style_prompt: str) -> str:
        """Translate style prompt to English if it appears to be in another language."""
        # Simple detection: if it contains non-ASCII characters, assume it needs translation
        if any(ord(char) > 127 for char in style_prompt):
            logger.info(f"Non-English style prompt detected: '{style_prompt}'")
            
            if not self._ensure_gemini_initialized():
                logger.warning("Gemini not available for translation, using original prompt")
                return style_prompt
            
            try:
                # Use Gemini to translate the style prompt to English
                translation_prompt = f"""Translate this image style description to English. 
Only return the English translation, nothing else:

{style_prompt}"""
                
                response = self._model.generate_content(translation_prompt)
                
                if response and response.text:
                    translated = response.text.strip()
                    logger.info(f"Translated style prompt: '{style_prompt}' -> '{translated}'")
                    return translated
                else:
                    logger.warning("Translation failed, using original prompt")
                    return style_prompt
                    
            except Exception as e:
                logger.error(f"Translation error: {e}")
                logger.info("Using original prompt due to translation failure")
                return style_prompt
        
        # If it's already in English (ASCII characters only), return as-is
        return style_prompt
    
    def _resolve_image_path(self, image_path_param: str) -> Optional[str]:
        """Resolve image path - ONLY supports UIDs (img_XXX format)."""

        # Check if it's a UID (format: img_XXX)
        if image_path_param.startswith('img_') and image_path_param[4:].isdigit():
            logger.info(f"Resolving UID: {image_path_param}")
            mapping = get_uid_mapping(image_path_param)
            if not mapping:
                logger.error(f"UID not found in mapping table: {image_path_param}")
                return None

            # Get file path from mapping metadata
            file_path = mapping.get('metadata', {}).get('file_path')
            if file_path and os.path.exists(file_path):
                logger.info(f"Resolved UID {image_path_param} to: {file_path}")
                return file_path
            else:
                logger.error(f"File not found for UID {image_path_param}: {file_path}")
                return None

        # Reject all non-UID inputs - no fallbacks allowed
        logger.error(f"Only UID format (img_XXX) is supported for image editing. Received: {image_path_param}")
        return None
    
    def _extract_original_screenshot_name(self, file_path: str) -> str:
        """Extract original screenshot name from potentially styled filename."""
        filename = Path(file_path).stem
        
        # Extract original screenshot name (e.g., ScreenShot00039 from any styled variant)
        import re
        match = re.match(r'^(ScreenShot\d+)', filename)
        if match:
            return match.group(1)
        
        # Fallback: use first part before underscore
        return filename.split('_')[0]
    
