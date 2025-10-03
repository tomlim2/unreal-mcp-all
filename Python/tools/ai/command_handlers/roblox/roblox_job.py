"""
Async Roblox download job worker for background processing of 3D avatar downloads.

Provides non-blocking download experience with progress tracking and status updates.
Integrates with UID system and session management for organized storage.
"""

import asyncio
import logging
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum

from core.errors import RobloxError, RobloxErrorCodes
from .roblox_errors import RobloxErrorHandler, log_roblox_error
from .scripts.roblox_obj_downloader import RobloxAvatar3DDownloader
from ...uid_manager import get_uid_manager, generate_object_uid
from ...session_management.utils.path_manager import get_path_manager

logger = logging.getLogger("UnrealMCP.Roblox.Job")


class JobStatus(Enum):
    """Status enum for download jobs."""
    QUEUED = "queued"
    RESOLVING_USER = "resolving_user"
    FETCHING_METADATA = "fetching_metadata"
    DOWNLOADING_MODEL = "downloading_model"
    DOWNLOADING_TEXTURES = "downloading_textures"
    PROCESSING_FILES = "processing_files"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobProgress:
    """Progress information for download jobs."""
    current_step: str
    completed_files: int
    total_files: int
    percentage: float
    estimated_remaining_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JobResult:
    """Final result of download job."""
    success: bool
    uid: str
    username: Optional[str] = None
    user_id: Optional[int] = None
    file_paths: Optional[Dict[str, Any]] = None
    download_stats: Optional[Dict[str, Any]] = None
    error: Optional[RobloxError] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.error:
            result["error"] = self.error.to_dict()
        return result


