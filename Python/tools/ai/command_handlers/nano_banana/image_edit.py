import logging
import os
import base64
import time
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand
from ...session_management.utils.path_manager import get_path_manager
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

            # UID-only system: Check for target_image_uid (or fallback to image_uid)
            target_image_uid = params.get("target_image_uid") or params.get("image_uid")
            if not target_image_uid:
                errors.append("target_image_uid or image_uid is required (UID format: img_XXX)")
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

        # Auto-assign target_image_uid from image_uid if not provided
        if command_type == "transform_image_style":
            if not processed.get("target_image_uid") and processed.get("image_uid"):
                processed["target_image_uid"] = processed["image_uid"]
                logger.info(f"Auto-assigned target_image_uid: {processed['target_image_uid']}")

        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        logger.info(f"Nano Banana Handler: Executing {command_type} with params: {params}")

        # DEBUG: Log detailed parameter analysis
        logger.info(f"🔍 DEBUG - Parameter analysis:")
        logger.info(f"  - main_prompt present: {'main_prompt' in params} = '{params.get('main_prompt', 'NOT_PRESENT')}'")
        logger.info(f"  - reference_prompts present: {'reference_prompts' in params} = {params.get('reference_prompts', 'NOT_PRESENT')}")
        logger.info(f"  - style_prompt present: {'style_prompt' in params} = '{params.get('style_prompt', 'NOT_PRESENT')}'")

        if "reference_images" in params:
            ref_images = params["reference_images"]
            logger.info(f"  - reference_images count: {len(ref_images)}")
            for i, ref in enumerate(ref_images):
                logger.info(f"    [{i}] refer_uid: {ref.get('refer_uid', 'NO_UID')}, purpose: {ref.get('purpose', 'NO_PURPOSE')}")

        # Handle new prompt organization system
        if "main_prompt" in params or "reference_prompts" in params:
            logger.info("🎯 Using NEW prompt organization system")
            params["style_prompt"] = self._translate_and_organize_prompts(
                main_prompt=params.get("main_prompt", ""),
                reference_prompts=params.get("reference_prompts", [])
            )
        elif "style_prompt" in params:
            logger.info("🔄 Using LEGACY single prompt handling")
            # Legacy single prompt handling
            params["style_prompt"] = self._translate_style_prompt_if_needed(params["style_prompt"])
        else:
            logger.warning("⚠️ No prompt data found in parameters!")

        logger.info(f"📝 Final style_prompt: '{params.get('style_prompt', 'NO_STYLE_PROMPT')}'")

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

            # Pre-flight request size validation
            size_info = self._estimate_request_size(target_image_data, reference_images, style_prompt)
            logger.info(f"Request size estimation: {size_info['total_size_mb']}MB, {size_info['estimated_tokens']} tokens")

            if not size_info['within_limits']:
                logger.warning(f"Request may exceed API limits - proceeding with caution")
                if size_info['total_size_mb'] >= 20.0:
                    raise Exception(f"Request too large: {size_info['total_size_mb']}MB exceeds 20MB limit")
                if size_info['estimated_tokens'] >= 1000000:
                    logger.warning(f"Token count may exceed limit: {size_info['estimated_tokens']}")
                    # Continue but log warning

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
        """Build the multi-image generation prompt for Gemini using organized prompts."""
        intensity_description = "subtle" if intensity < 0.4 else "moderate" if intensity < 0.7 else "strong"

        # The style_prompt is already organized by _translate_and_organize_prompts function
        # So we just need to create the final transformation instruction

        # Legacy purpose-based handling for backward compatibility
        # (in case old-style purpose data is still passed)
        purposes = [ref.get('purpose', 'style') for ref in reference_images]
        if 'composition' in purposes:
            # Special case: composition changes require different handling
            return f"""Change the pose and body position of the character in the first image to match the reference image exactly.

CRITICAL INSTRUCTIONS:
1. Copy the EXACT pose, stance, and body position from the reference image
2. Match arm positions, leg positions, and overall posture precisely
3. Keep the character's face, appearance, clothing, and style UNCHANGED
4. Keep the background and environment IDENTICAL
5. Apply {intensity_description} transformation intensity
6. Only modify the pose/position - preserve everything else

Additional instructions: {style_prompt}
Generate the image with the new pose matching the reference."""

        # Use the already organized and translated style prompt
        return f"""Transform the first image using the following instructions with a {intensity_description} intensity:

{style_prompt}

INSTRUCTIONS:
1. Apply the transformation described above
2. Use the reference images to guide the transformation
3. Maintain the original subject and composition while applying changes
4. Create a harmonious result that preserves the main subject
5. Incorporate elements from reference images as specified

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
            # Create styled directory using centralized path management
            path_manager = get_path_manager()
            styled_dir_path = path_manager.get_unreal_styled_images_path()
            if not styled_dir_path:
                raise Exception("Unable to determine styled images directory path")

            styled_dir = Path(styled_dir_path)
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
            # Create styled directory using centralized path management
            path_manager = get_path_manager()
            styled_dir_path = path_manager.get_unreal_styled_images_path()
            if not styled_dir_path:
                raise Exception("Unable to determine styled images directory path")

            styled_dir = Path(styled_dir_path)
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
            
            # No image data found in Gemini response
            candidates_count = len(response.candidates) if response.candidates else 0
            logger.error(f"No image data found in Gemini response (candidates: {candidates_count})")
            raise Exception("No image data found in Gemini response")
            
        except Exception as e:
            logger.error(f"Failed to save Gemini generated image: {e}")
            raise Exception(f"Failed to save generated image: {str(e)}")
    
    def _find_newest_screenshot(self) -> Optional[Path]:
        """Find the newest screenshot file in the WindowsEditor directory."""
        try:
            # Get screenshot directory using centralized path management
            path_manager = get_path_manager()
            screenshot_dir_path = path_manager.get_unreal_screenshots_path()
            if not screenshot_dir_path:
                logger.warning("Unable to determine screenshot directory path - cannot find screenshot files")
                return None

            # Look in WindowsEditor subdirectory where Unreal saves high-res screenshots
            screenshot_dir = Path(screenshot_dir_path)
            
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

    def _translate_and_organize_prompts(self, main_prompt: str, reference_prompts: List[str]) -> str:
        """Translate and organize multiple prompts using LLM-based prompt combination."""
        try:
            # Collect all non-empty prompts
            all_prompts = []

            if main_prompt.strip():
                all_prompts.append(f"Main transformation: {main_prompt.strip()}")

            for i, ref_prompt in enumerate(reference_prompts):
                if ref_prompt.strip():
                    all_prompts.append(f"Reference {i+1}: {ref_prompt.strip()}")

            # If no prompts provided, use default
            if not all_prompts:
                logger.warning("No main or reference prompts provided")
                return "Transform the image with artistic style"

            # If only one prompt, just translate it
            if len(all_prompts) == 1:
                single_prompt = all_prompts[0].split(": ", 1)[1] if ": " in all_prompts[0] else all_prompts[0]
                return self._translate_style_prompt_if_needed(single_prompt)

            # Use LLM to organize multiple prompts
            return self._organize_prompts_with_llm(all_prompts)

        except Exception as e:
            logger.error(f"Prompt organization failed: {e}")
            # Fallback to first available prompt or default
            if main_prompt.strip():
                return self._translate_style_prompt_if_needed(main_prompt)
            elif reference_prompts and any(p.strip() for p in reference_prompts):
                first_ref = next(p for p in reference_prompts if p.strip())
                return self._translate_style_prompt_if_needed(first_ref)
            else:
                return "Transform the image with artistic style"

    def _organize_prompts_with_llm(self, all_prompts: List[str]) -> str:
        """Use LLM to organize multiple prompts into a coherent single prompt."""
        if not self._ensure_gemini_initialized():
            logger.warning("Gemini not available for prompt organization, concatenating prompts")
            # Fallback: simple concatenation without LLM
            return self._concatenate_prompts_simple(all_prompts)

        try:
            # Create organization prompt for Gemini
            prompts_text = "\n".join(f"- {prompt}" for prompt in all_prompts)

            organization_request = f"""Combine these image transformation instructions into a single, coherent prompt:

{prompts_text}

Requirements:
1. Create ONE clear, concise transformation prompt
2. Maintain the intent of all instructions
3. Resolve any conflicts by prioritizing main transformation over references
4. Keep the result under 800 characters
5. Use clear, specific visual descriptions
6. Return ONLY the combined prompt, no explanations

Combined prompt:"""

            logger.info(f"Organizing {len(all_prompts)} prompts using Gemini LLM")
            response = self._model.generate_content(organization_request)

            if response and response.text:
                organized_prompt = response.text.strip()

                # Apply length limits with truncation
                if len(organized_prompt) > 800:
                    logger.warning(f"Organized prompt too long ({len(organized_prompt)} chars), truncating")
                    organized_prompt = organized_prompt[:800].rsplit(' ', 1)[0] + "..."

                logger.info(f"LLM organized prompt: '{organized_prompt[:100]}...' ({len(organized_prompt)} chars)")
                return organized_prompt
            else:
                logger.warning("LLM organization failed, using fallback")
                return self._concatenate_prompts_simple(all_prompts)

        except Exception as e:
            logger.error(f"LLM prompt organization error: {e}")
            return self._concatenate_prompts_simple(all_prompts)

    def _concatenate_prompts_simple(self, all_prompts: List[str]) -> str:
        """Simple fallback method to combine prompts without LLM."""
        # Remove prefixes and combine with appropriate conjunctions
        clean_prompts = []
        for prompt in all_prompts:
            clean = prompt.split(": ", 1)[1] if ": " in prompt else prompt
            clean_prompts.append(clean.strip())

        # Combine with "and" and apply basic length limits
        combined = "; ".join(clean_prompts)

        if len(combined) > 800:
            logger.warning(f"Concatenated prompt too long ({len(combined)} chars), truncating")
            combined = combined[:800].rsplit(';', 1)[0] + "..."

        logger.info(f"Simple concatenation result: '{combined[:100]}...' ({len(combined)} chars)")
        return combined

    def _estimate_request_size(self, image_data: Dict[str, Any], reference_images: List[Dict[str, Any]], prompt: str) -> Dict[str, Any]:
        """Estimate API request size and token count for validation."""
        total_size_mb = 0.0
        estimated_tokens = 0

        try:
            # Calculate image sizes
            if image_data and 'data' in image_data:
                if isinstance(image_data['data'], bytes):
                    total_size_mb += len(image_data['data']) / (1024 * 1024)
                else:
                    # Base64 string - decode to get actual size
                    import base64
                    try:
                        decoded = base64.b64decode(image_data['data'])
                        total_size_mb += len(decoded) / (1024 * 1024)
                    except:
                        # Estimate: base64 is ~33% larger than binary
                        total_size_mb += (len(image_data['data']) * 0.75) / (1024 * 1024)

            # Calculate reference image sizes
            for ref_img in reference_images:
                if 'data' in ref_img:
                    if isinstance(ref_img['data'], bytes):
                        total_size_mb += len(ref_img['data']) / (1024 * 1024)
                    else:
                        # Base64 string estimation
                        import base64
                        try:
                            decoded = base64.b64decode(ref_img['data'])
                            total_size_mb += len(decoded) / (1024 * 1024)
                        except:
                            total_size_mb += (len(ref_img['data']) * 0.75) / (1024 * 1024)

            # Estimate tokens (rough calculation: ~4 chars per token for text)
            estimated_tokens += len(prompt) // 4

            # Each image contributes to token count (Google's tile-based calculation is complex)
            # For estimation: assume ~1000-2000 tokens per image
            estimated_tokens += (1 + len(reference_images)) * 1500  # Conservative estimate

            return {
                'total_size_mb': round(total_size_mb, 2),
                'estimated_tokens': estimated_tokens,
                'prompt_length': len(prompt),
                'image_count': 1 + len(reference_images),
                'within_limits': total_size_mb < 18.0 and estimated_tokens < 900000  # Conservative limits
            }

        except Exception as e:
            logger.warning(f"Request size estimation failed: {e}")
            return {
                'total_size_mb': 0.0,
                'estimated_tokens': 0,
                'prompt_length': len(prompt),
                'image_count': 1 + len(reference_images),
                'within_limits': True  # Assume OK if estimation fails
            }

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
    
