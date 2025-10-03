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
from ...session_management.utils.path_manager import get_path_manager
from ...pricing_manager import get_pricing_manager
from ...video_schema_utils import (
    build_video_transform_response,
    generate_request_id,
    extract_parent_filename,
    generate_video_filename
)
from ...uid_manager import generate_image_uid, generate_video_uid, add_uid_mapping
from core.errors import (
    video_not_found, video_generation_failed, video_api_unavailable,
    invalid_video_duration, AppError, ErrorCategory
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
    logger.warning("google.generativeai not available - Veo-3 features disabled")

try:
    from google import genai as google_genai
    from google.genai import types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    types = None
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
            "cost": 3.2,  # $0.40 per second * 8 seconds (2025 updated pricing)
            "estimated_cost": "$3.200",
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
                raise video_api_unavailable("Veo-3", "Google AI packages not installed")
            else:
                raise video_api_unavailable("Veo-3", "GOOGLE_API_KEY not configured")

        if command_type == "generate_video_from_image":
            # Required parameters
            if not params.get("prompt"):
                errors.append("prompt is required")

            # Support both target_image_uid (new) and image_url (legacy)
            if params.get("target_image_uid"):
                params["image_url"] = params["target_image_uid"]
                logger.info(f"Using target_image_uid as image_url: {params['image_url']}")

            if not params.get("image_url"):
                # 세션에서 최신 이미지 자동 할당 시도
                session_id = params.get("session_id")
                if session_id:
                    try:
                        from ...session_management import get_session_manager
                        session_manager = get_session_manager()
                        session_context = session_manager.get_session(session_id)
                        if session_context:
                            latest_uid = session_context.get_latest_image_uid()
                            # Double-check: ensure it's an image UID, not a video UID
                            if latest_uid and latest_uid.startswith('img_'):
                                params["image_url"] = latest_uid
                                logger.info(f"Auto-assigned latest image UID for video generation: {latest_uid}")
                            else:
                                errors.append("비디오 생성에는 이미지가 필요합니다. 먼저 스크린샷을 찍어주세요.")
                        else:
                            errors.append("비디오 생성에는 이미지가 필요합니다. 먼저 스크린샷을 찍어주세요.")
                    except Exception as e:
                        logger.error(f"Failed to get session context: {e}")
                        errors.append("비디오 생성에는 이미지가 필요합니다. 먼저 스크린샷을 찍어주세요.")
                else:
                    errors.append("비디오 생성에는 이미지가 필요합니다. 먼저 스크린샷을 찍어주세요.")

            # Validate image_url format if it exists (either provided or auto-assigned)
            if params.get("image_url"):
                image_url = params["image_url"]
                # Validate UID format: must be img_XXX where XXX is digits
                if not (image_url.startswith('img_') and image_url[4:].isdigit()):
                    errors.append("image_url must be a valid UID format (e.g., 'img_074'). Filenames not supported.")

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
            from core.errors import validation_failed
            raise validation_failed(
                message=f"Unsupported command: {command_type}",
                invalid_params={"type": command_type},
                suggestion="Use 'generate_video_from_image' for video generation"
            )

    def _generate_video_from_latest_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate video from latest screenshot automatically."""
        start_time = time.time()
        request_id = generate_request_id()

        prompt = params["prompt"]
        aspect_ratio = params.get("aspect_ratio", "16:9")
        resolution = params.get("resolution", "720p")
        negative_prompt = params.get("negative_prompt")

        logger.info(f"Generate Video: image -> {prompt} [req_id: {request_id}]")

        try:
            # image_url is now REQUIRED - no fallback to latest screenshot
            image_url = params.get("image_url")
            if not image_url:
                raise AppError(
                    code="VIDEO_IMAGE_REQUIRED",
                    message="image_url parameter is required for video generation",
                    category=ErrorCategory.USER_INPUT,
                    suggestion="Please specify an image UID (e.g., 'img_074')",
                    request_id=request_id
                )

            # Resolve the specified image (supports UID only)
            from ...uid_manager import get_uid_mapping
            source_image = self._resolve_image_path(image_url)
            if not source_image:
                raise video_not_found(image_url, request_id=request_id)

            latest_screenshot = Path(source_image)
            logger.info(f"Using specified image: {image_url} -> {latest_screenshot.name}")

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

                # Extract session_id from params if available
                session_id = params.get('session_id')

                # Parse resolution to get dimensions
                if resolution == "720p":
                    video_width, video_height = (1280, 720) if aspect_ratio == "16:9" else (720, 1280)
                else:  # 1080p
                    video_width, video_height = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)

                # Add mappings for both screenshot and video
                # 1. Original screenshot
                add_uid_mapping(
                    parent_uid,
                    'image',
                    Path(latest_screenshot).name,
                    session_id=session_id,
                    metadata={
                        'width': screenshot_metadata.get('width', 0),
                        'height': screenshot_metadata.get('height', 0),
                        'file_path': str(latest_screenshot),
                        'video_source': True
                    }
                )

                # 2. Generated video
                add_uid_mapping(
                    video_uid,
                    'video',
                    filename,
                    parent_uid=parent_uid,
                    session_id=session_id,
                    metadata={
                        'width': video_width,
                        'height': video_height,
                        'file_path': video_path,
                        'duration_seconds': video_metadata['duration_seconds'],
                        'prompt': prompt,
                        'aspect_ratio': aspect_ratio,
                        'resolution': resolution,
                        'cost': video_metadata['cost']
                    }
                )

                # Build standardized video response
                return build_video_transform_response(
                    video_uid=video_uid,
                    parent_uid=parent_uid,
                    filename=filename,
                    video_path=video_path,
                    original_width=screenshot_metadata.get('width', 0),
                    original_height=screenshot_metadata.get('height', 0),
                    processed_width=video_width,
                    processed_height=video_height,
                    duration_seconds=video_metadata['duration_seconds'],
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    cost=video_metadata['cost'],
                    request_id=request_id,
                    start_time=start_time
                )
            else:
                raise video_generation_failed(
                    reason="No video data returned from Veo-3 API",
                    model="veo-3",
                    request_id=request_id
                )

        except AppError:
            raise
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise video_generation_failed(
                reason=str(e),
                model="veo-3",
                request_id=request_id
            )

    def _generate_video_with_veo3(self, image_path: str, prompt: str, aspect_ratio: str, resolution: str, negative_prompt: Optional[str]) -> Optional[str]:
        """Generate video using Veo-3 API."""
        if not self._ensure_gemini_initialized():
            raise video_api_unavailable("Veo-3", "API not initialized")

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

            # Build config - only if types is available
            if not types:
                raise video_api_unavailable("Veo-3", "Google GenAI types not available")

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
                elapsed = time.time() - start_time
                if elapsed > max_wait_time:
                    raise AppError(
                        code="VIDEO_GENERATION_TIMEOUT",
                        message=f"Video generation timeout after {elapsed:.1f}s",
                        category=ErrorCategory.EXTERNAL_API,
                        suggestion="Try a simpler prompt or shorter duration"
                    )

                time.sleep(20)  # Check every 20 seconds
                operation = self._client.operations.get(operation)
                logger.info(f"Video generation in progress... ({elapsed:.1f}s elapsed)")

            # Extract and save video
            if operation.response and operation.response.generated_videos:
                generated_video = operation.response.generated_videos[0]
                video_path = self._save_video_to_project(generated_video, image_path, prompt)
                logger.info(f"Video generated successfully: {video_path}")
                return video_path
            else:
                raise video_generation_failed(
                    reason="No video data in Veo-3 response",
                    model="veo-3"
                )

        except AppError:
            raise
        except Exception as e:
            logger.error(f"Veo-3 video generation failed: {e}")
            raise video_generation_failed(
                reason=str(e),
                model="veo-3"
            )

    def _save_video_to_project(self, generated_video, image_path: str, prompt: str) -> str:
        """Save the Veo-3 generated video to the project directory."""
        try:
            # Create video directory using centralized path management
            path_manager = get_path_manager()
            project_path = path_manager.get_unreal_project_path()
            if not project_path:
                raise AppError(
                    code="VIDEO_SAVE_FAILED",
                    message="Unable to determine Unreal project path",
                    category=ErrorCategory.INTERNAL_SERVER,
                    suggestion="Check UNREAL_PROJECT_PATH environment variable"
                )

            video_dir = Path(project_path) / "Saved" / "Videos" / "generated"
            video_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename: [parent_filename]_VEO3_[timestamp]
            parent_filename = extract_parent_filename(image_path)
            timestamp = int(time.time())

            video_filename = generate_video_filename(parent_filename, timestamp)
            video_path = video_dir / video_filename

            # Download and save video
            self._client.files.download(file=generated_video.video)
            generated_video.video.save(str(video_path))

            logger.info(f"Veo-3 generated video saved: {video_path}")
            return str(video_path)

        except AppError:
            raise
        except Exception as e:
            logger.error(f"Failed to save Veo-3 generated video: {e}")
            raise AppError(
                code="VIDEO_SAVE_FAILED",
                message=f"Failed to save generated video: {str(e)}",
                category=ErrorCategory.INTERNAL_SERVER
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

    def _resolve_image_path(self, image_path_param: str) -> Optional[str]:
        """Resolve image path - handles UIDs, full paths, and filenames."""
        from ...uid_manager import get_uid_mapping

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

        # If it's already a full path and exists, use it
        if os.path.isabs(image_path_param) and os.path.exists(image_path_param):
            return image_path_param

        # For non-UID inputs, return None (no fallback search)
        logger.error(f"Image path not supported: {image_path_param}. Use UID (img_XXX) or full path only.")
        return None

