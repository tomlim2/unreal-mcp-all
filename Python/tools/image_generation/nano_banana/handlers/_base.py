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


class NanoBananaBaseHandler(BaseCommandHandler):
    """Base handler with shared Gemini logic for both I2I and T2I."""
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
    
    # Note: get_supported_commands() is implemented in subclasses (I2I and T2I handlers)

    def _build_gemini_image_part(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Gemini API image part from image data."""
        from core.resources.images import encode_image_to_base64
        return {
            'inline_data': {
                'mime_type': image_data['mime_type'],
                'data': encode_image_to_base64(image_data)
            }
        }

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
    
    # Note: validate_command(), preprocess_params(), execute_command()
    # are implemented in subclasses (I2I and T2I handlers)
    
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
            # Apply I2I transformation (with or without reference images)
            result_path = self._nano_banana_i2i(
                main_image, reference_images, prompt, output_filename
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
            generation_prompt = self._build_text_to_image_prompt(prompt, aspect_ratio)

            # Generate image
            result_path = self._nano_banana_t2i(
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

    def _nano_banana_i2i(self, target_image_data: Dict[str, Any], reference_images: List[Dict[str, Any]], style_prompt: str, output_filename: str = None) -> Optional[str]:
        """
        Nano Banana Image-to-Image transformation using Gemini.

        Handles both single image and multi-image (with references) transformations.
        """
        if not self._ensure_gemini_initialized():
            raise api_unavailable("Gemini", "Image transformation requires Gemini API")

        try:
            logger.info(f"Nano Banana I2I transformation: {style_prompt}")
            logger.info(f"Reference images: {len(reference_images)}")

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

            # Validate reference images - reject tiny/test images
            valid_references = []
            for i, ref_img in enumerate(reference_images):
                data_size = len(ref_img['data']) if isinstance(ref_img['data'], bytes) else len(ref_img['data'].encode())
                if data_size < 500:  # Reject images smaller than 500 bytes
                    logger.warning(f"Skipping reference image {i+1}: too small ({data_size} bytes)")
                    continue
                valid_references.append(ref_img)

            if valid_references:
                logger.info(f"Using {len(valid_references)} valid reference images (filtered from {len(reference_images)})")
            else:
                logger.info("No reference images - single image transformation")

            # Build image parts for Gemini API
            image_parts = []

            # Add target image (always required)
            image_parts.append(self._build_gemini_image_part(target_image_data))

            # Add reference images (up to 3 for Gemini API limit)
            for ref_img in valid_references[:3]:
                image_parts.append(self._build_gemini_image_part(ref_img))

            # Build prompt with aspect ratio information
            width = main_image_dimensions.get('width', 0)
            height = main_image_dimensions.get('height', 0)

            if width > 0 and height > 0:
                # Calculate aspect ratio
                from math import gcd
                divisor = gcd(width, height)
                aspect_w = width // divisor
                aspect_h = height // divisor
                i2i_prompt = f"{style_prompt}\n\nMaintain original aspect ratio: {aspect_w}:{aspect_h} ({width}x{height}px)"
            else:
                i2i_prompt = style_prompt

            # Generate transformed image using Gemini
            logger.info(f"Sending I2I request to Gemini with {len(image_parts)} images...")
            logger.info(f"📋 PROMPT TO GEMINI:\n{i2i_prompt}")
            response = self._model.generate_content([*image_parts, i2i_prompt])

            if not response or not response.candidates:
                logger.warning("No response from Gemini I2I generation")
                return None

            # Save the generated image
            styled_image_path = self._save_gemini_generated_image(response, output_filename)
            return styled_image_path

        except Exception as e:
            logger.error(f"Nano Banana I2I transformation failed: {e}")
            raise transformation_failed(str(e), "nano_banana_i2i")

    def _extract_image_from_gemini_response(self, response) -> bytes:
        """
        Extract image bytes from Gemini API response.

        Args:
            response: Gemini API response object

        Returns:
            bytes: Raw image data

        Raises:
            transformation_failed: If no image data found in response
        """
        from core.errors import transformation_failed

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
                                logger.info(f"Extracted raw bytes: {len(raw_data)} bytes")
                                return raw_data
                            else:
                                # Fallback to base64 decode if needed
                                image_data = base64.b64decode(raw_data)
                                logger.info(f"Extracted base64 decoded: {len(image_data)} bytes")
                                return image_data

        # No image data found in Gemini response
        candidates_count = len(response.candidates) if response.candidates else 0
        logger.error(f"No image data found in Gemini response (candidates: {candidates_count})")
        raise transformation_failed(
            reason="No image data found in Gemini response",
            model="gemini"
        )

    def _save_gemini_generated_image(self, response, output_filename: str = None) -> str:
        """
        Save Gemini generated image using centralized PathManager.

        Args:
            response: Gemini API response
            original_path: Original image path (for logging)
            style_prompt: Style prompt used (for logging)
            output_filename: Optional output filename

        Returns:
            str: Absolute path to saved image
        """
        # Extract image data from Gemini response (Gemini-specific)
        image_data = self._extract_image_from_gemini_response(response)

        # Determine filename
        filename = output_filename or f"NB_{int(time.time())}.png"

        # Save via PathManager (centralized storage)
        path_manager = get_path_manager()
        return path_manager.save_generated_image(
            image_data=image_data,
            filename=filename,
            source="nano_banana"
        )
    
    def _estimate_request_size(self, image_data: Dict[str, Any], reference_images: List[Dict[str, Any]], prompt: str) -> Dict[str, Any]:
        """Estimate API request size and token count for validation."""
        total_size_mb = 0.0
        estimated_tokens = 0

        try:
            from core.resources.images import calculate_image_size_mb

            # Calculate image sizes
            if image_data and 'data' in image_data:
                total_size_mb += calculate_image_size_mb(image_data['data'])

            # Calculate reference image sizes
            for ref_img in reference_images:
                if 'data' in ref_img:
                    total_size_mb += calculate_image_size_mb(ref_img['data'])

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

    def _build_text_to_image_prompt(self, text_prompt: str, aspect_ratio: str) -> str:
        """Build prompt for text-to-image generation with optional reference images."""
        return f"{text_prompt}\n\nAspect ratio: {aspect_ratio}"

    def _nano_banana_t2i(self, generation_prompt: str, reference_images: List[Dict[str, Any]], output_filename: str) -> Optional[str]:
        """
        Nano Banana Text-to-Image generation using Gemini.

        Generates image from text prompt with optional reference images.
        """
        if not self._ensure_gemini_initialized():
            raise api_unavailable("Gemini", "Text-to-image generation requires Gemini API")

        try:
            # Prepare content parts
            content_parts = []

            # Add reference images first if present
            for ref_img in reference_images[:3]:  # Max 3 references
                content_parts.append(self._build_gemini_image_part(ref_img))

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
            generated_image_path = self._save_gemini_generated_image(response, output_filename)
            return generated_image_path

        except Exception as e:
            logger.error(f"Gemini text-to-image generation failed: {e}")
            raise transformation_failed(str(e), "gemini_text_to_image")

