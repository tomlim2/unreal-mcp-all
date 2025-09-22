"""
Video generation handler using Google Veo-3.

Handles Google Gemini Veo-3 video generation operations.
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
from ...uid_manager import generate_image_uid, generate_video_uid

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
    logger.warning("google.generativeai not available - Veo-3 features disabled")

try:
    from google import genai as google_genai
    from google.genai import types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    logger.warning("google.genai not available - will use fallback")


class VideoGenerationHandler(BaseCommandHandler):
    """Handler for Veo-3 video generation commands.

    Supported Commands:
    - generate_video_from_image: Generate video from latest screenshot + prompt

    Input Constraints:
    - prompt: Required string describing the desired video animation
    - aspect_ratio: Optional string ("16:9" or "9:16"), defaults to "16:9"
    - resolution: Optional string ("720p" or "1080p"), defaults to "720p"
    - negative_prompt: Optional string describing what to avoid

    Output:
    - Returns video UID and generation details
    """

    def __init__(self):
        super().__init__()
        self._client = None
        self._client_initialized = False

    def _ensure_gemini_initialized(self):
        """Initialize Gemini API lazily when needed."""
        if self._client_initialized:
            return self._client is not None

        self._client_initialized = True

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set - Veo-3 features will not work")
            self._client = None
            return False

        # Try different import methods
        try:
            if GOOGLE_GENAI_AVAILABLE:
                # Use google.genai client for Veo-3
                self._client = google_genai.Client(api_key=api_key)
                logger.info("Veo-3 (google.genai) initialized successfully")
                return True
            elif GEMINI_AVAILABLE:
                # Fallback to google.generativeai
                genai.configure(api_key=api_key)
                self._client = genai
                logger.info("Veo-3 (google.generativeai) initialized successfully")
                return True
            else:
                logger.warning("No Google AI packages available")
                self._client = None
                return False
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self._client = None
            return False

    def get_supported_commands(self) -> List[str]:
        return ["generate_video_from_image"]

    def _extract_video_metadata(self, video_path: str, prompt: str) -> Dict[str, Any]:
        """Extract video metadata and calculate costs."""
        metadata = {
            "duration_seconds": 8,  # Veo-3 always generates 8-second videos
            "file_size_mb": 0.0,
            "cost": 6.0,  # $0.75 per second * 8 seconds
            "estimated_cost": "$6.000",
            "prompt": prompt,
            "has_audio": True,
            "watermarked": True
        }

        try:
            # Get file size
            file_path = Path(video_path)
            if file_path.exists():
                file_size_bytes = file_path.stat().st_size
                metadata["file_size_mb"] = round(file_size_bytes / (1024 * 1024), 1)

        except Exception as e:
            logger.warning(f"Failed to extract video metadata from {video_path}: {e}")

        return metadata

    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate Veo-3 video generation commands with parameter checks."""
        errors = []

        # Check if Gemini is available (lazy initialization)
        if not self._ensure_gemini_initialized():
            if not GEMINI_AVAILABLE and not GOOGLE_GENAI_AVAILABLE:
                errors.append("Google AI packages not available")
            else:
                errors.append("Gemini API not properly configured (check GOOGLE_API_KEY)")

        if command_type == "generate_video_from_image":
            # Required parameters
            if not params.get("prompt"):
                errors.append("prompt is required")

            # Validate optional parameters
            if "aspect_ratio" in params:
                aspect_ratio = params["aspect_ratio"]
                if aspect_ratio not in ["16:9", "9:16"]:
                    errors.append("aspect_ratio must be '16:9' or '9:16'")

            if "resolution" in params:
                resolution = params["resolution"]
                if resolution not in ["720p", "1080p"]:
                    errors.append("resolution must be '720p' or '1080p'")

        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )

    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values and normalize parameters."""
        processed = params.copy()

        # Apply defaults
        processed.setdefault("aspect_ratio", "16:9")
        processed.setdefault("resolution", "720p")

        return processed

    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute Veo-3 video generation commands."""
        logger.info(f"Video Generation Handler: Executing {command_type} with params: {params}")

        if command_type == "generate_video_from_image":
            return self._generate_video_from_latest_screenshot(params)
        else:
            raise Exception(f"Unsupported command: {command_type}")

    def _generate_video_from_latest_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate video from latest screenshot automatically."""
        start_time = time.time()
        request_id = generate_request_id()

        prompt = params["prompt"]
        aspect_ratio = params["aspect_ratio"]
        resolution = params["resolution"]
        negative_prompt = params.get("negative_prompt")

        logger.info(f"Generate Video: latest screenshot -> {prompt} [req_id: {request_id}]")

        try:
            # Find latest screenshot automatically
            latest_screenshot = self._find_newest_screenshot()
            if not latest_screenshot:
                return build_error_response(
                    "No screenshot found in WindowsEditor directory",
                    "screenshot_not_found",
                    request_id,
                    start_time
                )

            logger.info(f"Using latest screenshot: {latest_screenshot.name}")

            # Generate video using Veo-3
            video_path = self._generate_video_with_veo3(
                str(latest_screenshot), prompt, aspect_ratio, resolution, negative_prompt
            )

            if video_path:
                filename = Path(video_path).name

                # Extract metadata for both image and video
                screenshot_metadata = self._extract_image_metadata_if_available(str(latest_screenshot))
                video_metadata = self._extract_video_metadata(video_path, prompt)

                # Generate UIDs
                parent_uid = generate_image_uid()  # UID for source screenshot
                video_uid = generate_video_uid()  # UID for video result

                # Build video response
                return self._build_video_response(
                    video_uid=video_uid,
                    parent_uid=parent_uid,
                    filename=filename,
                    video_path=video_path,
                    original_width=screenshot_metadata.get('width', 0),
                    original_height=screenshot_metadata.get('height', 0),
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    duration_seconds=video_metadata['duration_seconds'],
                    cost=video_metadata['cost'],
                    request_id=request_id,
                    start_time=start_time
                )
            else:
                return build_error_response(
                    "Failed to generate video with Veo-3",
                    "video_generation_failed",
                    request_id,
                    start_time
                )

        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return build_error_response(
                f"Video generation failed: {str(e)}",
                "execution_error",
                request_id,
                start_time
            )

    def _generate_video_with_veo3(self, image_path: str, prompt: str, aspect_ratio: str, resolution: str, negative_prompt: Optional[str]) -> Optional[str]:
        """Generate video using Veo-3 API."""
        if not self._ensure_gemini_initialized():
            raise Exception("Veo-3 video generation not available")

        try:
            logger.info(f"Generating Veo-3 video: {prompt} ({aspect_ratio}, {resolution})")

            # Read the image
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()

            # Create image part for Veo-3 API using correct format
            image_part = {
                'imageBytes': image_data,
                'mimeType': 'image/png'
            }

            # Build config
            config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                resolution=resolution
            )

            if negative_prompt:
                config.negative_prompt = negative_prompt

            # Start video generation using correct API format
            logger.info("Starting Veo-3 video generation operation...")

            # Use the correct API call structure for image-to-video
            operation = self._client.models.generate_videos(
                model="veo-3.0-generate-001",
                prompt=prompt,
                image=image_part,
                config=config
            )

            # Poll for completion
            logger.info("Polling for video generation completion...")
            max_wait_time = 360  # 6 minutes max
            start_time = time.time()

            while not operation.done:
                if time.time() - start_time > max_wait_time:
                    raise Exception("Video generation timeout (6 minutes)")

                time.sleep(20)  # Check every 20 seconds
                operation = self._client.operations.get(operation)
                logger.info(f"Video generation in progress... ({time.time() - start_time:.1f}s elapsed)")

            # Extract and save video
            if operation.response and operation.response.generated_videos:
                generated_video = operation.response.generated_videos[0]
                video_path = self._save_video_to_project(generated_video, prompt)
                logger.info(f"Video generated successfully: {video_path}")
                return video_path
            else:
                logger.error("No video data in Veo-3 response")
                return None

        except Exception as e:
            logger.error(f"Veo-3 video generation failed: {e}")
            raise Exception(f"Video generation failed: {str(e)}")

    def _save_video_to_project(self, generated_video, prompt: str) -> str:
        """Save the Veo-3 generated video to the project directory."""
        try:
            # Create video directory
            project_path = os.getenv('UNREAL_PROJECT_PATH')
            if not project_path:
                raise Exception("UNREAL_PROJECT_PATH not set")

            video_dir = Path(project_path) / "Saved" / "Videos" / "generated"
            video_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename: [prompt_keywords]_VEO_[timestamp]
            prompt_keywords = self._extract_prompt_keywords(prompt)
            timestamp = int(time.time())

            video_filename = f"{prompt_keywords}_VEO_{timestamp}.mp4"
            video_path = video_dir / video_filename

            # Download and save video
            self._client.files.download(file=generated_video.video)
            generated_video.video.save(str(video_path))

            logger.info(f"Veo-3 generated video saved: {video_path}")
            return str(video_path)

        except Exception as e:
            logger.error(f"Failed to save Veo-3 generated video: {e}")
            raise Exception(f"Failed to save generated video: {str(e)}")

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

    def _extract_image_metadata_if_available(self, image_path: str) -> Dict[str, Any]:
        """Extract image metadata if PIL is available."""
        metadata = {"width": 0, "height": 0}

        if PIL_AVAILABLE:
            try:
                with Image.open(image_path) as img:
                    metadata["width"] = img.width
                    metadata["height"] = img.height
            except Exception as e:
                logger.warning(f"Failed to extract image metadata: {e}")

        return metadata

    def _extract_prompt_keywords(self, prompt: str) -> str:
        """Extract keywords from prompt for filename."""
        import re
        # Remove special characters and take first few words
        clean_prompt = re.sub(r'[^a-zA-Z0-9\s]', '', prompt)
        words = clean_prompt.split()[:4]  # Take first 4 words
        return '_'.join(words).lower()


    def _build_video_response(self, video_uid: str, parent_uid: str, filename: str,
                             video_path: str, original_width: int, original_height: int,
                             prompt: str, aspect_ratio: str, resolution: str,
                             duration_seconds: int, cost: float, request_id: str,
                             start_time: float) -> Dict[str, Any]:
        """Build standardized video response."""
        processing_time = time.time() - start_time

        # Parse resolution to get dimensions
        if resolution == "720p":
            video_width, video_height = (1280, 720) if aspect_ratio == "16:9" else (720, 1280)
        else:  # 1080p
            video_width, video_height = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)

        return {
            "video_uid": video_uid,
            "parent_uid": parent_uid,
            "filename": filename,
            "video_path": video_path,
            "original_width": original_width,
            "original_height": original_height,
            "processed_width": video_width,
            "processed_height": video_height,
            "duration_seconds": duration_seconds,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "cost": cost,
            "request_id": request_id,
            "processing_time_seconds": round(processing_time, 2),
            "origin": "latest_screenshot_to_video",
            "has_audio": True,
            "watermarked": True,
            "model": "veo-3.0-generate-001"
        }