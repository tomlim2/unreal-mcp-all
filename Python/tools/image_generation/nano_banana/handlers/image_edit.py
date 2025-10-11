import logging
import os
import base64
import time
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from tools.ai.command_handlers.main import BaseCommandHandler
from tools.ai.command_handlers.validation import ValidatedCommand
from core.utils.path_manager import get_path_manager
from tools.ai.pricing_manager import get_pricing_manager
from core.schemas import (
    build_transform_response,
    generate_request_id,
    extract_style_name
)
from core.resources.uid_manager import generate_image_uid, add_uid_mapping, get_uid_mapping
from core.errors import (
    image_not_found, image_size_exceeded, transformation_failed,
    api_unavailable, AppError, ErrorCategory
)

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
        return ["image_to_image", "text_to_image"]
    
    def _extract_image_dimensions(self, image_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract width and height from image data (bytes or file path)."""
        dimensions = {'width': 0, 'height': 0}

        try:
            if PIL_AVAILABLE:
                # Try to extract from file path first
                if image_data.get('file_path'):
                    with Image.open(image_data['file_path']) as img:
                        dimensions['width'] = img.width
                        dimensions['height'] = img.height
                        return dimensions

                # Try to extract from bytes data
                if image_data.get('data'):
                    import io
                    if isinstance(image_data['data'], bytes):
                        img_bytes = image_data['data']
                    else:
                        # Assume base64 string
                        img_bytes = base64.b64decode(image_data['data'])

                    with Image.open(io.BytesIO(img_bytes)) as img:
                        dimensions['width'] = img.width
                        dimensions['height'] = img.height
                        return dimensions
        except Exception as e:
            logger.warning(f"Failed to extract image dimensions: {e}")

        return dimensions

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
        """Validate Nano Banana commands with new schema (fal.ai style)."""
        errors = []

        if not self._ensure_gemini_initialized():
            if not GEMINI_AVAILABLE:
                errors.append("google.generativeai package not available")
            else:
                errors.append("Gemini API not properly configured (check GOOGLE_API_KEY)")

        # Common validation: prompt is required
        if not params.get("prompt"):
            errors.append("prompt is required")

        # Validate images array
        images = params.get("images", [])
        if not isinstance(images, list):
            errors.append("images must be an array")

        if command_type == "image_to_image":
            # I2I: images[0] is MAIN IMAGE (required)
            if len(images) == 0:
                errors.append("image_to_image requires at least 1 image (main image at images[0])")
            elif len(images) > 4:
                errors.append("Maximum 4 images allowed (images[0]=main + images[1,2,3]=references)")

        elif command_type == "text_to_image":
            # T2I: images are optional reference images (max 3)
            if len(images) > 3:
                errors.append("Maximum 3 reference images allowed for text_to_image (images[0,1,2])")

        # Validate config.aspect_ratio if provided
        config = params.get("config", {})
        if "aspect_ratio" in config:
            valid_ratios = ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
            if config["aspect_ratio"] not in valid_ratios:
                errors.append(f"config.aspect_ratio must be one of {valid_ratios}")

        # Validate config.num_images if provided
        if "num_images" in config:
            num_images = config["num_images"]
            if not isinstance(num_images, int) or num_images < 1 or num_images > 4:
                errors.append("config.num_images must be an integer between 1 and 4")

        # Validate config.output_format if provided
        if "output_format" in config:
            valid_formats = ["png", "jpeg", "jpg"]
            if config["output_format"] not in valid_formats:
                errors.append(f"config.output_format must be one of {valid_formats}")

        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        processed = params.copy()

        # Ensure config exists
        if "config" not in processed:
            processed["config"] = {}

        config = processed["config"]

        # Set default config values (fal.ai style)
        config.setdefault("aspect_ratio", "16:9")  # 기존 방식 유지
        config.setdefault("num_images", 1)
        config.setdefault("output_format", "png")

        # Ensure images array exists
        processed.setdefault("images", [])

        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        logger.info(f"Nano Banana Handler: Executing {command_type} with params: {params}")

        # Get prompt and translate if needed (Korean → English)
        prompt = params.get("prompt", "")
        if prompt and self._is_non_english(prompt):
            logger.info(f"Non-English prompt detected, translating: '{prompt}'")
            params["prompt"] = self._translate_style_prompt_if_needed(prompt)

        logger.info(f"📝 Final prompt: '{params.get('prompt', 'NO_PROMPT')}'")

        if command_type == "image_to_image":
            return self._image_to_image(params)
        elif command_type == "text_to_image":
            return self._text_to_image(params)
        else:
            from core.errors import validation_failed
            raise validation_failed(
                message=f"Unsupported command: {command_type}",
                invalid_params={"type": command_type},
                suggestion="Use 'image_to_image' or 'text_to_image'"
            )
    
    def _image_to_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Image-to-Image transformation (fal.ai style).

        Schema:
        - images[0] = MAIN IMAGE (required)
        - images[1,2,3] = Reference images (optional)
        """
        start_time = time.time()
        request_id = generate_request_id()

        prompt = params["prompt"]
        images = params["images"]
        config = params["config"]
        session_id = params.get("session_id")

        logger.info(f"I2I: prompt='{prompt}', images={len(images)}, config={config} [req_id: {request_id}]")

        # images[0] = MAIN IMAGE (required, validated already)
        main_image = images[0]

        # images[1,2,3] = Reference images (optional)
        reference_images = images[1:] if len(images) > 1 else []

        # Generate UID and filename BEFORE transformation
        new_image_uid = generate_image_uid()
        model = "gemini-2.5-flash-image"
        output_filename = self._generate_styled_filename(new_image_uid, model, "i2i")

        try:
            # Apply transformation
            if reference_images:
                logger.info(f"I2I with {len(reference_images)} reference images")
                result_path = self._transform_image_with_references(
                    main_image, reference_images, prompt, output_filename
                )
            else:
                logger.info("I2I without reference images")
                result_path = self._transform_image_with_references(
                    main_image, [], prompt, output_filename
                )

            if not result_path:
                raise transformation_failed("Image transformation returned no result")

            # Extract metadata
            result_metadata = self._extract_image_metadata(result_path, model=model)

            # Add UID mapping
            add_uid_mapping(
                new_image_uid,
                'image',
                output_filename,
                parent_uid=None,  # New schema: no parent tracking
                session_id=session_id,
                metadata={
                    'width': result_metadata['width'],
                    'height': result_metadata['height'],
                    'file_path': result_path,
                    'style_type': 'image_to_image',
                    'model': model,
                    'reference_count': len(reference_images),
                    'source': 'image_to_image'
                }
            )

            # Build response
            return build_transform_response(
                image_uid=new_image_uid,
                parent_uid=None,
                filename=output_filename,
                image_path=result_path,
                original_width=0,
                original_height=0,
                processed_width=result_metadata['width'],
                processed_height=result_metadata['height'],
                style_name=extract_style_name(prompt),
                style_prompt=prompt,
                intensity=1.0,
                tokens=result_metadata['tokens'],
                cost=float(result_metadata['estimated_cost'].replace('$', '')),
                request_id=request_id,
                start_time=start_time,
                origin="image_to_image"
            )

        except AppError:
            raise
        except Exception as e:
            logger.error(f"I2I failed: {e}")
            raise transformation_failed(str(e))

    def _text_to_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Text-to-Image generation (fal.ai style).

        Schema:
        - images[0,1,2] = Optional reference images for style
        """
        start_time = time.time()
        request_id = generate_request_id()

        prompt = params["prompt"]
        images = params["images"]  # Optional reference images
        config = params["config"]
        session_id = params.get("session_id")

        aspect_ratio = config.get("aspect_ratio", "16:9")

        logger.info(f"T2I: prompt='{prompt}', refs={len(images)}, aspect_ratio={aspect_ratio} [req_id: {request_id}]")

        # Generate UID and filename
        new_image_uid = generate_image_uid()
        model = "gemini-2.5-flash-image"
        output_filename = self._generate_styled_filename(new_image_uid, model, "t2i")

        try:
            # Build generation prompt
            generation_prompt = self._build_text_to_image_prompt(prompt, aspect_ratio, images)

            # Generate image
            result_path = self._generate_image_from_text(
                generation_prompt, images, output_filename
            )

            if not result_path:
                raise transformation_failed("Text-to-image generation returned no result")

            # Extract metadata
            result_metadata = self._extract_image_metadata(result_path, model=model)

            # Add UID mapping
            add_uid_mapping(
                new_image_uid,
                'image',
                output_filename,
                parent_uid=None,
                session_id=session_id,
                metadata={
                    'width': result_metadata['width'],
                    'height': result_metadata['height'],
                    'file_path': result_path,
                    'style_type': 'text_to_image',
                    'model': model,
                    'aspect_ratio': aspect_ratio,
                    'reference_count': len(images),
                    'source': 'text_to_image'
                }
            )

            # Build response
            return build_transform_response(
                image_uid=new_image_uid,
                parent_uid=None,
                filename=output_filename,
                image_path=result_path,
                original_width=0,
                original_height=0,
                processed_width=result_metadata['width'],
                processed_height=result_metadata['height'],
                style_name=extract_style_name(prompt),
                style_prompt=prompt,
                intensity=1.0,
                tokens=result_metadata['tokens'],
                cost=float(result_metadata['estimated_cost'].replace('$', '')),
                request_id=request_id,
                start_time=start_time,
                origin="text_to_image"
            )

        except AppError:
            raise
        except Exception as e:
            logger.error(f"T2I failed: {e}")
            raise transformation_failed(str(e))

    def _apply_nano_banana_style(self, image_path: str, style_prompt: str, output_filename: str = None) -> Optional[str]:
        """Apply Gemini image generation style transformation to image."""
        if not self._ensure_gemini_initialized():
            raise api_unavailable("Gemini", "Image generation requires Gemini API")

        try:
            logger.info(f"Applying Gemini image transformation: {style_prompt}")

            # Read the original image
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()
                image_b64 = base64.b64encode(image_data).decode('utf-8')

            # Build the transformation prompt
            transformation_prompt = self._build_gemini_image_prompt(style_prompt)

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
                return self._create_placeholder_styled_image(image_path, style_prompt)

            # Try to save the generated image
            try:
                styled_image_path = self._save_gemini_generated_image(
                    response, image_path, style_prompt, output_filename
                )
                return styled_image_path
            except Exception as save_error:
                logger.warning(f"Gemini image generation failed: {save_error}")
                logger.info("Creating placeholder styled image instead")
                return self._create_placeholder_styled_image(image_path, style_prompt)

        except Exception as e:
            logger.error(f"Gemini image transformation failed: {e}")
            raise transformation_failed(str(e), "gemini")

    def _transform_image_with_references(self, target_image_data: Dict[str, Any], reference_images: List[Dict[str, Any]], style_prompt: str, output_filename: str = None) -> Optional[str]:
        """Transform image using Gemini I2I with reference images (main image + references)."""
        if not self._ensure_gemini_initialized():
            raise api_unavailable("Gemini", "Multi-image transformation requires Gemini API")

        try:
            logger.info(f"Applying Gemini multi-image transformation: {style_prompt}")
            logger.info(f"Using {len(reference_images)} reference images")

            # Extract main image dimensions for aspect ratio preservation
            main_image_dimensions = self._extract_image_dimensions(target_image_data)
            logger.info(f"Main image dimensions: {main_image_dimensions['width']}x{main_image_dimensions['height']}")

            # Pre-flight request size validation
            size_info = self._estimate_request_size(target_image_data, reference_images, style_prompt)
            logger.info(f"Request size estimation: {size_info['total_size_mb']}MB, {size_info['estimated_tokens']} tokens")

            if not size_info['within_limits']:
                logger.warning(f"Request may exceed API limits - proceeding with caution")
                if size_info['total_size_mb'] >= 20.0:
                    raise image_size_exceeded(
                        size_mb=size_info['total_size_mb'],
                        max_size_mb=20.0
                    )
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
                return self._apply_nano_banana_style_fallback(target_image_data, style_prompt, output_filename)

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

            # Build multi-image prompt with main image dimensions
            transformation_prompt = self._build_multi_image_prompt(
                style_prompt, valid_references, main_image_dimensions
            )

            # Generate styled image using Gemini multi-image API
            logger.info(f"Sending multi-image transformation request to Gemini with {len(image_parts)} images...")
            logger.info(f"📋 PROMPT TO GEMINI:\n{transformation_prompt}")
            response = self._model.generate_content([*image_parts, transformation_prompt])

            if not response or not response.candidates:
                logger.warning("No response from Gemini multi-image generation")
                return None

            # Save the generated image
            original_path = target_image_data.get('file_path', 'unknown')
            styled_image_path = self._save_gemini_generated_image(
                response, original_path, style_prompt, output_filename
            )
            return styled_image_path

        except Exception as e:
            logger.error(f"Gemini multi-image transformation failed: {e}")
            raise transformation_failed(str(e), "gemini_multi_image")

    def _build_multi_image_prompt(self, style_prompt: str, reference_images: List[Dict[str, Any]], main_image_dimensions: Dict[str, int] = None) -> str:
        """Build the I2I prompt with unified prompt (no per-reference parsing needed).

        Image order in Gemini API: [main_image, ref1, ref2, ref3]
        - First image = main image to transform
        - Remaining images = reference images for style/features
        """
        # Add dimension constraint if available
        dimension_instruction = ""
        if main_image_dimensions and main_image_dimensions.get('width') and main_image_dimensions.get('height'):
            dimension_instruction = f" The output must be {main_image_dimensions['width']}x{main_image_dimensions['height']} pixels."

        ref_count = len(reference_images)

        # Simple unified prompt - no complex parsing needed
        if ref_count > 0:
            instruction_text = f"Transform the first image based on this instruction: {style_prompt}. Use the reference images provided for style and visual guidance. Keep the first image's composition and structure."
        else:
            instruction_text = f"Transform the first image: {style_prompt}. Keep the composition and structure."

        return f"""{instruction_text}

Apply the transformation naturally. Do not change the aspect ratio.{dimension_instruction}"""
    
    def _build_gemini_image_prompt(self, style_prompt: str) -> str:
        """Build the image generation prompt for Gemini."""
        return f"""Modify ONLY the requested changes: {style_prompt}.
Apply the transformation that affects ONLY the elements mentioned in the request.
Keep the background, environment, and all other elements completely unchanged.
Only modify what is explicitly requested - preserve everything else exactly as it appears in the original image.
Generate the image with minimal changes."""
    
    def _create_placeholder_styled_image(self, original_path: str, style_prompt: str) -> str:
        """Create a placeholder styled image by copying the original."""
        try:
            # Create generated images directory using centralized path management
            from core.errors import AppError, ErrorCategory

            path_manager = get_path_manager()
            generated_dir_path = path_manager.get_generated_images_path()
            if not generated_dir_path:
                raise AppError(
                    code="IMG_PATH_ERROR",
                    message="Unable to determine generated images directory path",
                    category=ErrorCategory.INTERNAL_SERVER,
                    suggestion="Check data_storage configuration"
                )

            styled_dir = Path(generated_dir_path)
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
            from core.errors import AppError, ErrorCategory
            logger.error(f"Failed to create placeholder styled image: {e}")
            raise AppError(
                code="IMG_PROCESSING_FAILED",
                message=f"Failed to create styled image: {str(e)}",
                category=ErrorCategory.INTERNAL_SERVER,
                suggestion="Check image processing configuration and file permissions"
            )

    def _save_gemini_generated_image(self, response, original_path: str, style_prompt: str, output_filename: str = None) -> str:
        """Save the Gemini generated image to data_storage/assets/images/generated."""
        try:
            # Create generated images directory using centralized path management
            from core.errors import AppError, ErrorCategory

            path_manager = get_path_manager()
            generated_dir_path = path_manager.get_generated_images_path()
            if not generated_dir_path:
                raise AppError(
                    code="IMG_PATH_ERROR",
                    message="Unable to determine generated images directory path",
                    category=ErrorCategory.INTERNAL_SERVER,
                    suggestion="Check data_storage configuration"
                )

            styled_dir = Path(generated_dir_path)
            styled_dir.mkdir(parents=True, exist_ok=True)

            # Use provided filename or generate legacy format
            if output_filename:
                styled_filename = output_filename
            else:
                # Fallback to legacy format
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
            from core.errors import transformation_failed

            candidates_count = len(response.candidates) if response.candidates else 0
            logger.error(f"No image data found in Gemini response (candidates: {candidates_count})")
            raise transformation_failed(
                reason="No image data found in Gemini response",
                model="gemini"
            )
            
        except AppError:
            raise  # Re-raise AppError as-is
        except Exception as e:
            from core.errors import AppError, ErrorCategory
            logger.error(f"Failed to save Gemini generated image: {e}")
            raise AppError(
                code="IMG_SAVE_FAILED",
                message=f"Failed to save generated image: {str(e)}",
                category=ErrorCategory.INTERNAL_SERVER,
                suggestion="Check file permissions and storage space"
            )
    
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

    def _is_non_english(self, text: str) -> bool:
        """Check if text contains non-English (e.g., Korean) characters."""
        # Check for non-ASCII characters (Korean, Chinese, Japanese, etc.)
        return any(ord(char) > 127 for char in text)

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

    def _generate_styled_filename(self, image_uid: str, model: str, operation: str = "transform") -> str:
        """
        Generate standardized filename for generated images.

        Format: {uid}_{YYYYMMDD}.png
        Example: img_003_20251002.png

        Args:
            image_uid: Image UID (e.g., img_003)
            model: Model name (unused, kept for API compatibility)
            operation: Operation type (unused, kept for API compatibility)

        Returns:
            Formatted filename with date
        """
        from datetime import datetime

        # Generate date in YYYYMMDD format
        date_str = datetime.now().strftime("%Y%m%d")

        # Build filename: uid_date.png
        filename = f"{image_uid}_{date_str}.png"

        return filename

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

    def _apply_nano_banana_style_fallback(self, target_image_data: Dict[str, Any], style_prompt: str, output_filename: str = None) -> Optional[str]:
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
                temp_image_path, style_prompt, output_filename
            )

            # Clean up temp file
            os.unlink(temp_image_path)

            return styled_image_path

        except AppError:
            raise  # Re-raise AppError as-is
        except Exception as e:
            from core.errors import transformation_failed
            logger.error(f"Fallback transformation failed: {e}")
            raise transformation_failed(
                reason=str(e),
                model="fallback"
            )

    def _build_text_to_image_prompt(self, text_prompt: str, aspect_ratio: str, reference_images: List[Dict[str, Any]] = None) -> str:
        """Build prompt for text-to-image generation with optional reference images."""
        if reference_images and len(reference_images) > 0:
            # With reference images - use their style
            return f"""Generate a high-quality image based on this description: {text_prompt}

Apply the visual style, color palette, and artistic elements from the provided reference images.

Create a detailed, visually appealing image that combines the described content with the referenced visual style.
Aspect ratio: {aspect_ratio}
Focus on quality, composition, and aesthetic appeal."""
        else:
            # Pure text-to-image
            return f"""Generate a high-quality image based on this description: {text_prompt}

Create a detailed, visually appealing image that accurately represents the described scene.
Aspect ratio: {aspect_ratio}
Focus on quality, composition, and aesthetic appeal."""

    def _generate_image_from_text(self, generation_prompt: str, reference_images: List[Dict[str, Any]], output_filename: str) -> Optional[str]:
        """Generate image using Gemini T2I with optional reference images (text + references only)."""
        if not self._ensure_gemini_initialized():
            raise api_unavailable("Gemini", "Text-to-image generation requires Gemini API")

        try:
            # Prepare content parts
            content_parts = []

            # Add reference images first if present
            for ref_img in reference_images[:3]:  # Max 3 references
                if isinstance(ref_img['data'], bytes):
                    ref_b64 = base64.b64encode(ref_img['data']).decode('utf-8')
                else:
                    ref_b64 = ref_img['data']

                content_parts.append({
                    'inline_data': {
                        'mime_type': ref_img['mime_type'],
                        'data': ref_b64
                    }
                })

            # Add text prompt
            content_parts.append(generation_prompt)

            # Generate image
            logger.info(f"Sending text-to-image request to Gemini with {len(reference_images)} references...")
            logger.info(f"📋 PROMPT TO GEMINI:\n{generation_prompt}")
            response = self._model.generate_content(content_parts)

            if not response or not response.candidates:
                logger.warning("No response from Gemini text-to-image generation")
                return None

            # Save the generated image
            generated_image_path = self._save_gemini_generated_image(
                response, "text_generated", generation_prompt, output_filename
            )
            return generated_image_path

        except Exception as e:
            logger.error(f"Gemini text-to-image generation failed: {e}")
            raise transformation_failed(str(e), "gemini_text_to_image")

