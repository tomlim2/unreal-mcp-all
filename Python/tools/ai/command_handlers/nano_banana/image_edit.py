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
            # Use Gemini's image generation model for Nano Banana (launched Aug 2025)
            self._model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
            logger.info("Nano Banana (Gemini) initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self._model = None
            return False
    
    def get_supported_commands(self) -> List[str]:
        return ["transform_image_style"]
    
    def _extract_image_metadata(self, image_path: str, resolution_multiplier: float = 1.0, model: str = "gemini-2.5-flash-image") -> Dict[str, Any]:
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

        if not self._ensure_gemini_initialized():
            if not GEMINI_AVAILABLE:
                errors.append("google.generativeai package not available")
            else:
                errors.append("Gemini API not properly configured (check GOOGLE_API_KEY)")

        if command_type == "transform_image_style":
            # Required parameters
            if not params.get("style_prompt"):
                errors.append("style_prompt is required")

            # UID-only system: Check for target_image_uid
            target_image_uid = params.get("target_image_uid")
            if not target_image_uid:
                errors.append("target_image_uid is required (UID format: img_XXX)")
            elif not (target_image_uid.startswith('img_') and target_image_uid[4:].isdigit()):
                errors.append("target_image_uid must be a valid UID format (e.g., 'img_177')")

            # Validate optional parameters
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
        processed = params.copy()
        processed.setdefault("intensity", 0.8)
        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        logger.info(f"Nano Banana Handler: Executing {command_type} with params: {params}")
        if "style_prompt" in params:
            params["style_prompt"] = self._translate_style_prompt_if_needed(params["style_prompt"])
        
        if command_type == "transform_image_style":
            return self._transform_existing_image(params)
        else:
            raise Exception(f"Unsupported command: {command_type}")
    
    def _transform_existing_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform an existing image with style - UID-only system."""
        start_time = time.time()
        request_id = generate_request_id()

        style_prompt = params["style_prompt"]
        intensity = params.get("intensity", 0.8)
        target_image_uid = params["target_image_uid"]  # Required by validation

        # Load target image from UID
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

        # Read target image file as bytes
        with open(file_path, 'rb') as f:
            image_bytes = f.read()

        target_image = {
            'data': image_bytes,
            'mime_type': 'image/png',
            'file_path': file_path
        }
        logger.info(f"Loaded target image from UID {target_image_uid}: {file_path}")

        # Load reference images from UIDs if present
        reference_images = []
        reference_images_param = params.get("reference_images", [])
        if reference_images_param:
            from ...reference_storage import get_reference_image
            for ref in reference_images_param:
                refer_uid = ref.get('refer_uid')
                if refer_uid:
                    logger.info(f"Loading reference image from UID: {refer_uid}")
                    ref_data = get_reference_image(refer_uid)
                    if ref_data:
                        reference_images.append(ref_data)
                    else:
                        logger.warning(f"Reference image UID not found: {refer_uid}")

        try:
            if reference_images:
                # Multi-image approach with references
                logger.info(f"Transform with {len(reference_images)} reference images: {style_prompt} [req_id: {request_id}]")
                styled_image_path = self._apply_nano_banana_with_references(
                    target_image, reference_images, style_prompt, intensity
                )
                origin = "multi_image_transform"
            else:
                # Single image transformation
                logger.info(f"Transform single image: {style_prompt} [req_id: {request_id}]")
                styled_image_path = self._apply_nano_banana_style(
                    file_path, style_prompt, intensity
                )
                origin = "single_image_transform"

            if not styled_image_path:
                return build_error_response(
                    "Failed to apply style transformation",
                    "transformation_failed",
                    request_id,
                    start_time
                )

            # Generate response
            filename = Path(styled_image_path).name
            model = params.get("model", "gemini-2.5-flash-image")

            # Extract metadata for both images
            original_metadata = self._extract_image_metadata(file_path, model=model)
            styled_metadata = self._extract_image_metadata(styled_image_path, model=model)

            # Generate UID for styled result
            new_image_uid = generate_image_uid()
            session_id = params.get('session_id')

            # Add mapping for the styled image
            add_uid_mapping(
                new_image_uid,
                'image',
                filename,
                parent_uid=target_image_uid,
                session_id=session_id,
                metadata={
                    'width': styled_metadata['width'],
                    'height': styled_metadata['height'],
                    'file_path': styled_image_path,
                    'style_type': 'transform_image_style',
                    'model': model,
                    'reference_count': len(reference_images)
                }
            )

            # Build standardized response
            return build_transform_response(
                image_uid=new_image_uid,
                parent_uid=target_image_uid,
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
                origin=origin
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
                model = params.get("model", "gemini-2.5-flash-image")
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

            # Validate reference images - reject tiny/test images
            valid_references = []
            for i, ref_img in enumerate(reference_images):
                data_size = len(ref_img['data']) if isinstance(ref_img['data'], bytes) else len(ref_img['data'].encode())
                if data_size < 500:  # Reject images smaller than 500 bytes (likely test/invalid images)
                    logger.warning(f"Skipping reference image {i+1}: too small ({data_size} bytes) - likely a test image")
                    continue
                valid_references.append(ref_img)

            if not valid_references:
                logger.warning("No valid reference images found - falling back to single image processing")
                # Fallback to single image processing without references
                return self._apply_nano_banana_style_fallback(target_image_data, style_prompt, intensity)

            logger.info(f"Using {len(valid_references)} valid reference images (filtered from {len(reference_images)})")
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
            for ref_img in valid_references[:3]:
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
            transformation_prompt = self._build_multi_image_prompt(style_prompt, valid_references, intensity)

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

        # Special handling for composition purpose (pose changes)
        if 'composition' in purposes:
            return f"""Change the pose and body position of the character in the first image to match the reference image exactly.

CRITICAL INSTRUCTIONS:
1. Copy the EXACT pose, stance, and body position from the reference image
2. Match arm positions, leg positions, and overall posture precisely
3. Keep the character's face, appearance, clothing, and style UNCHANGED
4. Keep the background and environment IDENTICAL
5. Apply {intensity_description} transformation intensity
6. Only modify the pose/position - preserve everything else

Generate the image with the new pose matching the reference."""

        # Style/Color purposes - preserve composition
        purpose_text = ""
        if 'style' in purposes:
            purpose_text += "Use the artistic style from the reference images. "
        if 'color' in purposes:
            purpose_text += "Apply the color palette from the reference images. "

        return f"""Transform the first image using {style_prompt} style with a {intensity_description} intensity.
{purpose_text}
Maintain the original subject and composition while applying the desired style transformation.
The result should be a harmonious blend that preserves the main subject while incorporating the style elements.
Generate the transformed image."""
    
    def _build_gemini_image_prompt(self, style_prompt: str, intensity: float) -> str:
        """Build the image generation prompt for Gemini."""
        intensity_description = "subtle" if intensity < 0.4 else "moderate" if intensity < 0.7 else "strong"

        return f"""Modify ONLY the requested changes: {style_prompt}.
Apply a {intensity_description} transformation that affects ONLY the elements mentioned in the request.
Keep the background, environment, and all other elements completely unchanged.
Only modify what is explicitly requested - preserve everything else exactly as it appears in the original image.
Generate the image with minimal changes."""
    
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

    def _apply_nano_banana_style_fallback(self, target_image_data: Dict[str, Any], style_prompt: str, intensity: float) -> Optional[str]:
        """Fallback method to process target image without reference images."""
        try:
            logger.info(f"Applying single-image transformation (fallback): {style_prompt}")

            # Convert to temporary file for existing logic compatibility
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                if isinstance(target_image_data['data'], bytes):
                    temp_file.write(target_image_data['data'])
                else:
                    # Assume base64 string, decode it
                    temp_file.write(base64.b64decode(target_image_data['data']))
                temp_image_path = temp_file.name

            # Apply style transformation using existing single-image method
            styled_image_path = self._apply_nano_banana_style(
                temp_image_path, style_prompt, intensity
            )

            # Clean up temp file
            os.unlink(temp_image_path)

            return styled_image_path

        except Exception as e:
            logger.error(f"Fallback transformation failed: {e}")
            raise Exception(f"Fallback transformation failed: {str(e)}")
    