class RobloxDownloadJob:
    """
    Async job for downloading Roblox 3D avatars in the background.

    Features:
    - Progressive status updates with detailed progress tracking
    - Automatic UID generation and file organization
    - Session-based storage with PathManager integration
    - Comprehensive error handling with user-friendly messages
    - Cancellation support for long-running downloads
    """

    def __init__(self, uid: str, user_input: str, session_id: Optional[str] = None,
                 progress_callback: Optional[Callable] = None):
        """
        Initialize download job.

        Args:
            uid: Generated object UID for tracking
            user_input: User ID or username to download
            session_id: Optional session ID for organization
            progress_callback: Optional callback for progress updates
        """
        self.uid = uid
        self.user_input = user_input.strip()
        self.session_id = session_id
        self.progress_callback = progress_callback

        # Job state
        self.status = JobStatus.QUEUED
        self.progress = JobProgress("Initializing", 0, 0, 0.0)
        self.result: Optional[JobResult] = None
        self.error: Optional[RobloxError] = None
        self.cancelled = False

        # Timing
        self.start_time = time.time()
        self.end_time: Optional[float] = None

        # Storage paths
        self.path_manager = get_path_manager()
        self.uid_manager = get_uid_manager()

        # Download components
        self.downloader: Optional[RobloxAvatar3DDownloader] = None
        self.download_folder: Optional[Path] = None

        logger.info(f"Roblox download job created: {uid} for user '{user_input}' (session: {session_id})")

    async def execute(self) -> JobResult:
        """
        Execute the download job asynchronously.

        Returns:
            JobResult with success/failure information
        """
        try:
            logger.info(f"Starting Roblox download job: {self.uid}")

            # Step 1: Setup storage paths
            await self._setup_storage()

            # Step 2: Resolve user ID/username
            user_id = await self._resolve_user()

            # Step 3: Get 3D avatar metadata
            metadata = await self._fetch_avatar_metadata(user_id)

            # Step 4: Download model files (OBJ/MTL)
            model_files = await self._download_model_files(user_id, metadata)

            # Step 5: Download textures
            texture_files = await self._download_textures(user_id, metadata)

            # Step 6: Process and organize files
            final_result = await self._finalize_download(user_id, metadata, model_files, texture_files)

            # Mark as completed
            self.status = JobStatus.COMPLETED
            self.end_time = time.time()
            self.result = final_result

            self._update_progress("Download completed", 100, 100, 100.0)
            self._add_uid_mapping(final_result)

            logger.info(f"Roblox download job completed: {self.uid} in {self.end_time - self.start_time:.1f}s")
            return final_result

        except Exception as exc:
            logger.exception(f"Roblox download job failed: {self.uid}")
            return await self._handle_job_failure(exc)

    async def cancel(self) -> bool:
        """
        Cancel the download job.

        Returns:
            True if cancellation was successful
        """
        self.cancelled = True
        self.status = JobStatus.CANCELLED
        self.end_time = time.time()

        # Cleanup partial downloads
        if self.download_folder and self.download_folder.exists():
            try:
                import shutil
                shutil.rmtree(self.download_folder)
                logger.info(f"Cleaned up partial download for cancelled job: {self.uid}")
            except Exception as e:
                logger.warning(f"Failed to cleanup cancelled job {self.uid}: {e}")

        self.error = RobloxError(
            code=RobloxErrorCodes.JOB_CANCELLED,
            message="Download was cancelled by user",
            details={"uid": self.uid, "cancelled_at": datetime.now().isoformat()}
        )

        return True

    def get_status(self) -> Dict[str, Any]:
        """Get current job status for polling."""
        status_data = {
            "uid": self.uid,
            "status": self.status.value,
            "progress": self.progress.to_dict(),
            "start_time": self.start_time,
            "elapsed_seconds": time.time() - self.start_time
        }

        if self.end_time:
            status_data["end_time"] = self.end_time
            status_data["total_duration_seconds"] = self.end_time - self.start_time

        if self.result:
            status_data["result"] = self.result.to_dict()

        if self.error:
            status_data["error"] = self.error.to_dict()

        return status_data

    async def _setup_storage(self):
        """Setup storage paths for the download."""
        try:
            # Use new PathManager method for clean object_3d/[uid]/ structure
            uid_path = self.path_manager.get_3d_object_uid_path(self.uid, self.session_id)
            self.download_folder = Path(uid_path)
            self.download_folder.mkdir(parents=True, exist_ok=True)

            logger.debug(f"Setup storage for {self.uid}: {self.download_folder}")

        except Exception as e:
            raise storage_error("storage setup", str(self.download_folder))

    async def _resolve_user(self) -> int:
        """Resolve user input to user ID."""
        self.status = JobStatus.RESOLVING_USER
        self._update_progress("Resolving user identity", 0, 1, 10.0)

        if self._check_cancelled():
            from core.errors import AppError, ErrorCategory
            raise AppError(
                code="JOB_CANCELLED",
                message="Job cancelled by user",
                category=ErrorCategory.USER_INPUT
            )

        try:
            # Create downloader instance
            self.downloader = RobloxAvatar3DDownloader(str(self.download_folder))

            # Resolve user input (can be username or user ID)
            user_id = self.downloader.resolve_user_input(self.user_input)

            if user_id is None:
                raise user_not_found(self.user_input)

            logger.info(f"Resolved user '{self.user_input}' to ID: {user_id}")
            return user_id

        except Exception as e:
            if isinstance(e, RobloxError):
                raise e
            else:
                raise RobloxErrorHandler.from_exception(e, "user resolution")

    async def _fetch_avatar_metadata(self, user_id: int) -> Dict[str, Any]:
        """Fetch 3D avatar metadata."""
        self.status = JobStatus.FETCHING_METADATA
        self._update_progress("Getting 3D avatar metadata", 0, 1, 25.0)

        if self._check_cancelled():
            from core.errors import AppError, ErrorCategory
            raise AppError(
                code="JOB_CANCELLED",
                message="Job cancelled by user",
                category=ErrorCategory.USER_INPUT
            )

        try:
            # Use asyncio to make blocking call non-blocking
            metadata = await asyncio.get_event_loop().run_in_executor(
                None, self.downloader.get_avatar_3d_metadata, user_id
            )

            if metadata is None:
                raise avatar_3d_unavailable(user_id)

            logger.info(f"Fetched 3D metadata for user {user_id}")
            return metadata

        except Exception as e:
            if isinstance(e, RobloxError):
                raise e
            else:
                raise RobloxErrorHandler.from_exception(e, "metadata fetch")

    async def _download_model_files(self, user_id: int, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Download OBJ and MTL model files."""
        self.status = JobStatus.DOWNLOADING_MODEL
        self._update_progress("Downloading 3D model files", 0, 2, 50.0)

        if self._check_cancelled():
            from core.errors import AppError, ErrorCategory
            raise AppError(
                code="JOB_CANCELLED",
                message="Job cancelled by user",
                category=ErrorCategory.USER_INPUT
            )

        try:
            model_files = {}

            # Download OBJ
            obj_hash = metadata.get("obj")
            if obj_hash:
                obj_path = self.download_folder / "avatar.obj"
                success = await asyncio.get_event_loop().run_in_executor(
                    None, self.downloader.download_file_from_hash,
                    obj_hash, obj_path, "OBJ Model"
                )
                if success:
                    model_files["obj"] = str(obj_path)
                    self._update_progress("Downloaded OBJ model", 1, 2, 60.0)

            # Download MTL
            mtl_hash = metadata.get("mtl")
            if mtl_hash:
                mtl_path = self.download_folder / "avatar.mtl"
                success = await asyncio.get_event_loop().run_in_executor(
                    None, self.downloader.download_file_from_hash,
                    mtl_hash, mtl_path, "MTL Material"
                )
                if success:
                    model_files["mtl"] = str(mtl_path)
                    self._update_progress("Downloaded MTL material", 2, 2, 70.0)

            if not model_files:
                raise download_failed("model files", "No OBJ or MTL files available")

            return model_files

        except Exception as e:
            if isinstance(e, RobloxError):
                raise e
            else:
                raise RobloxErrorHandler.from_exception(e, "model download")

    async def _download_textures(self, user_id: int, metadata: Dict[str, Any]) -> List[str]:
        """Download texture files with progress tracking."""
        self.status = JobStatus.DOWNLOADING_TEXTURES

        textures = metadata.get("textures", [])
        if not textures:
            self._update_progress("No textures to download", 0, 0, 85.0)
            return []

        self._update_progress(f"Downloading {len(textures)} textures", 0, len(textures), 75.0)

        if self._check_cancelled():
            from core.errors import AppError, ErrorCategory
            raise AppError(
                code="JOB_CANCELLED",
                message="Job cancelled by user",
                category=ErrorCategory.USER_INPUT
            )

        try:
            texture_files = []
            textures_folder = self.download_folder / "textures"
            textures_folder.mkdir(exist_ok=True)

            for i, texture_hash in enumerate(textures):
                if self._check_cancelled():
                    break

                texture_path = textures_folder / f"texture_{i+1:03d}.png"

                success = await asyncio.get_event_loop().run_in_executor(
                    None, self.downloader.download_file_from_hash,
                    texture_hash, texture_path, f"Texture {i+1}"
                )

                if success:
                    texture_files.append(str(texture_path))

                # Update progress
                progress_percent = 75.0 + (10.0 * (i + 1) / len(textures))
                self._update_progress(f"Downloaded texture {i+1}/{len(textures)}", i+1, len(textures), progress_percent)

                # Small delay to prevent overwhelming the API
                await asyncio.sleep(0.1)

            logger.info(f"Downloaded {len(texture_files)}/{len(textures)} textures for user {user_id}")
            return texture_files

        except Exception as e:
            if isinstance(e, RobloxError):
                raise e
            else:
                raise RobloxErrorHandler.from_exception(e, "texture download")

    async def _finalize_download(self, user_id: int, metadata: Dict[str, Any],
                               model_files: Dict[str, str], texture_files: List[str]) -> JobResult:
        """Process and finalize the download."""
        self.status = JobStatus.PROCESSING_FILES
        self._update_progress("Processing downloaded files", 0, 1, 90.0)

        try:
            # Get user info for metadata
            user_info = await asyncio.get_event_loop().run_in_executor(
                None, self.downloader.get_user_info, user_id
            )

            username = user_info.get("name") if user_info else f"user_{user_id}"

            # Get extended info and analyze OBJ structure for avatar_type detection
            extended_info = await asyncio.get_event_loop().run_in_executor(
                None, self.downloader.get_extended_avatar_info, user_id
            )

            # Analyze OBJ structure if file exists
            obj_file = self.download_folder / "avatar.obj"
            if obj_file.exists():
                try:
                    obj_structure = await asyncio.get_event_loop().run_in_executor(
                        None, self.downloader.analyze_obj_structure, obj_file
                    )
                    if extended_info is not None:
                        extended_info["obj_structure"] = obj_structure
                except Exception as e:
                    logger.warning(f"Failed to analyze OBJ structure: {e}")
                    if extended_info is not None:
                        extended_info["obj_structure_error"] = str(e)

            # Generate metadata and documentation
            await asyncio.get_event_loop().run_in_executor(
                None, self.downloader.save_metadata,
                user_info or {"id": user_id, "name": username},
                metadata, self.download_folder, extended_info
            )

            # Prepare file paths
            file_paths = {
                "folder": str(self.download_folder),
                "metadata": str(self.download_folder / "metadata.json"),
                "readme": str(self.download_folder / "README.md")
            }
            file_paths.update(model_files)

            if texture_files:
                file_paths["textures"] = texture_files
                file_paths["textures_folder"] = str(self.download_folder / "textures")

            # Generate download stats
            download_stats = {
                "total_files": len(model_files) + len(texture_files) + 2,  # +2 for metadata and readme
                "success_count": len(model_files) + len(texture_files) + 2,
                "model_files": len(model_files),
                "texture_files": len(texture_files),
                "avatar_type": "Unknown",  # Could be extracted from metadata
                "download_duration_seconds": time.time() - self.start_time
            }

            return JobResult(
                success=True,
                uid=self.uid,
                username=username,
                user_id=user_id,
                file_paths=file_paths,
                download_stats=download_stats
            )

        except Exception as e:
            raise RobloxErrorHandler.from_exception(e, "file processing")

    async def _handle_job_failure(self, exc: Exception) -> JobResult:
        """Handle job failure and cleanup."""
        self.status = JobStatus.FAILED
        self.end_time = time.time()

        if isinstance(exc, RobloxError):
            self.error = exc
        else:
            self.error = RobloxErrorHandler.from_exception(exc, "download job")

        log_roblox_error(self.error, {
            "uid": self.uid,
            "user_input": self.user_input,
            "session_id": self.session_id,
            "duration_seconds": self.end_time - self.start_time
        })

        # Cleanup partial downloads
        if self.download_folder and self.download_folder.exists():
            try:
                import shutil
                shutil.rmtree(self.download_folder)
                logger.info(f"Cleaned up partial download for failed job: {self.uid}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup failed job {self.uid}: {cleanup_error}")

        self.result = JobResult(
            success=False,
            uid=self.uid,
            error=self.error
        )

        return self.result

    def _update_progress(self, step: str, completed: int, total: int, percentage: float):
        """Update job progress and notify callback."""
        self.progress = JobProgress(step, completed, total, percentage)

        if self.progress_callback:
            try:
                self.progress_callback(self.uid, self.status.value, self.progress.to_dict())
            except Exception as e:
                logger.warning(f"Progress callback failed for {self.uid}: {e}")

        logger.debug(f"Job {self.uid} progress: {step} ({percentage:.1f}%)")

    def _check_cancelled(self) -> bool:
        """Check if job has been cancelled."""
        return self.cancelled

    def _add_uid_mapping(self, result: JobResult):
        """Add UID mapping for completed download."""
        try:
            if result.success and result.file_paths:
                metadata = {
                    "download_type": "roblox_3d_avatar",
                    "username": result.username,
                    "user_id": result.user_id,
                    "download_stats": result.download_stats,
                    "downloaded_at": datetime.now().isoformat()
                }

                self.uid_manager.add_mapping(
                    uid=self.uid,
                    content_type="3d_object",
                    filename=f"{result.username}_{result.user_id}_3D",
                    session_id=self.session_id,
                    metadata=metadata
                )

                logger.info(f"Added UID mapping for successful download: {self.uid}")

        except Exception as e:
            logger.warning(f"Failed to add UID mapping for {self.uid}: {e}")


# Global job registry for tracking active downloads
_active_jobs: Dict[str, RobloxDownloadJob] = {}
_jobs_lock = threading.Lock()


def submit_download_job(uid: str, user_input: str, session_id: Optional[str] = None) -> RobloxDownloadJob:
    """
    Submit a new download job for background processing.

    Args:
        uid: Generated or reused object UID
        user_input: User ID or username to download
        session_id: Optional session ID

    Returns:
        RobloxDownloadJob instance for tracking
    """
    with _jobs_lock:
        # If UID already exists and is still active, cancel the old job first
        if uid in _active_jobs:
            old_job = _active_jobs[uid]
            if old_job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                logger.info(f"Cancelling existing active job for UID {uid}")
                try:
                    # Try to cancel in existing event loop
                    loop = asyncio.get_running_loop()
                    loop.create_task(old_job.cancel())
                except RuntimeError:
                    # No event loop, cancel synchronously by setting cancelled flag
                    old_job.cancelled = True
                    old_job.status = JobStatus.CANCELLED
                    logger.info(f"Marked existing job {uid} as cancelled")
                except Exception as e:
                    logger.warning(f"Failed to cancel existing job {uid}: {e}")

            # Remove old job from registry
            del _active_jobs[uid]

        job = RobloxDownloadJob(uid, user_input, session_id)
        _active_jobs[uid] = job

        # Start job execution in background
        _start_background_job(job)

        logger.info(f"Submitted download job: {uid} for user '{user_input}' (session: {session_id})")
        return job


def get_job_status(uid: str) -> Optional[Dict[str, Any]]:
    """Get status of a download job by UID."""
    with _jobs_lock:
        job = _active_jobs.get(uid)
        return job.get_status() if job else None


def cancel_job(uid: str) -> bool:
    """Cancel a download job by UID."""
    with _jobs_lock:
        job = _active_jobs.get(uid)
        if job:
            try:
                # Try to cancel in existing event loop
                loop = asyncio.get_running_loop()
                loop.create_task(job.cancel())
                return True
            except RuntimeError:
                # No event loop, cancel in background thread
                import threading

                def cancel_in_thread():
                    try:
                        asyncio.run(job.cancel())
                    except Exception as e:
                        logger.error(f"Failed to cancel job {uid} in background thread: {e}")

                thread = threading.Thread(target=cancel_in_thread, daemon=True)
                thread.start()
                logger.info(f"Started cancellation for job {uid} in background thread")
                return True
        return False


def cleanup_completed_jobs(max_age_hours: int = 24):
    """Clean up completed jobs older than specified age."""
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    with _jobs_lock:
        to_remove = []
        for uid, job in _active_jobs.items():
            if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and
                job.end_time and (current_time - job.end_time) > max_age_seconds):
                to_remove.append(uid)

        for uid in to_remove:
            del _active_jobs[uid]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} completed jobs older than {max_age_hours} hours")


def _start_background_job(job: RobloxDownloadJob):
    """Start a job in the background, handling event loop issues."""
    try:
        # Try to use existing event loop
        loop = asyncio.get_running_loop()
        loop.create_task(_execute_job_wrapper(job))
    except RuntimeError:
        # No event loop running, start one in a background thread
        import threading

        def run_in_thread():
            try:
                asyncio.run(_execute_job_wrapper(job))
            except Exception as e:
                logger.exception(f"Failed to run job {job.uid} in background thread: {e}")

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        logger.info(f"Started job {job.uid} in background thread")


async def _execute_job_wrapper(job: RobloxDownloadJob):
    """Wrapper for executing job and handling cleanup."""
    try:
        await job.execute()
    except Exception as e:
        logger.exception(f"Unhandled exception in job {job.uid}: {e}")
    finally:
        # Job will remain in registry for status polling until cleanup
        pass