"""
Screenshot Worker for handling Unreal Engine screenshot jobs.

Uses the worker pattern to handle variable-duration screenshot operations.
"""

import os
import time
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .job_manager import JobManager, JobStatus, JobResult

# Import session management for database storage
try:
    from ..ai.session_management import get_session_manager
    SESSION_MANAGEMENT_AVAILABLE = True
except ImportError:
    SESSION_MANAGEMENT_AVAILABLE = False
    logger.warning("Session management not available - job results won't be saved to chat context")

# Configure logging
logger = logging.getLogger("ScreenshotWorker")

class ScreenshotWorker:
    """Handles screenshot job execution and file detection."""
    
    def __init__(self, job_manager: JobManager, unreal_connection, project_path: Optional[str] = None):
        """Initialize screenshot worker."""
        self.job_manager = job_manager
        self.unreal_connection = unreal_connection
        
        # Log connection status
        if unreal_connection:
            logger.info("ScreenshotWorker initialized with Unreal connection")
        else:
            logger.warning("ScreenshotWorker initialized WITHOUT Unreal connection - jobs will fail")
        
        # Determine project path
        self.project_path = project_path or os.getenv('UNREAL_PROJECT_PATH')
        if self.project_path:
            # Unreal saves screenshots to Screenshots/WindowsEditor/ subdirectory
            base_screenshots_dir = Path(self.project_path) / "Saved" / "Screenshots"
            self.screenshots_dir = base_screenshots_dir / "WindowsEditor"
            
            # Fallback to base Screenshots directory if WindowsEditor doesn't exist yet
            if not self.screenshots_dir.exists() and base_screenshots_dir.exists():
                self.screenshots_dir = base_screenshots_dir
                
        else:
            self.screenshots_dir = None
            logger.warning("No Unreal project path configured - file serving will be limited")
        
        logger.info(f"ScreenshotWorker initialized with screenshots dir: {self.screenshots_dir}")

    def start_screenshot_job(self, job_id: str) -> bool:
        """Start a screenshot job in the background."""
        job = self.job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False
        
        if job.status != JobStatus.PENDING:
            logger.error(f"Job {job_id} is not in pending status: {job.status}")
            return False
        
        # Mark job as in progress with initial progress
        self.job_manager.update_job_status(job_id, JobStatus.IN_PROGRESS)
        self.job_manager.update_job_progress(job_id, 10.0)  # 10% - job started
        
        # Create initial job message in session if session_id available
        self._update_session_job_status(job_id, 'running', 'Screenshot job is starting...', 10)
        
        # Start background thread
        thread = threading.Thread(target=self._execute_screenshot_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started background thread for screenshot job {job_id}")
        return True

    def _execute_screenshot_job(self, job_id: str):
        """Execute screenshot job in background thread with timestamp-based detection."""
        try:
            print(f"DEBUG: Starting screenshot job execution for {job_id}")
            job = self.job_manager.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found during execution")
                print(f"DEBUG: Job {job_id} not found during execution")
                return
            
            logger.info(f"Executing screenshot job {job_id} with params: {job.params}")
            print(f"DEBUG: Executing screenshot job {job_id} with params: {job.params}")
            self.job_manager.update_job_progress(job_id, 20.0)  # 20% - preparing command
            
            # Record precise timestamp BEFORE executing command
            execution_start_time = time.time()
            
            # Check if we have Unreal connection
            if not self.unreal_connection:
                error_msg = "No Unreal Engine connection available - make sure Unreal Engine is running"
                logger.error(f"Screenshot command failed for job {job_id}: {error_msg}")
                self.job_manager.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
                return
                
            # Execute screenshot command via Unreal connection
            response = self.unreal_connection.send_command("take_highresshot", job.params)
            self.job_manager.update_job_progress(job_id, 40.0)  # 40% - command sent
            
            if not response or response.get("status") == "error":
                error_msg = response.get("error", "Unknown Unreal Engine error") if response else "No response from Unreal Engine"
                logger.error(f"Screenshot command failed for job {job_id}: {error_msg}")
                self.job_manager.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
                return
            
            logger.info(f"Screenshot command sent successfully for job {job_id}")
            self.job_manager.update_job_progress(job_id, 60.0)  # 60% - monitoring for file
            
            # Monitor for file creation using timestamp-based detection
            result = self._monitor_screenshot_with_timestamp(job_id, execution_start_time, max_wait_seconds=30)
            
            if result:
                self.job_manager.update_job_progress(job_id, 100.0)  # 100% - completed
                self.job_manager.update_job_status(job_id, JobStatus.COMPLETED, result=result)
                
                # Update session with completion and image URL
                image_url = f"/api/screenshot/download/{job_id}" if result.download_url else None
                self._update_session_job_status(job_id, 'completed', 
                                              f"Screenshot completed successfully: {result.filename}", 
                                              100, image_url)
                
                logger.info(f"Screenshot job {job_id} completed successfully: {result.filename}")
            else:
                error_msg = "Screenshot file detection timeout or failed"
                self.job_manager.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
                
                # Update session with failure
                self._update_session_job_status(job_id, 'failed', error_msg, 100)
                
                logger.error(f"Screenshot job {job_id} failed: {error_msg}")
                
        except Exception as e:
            error_msg = f"Screenshot job execution error: {str(e)}"
            logger.error(f"Job {job_id} failed with exception: {error_msg}")
            self.job_manager.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
            
            # Update session with exception failure
            self._update_session_job_status(job_id, 'failed', error_msg, 100)

    def _get_screenshot_file_count(self) -> int:
        """Get current number of screenshot files across all screenshot directories."""
        if not self.project_path:
            return 0
            
        try:
            total_count = 0
            base_dir = Path(self.project_path) / "Saved" / "Screenshots"
            
            # Check base directory and subdirectories
            search_dirs = []
            if base_dir.exists():
                search_dirs.append(base_dir)
                for subdir in ["WindowsEditor", "Windows", "Editor"]:
                    subdir_path = base_dir / subdir
                    if subdir_path.exists():
                        search_dirs.append(subdir_path)
            
            for search_dir in search_dirs:
                screenshot_files = list(search_dir.glob("*.png")) + list(search_dir.glob("*.jpg"))
                total_count += len(screenshot_files)
                
            return total_count
        except Exception as e:
            logger.warning(f"Failed to count screenshot files: {e}")
            return 0

    def _monitor_screenshot_with_timestamp(self, job_id: str, start_timestamp: float, max_wait_seconds: int = 30) -> Optional[JobResult]:
        """
        Monitor for screenshot file creation using timestamp-based detection.
        
        This is more reliable than file counting as it avoids race conditions
        and works correctly with multiple concurrent screenshots.
        """
        if not self.screenshots_dir:
            logger.warning(f"No screenshots directory configured - cannot monitor file creation for job {job_id}")
            return JobResult(
                filename="screenshot_generated.png",
                metadata={"note": "File monitoring not available - check Unreal Engine project directory"}
            )
        
        logger.info(f"Starting timestamp-based detection for job {job_id} (start_time: {start_timestamp})")
        
        poll_interval = 0.5  # Check every 500ms
        attempts = int(max_wait_seconds / poll_interval)
        
        for attempt in range(attempts):
            try:
                # Check if job was cancelled
                job = self.job_manager.get_job(job_id)
                if job and job.status == JobStatus.CANCELLED:
                    logger.info(f"Job {job_id} was cancelled during monitoring")
                    return None
                
                # Look for screenshot files created after start timestamp
                # Check both the main screenshots dir and subdirectories
                search_dirs = []
                if self.screenshots_dir and self.screenshots_dir.exists():
                    search_dirs.append(self.screenshots_dir)
                    
                # Also check base screenshots directory and common subdirectories
                if self.project_path:
                    base_dir = Path(self.project_path) / "Saved" / "Screenshots"
                    if base_dir.exists():
                        search_dirs.append(base_dir)
                        # Check common Unreal screenshot subdirectories
                        for subdir in ["WindowsEditor", "Windows", "Editor"]:
                            subdir_path = base_dir / subdir
                            if subdir_path.exists() and subdir_path not in search_dirs:
                                search_dirs.append(subdir_path)
                
                candidates = []
                for search_dir in search_dirs:
                    try:
                        for file_path in search_dir.iterdir():
                            if self._is_screenshot_file(file_path):
                                try:
                                    # Get file creation time
                                    file_stats = file_path.stat()
                                    creation_time = file_stats.st_mtime
                                    
                                    # Check if file was created after job start (with small buffer for timing)
                                    if creation_time > (start_timestamp - 1.0):
                                        candidates.append({
                                            'path': file_path,
                                            'created_at': creation_time,
                                            'size': file_stats.st_size
                                        })
                                except OSError as e:
                                    # File might be in use or deleted, skip
                                    logger.debug(f"Could not access file {file_path}: {e}")
                                    continue
                    except OSError as e:
                        logger.debug(f"Could not access directory {search_dir}: {e}")
                        continue
                    
                    # If we found candidates, take the most recently created
                    if candidates:
                        newest_file_info = max(candidates, key=lambda x: x['created_at'])
                        newest_file = newest_file_info['path']
                        
                        # Wait for file to be fully written
                        if self._wait_for_file_stability(newest_file, max_wait_seconds=5):
                            # File is ready - create result
                            file_stats = newest_file.stat()
                            
                            # Generate URLs
                            download_url = f"/api/screenshot/download/{job_id}"
                            thumbnail_url = f"/api/screenshot/thumbnail/{job_id}"
                            
                            result = JobResult(
                                filename=newest_file.name,
                                filepath=str(newest_file),
                                download_url=download_url,
                                thumbnail_url=thumbnail_url,
                                file_size=file_stats.st_size,
                                metadata={
                                    "created_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                                    "detection_method": "timestamp-based",
                                    "job_start_time": start_timestamp,
                                    "file_creation_time": file_stats.st_mtime,
                                    "detection_attempts": attempt + 1,
                                    "project_path": str(self.project_path),
                                    "relative_path": str(newest_file.relative_to(Path(self.project_path)))
                                }
                            )
                            
                            logger.info(f"Timestamp-based detection successful for job {job_id}: {newest_file.name} "
                                      f"({file_stats.st_size} bytes, detected in {attempt + 1} attempts)")
                            return result
                
                # Wait before next attempt with exponential backoff
                time.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.2, 2.0)  # Cap at 2 seconds
                
            except Exception as e:
                logger.error(f"Error during timestamp-based detection for job {job_id} (attempt {attempt + 1}): {e}")
                time.sleep(poll_interval)
        
        logger.error(f"Timestamp-based detection timeout for job {job_id} after {max_wait_seconds}s")
        return None

    def _monitor_screenshot_completion(self, job_id: str, initial_file_count: int, max_wait_seconds: int = 30) -> Optional[JobResult]:
        """Monitor for screenshot file creation."""
        if not self.screenshots_dir:
            logger.warning(f"No screenshots directory configured - cannot monitor file creation for job {job_id}")
            # Return a basic result without file detection
            return JobResult(
                filename="screenshot_generated.png",
                metadata={"note": "File monitoring not available - check Unreal Engine project directory"}
            )
        
        start_time = time.time()
        check_interval = 0.5  # Check every 500ms
        
        logger.info(f"Monitoring screenshot completion for job {job_id} (initial count: {initial_file_count})")
        
        while (time.time() - start_time) < max_wait_seconds:
            try:
                # Check if we've been cancelled
                job = self.job_manager.get_job(job_id)
                if job and job.status == JobStatus.CANCELLED:
                    logger.info(f"Job {job_id} was cancelled during monitoring")
                    return None
                
                # Look for new files
                if self.screenshots_dir.exists():
                    screenshot_files = sorted(
                        list(self.screenshots_dir.glob("*.png")) + list(self.screenshots_dir.glob("*.jpg")),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )
                    
                    current_file_count = len(screenshot_files)
                    
                    if current_file_count > initial_file_count:
                        # New file detected - get the most recent one
                        latest_file = screenshot_files[0]
                        
                        # Wait for file to be fully written (check size stability)
                        if self._wait_for_file_stability(latest_file, max_wait_seconds=5):
                            # File is ready
                            file_stats = latest_file.stat()
                            
                            # Generate URLs (will be handled by HTTP endpoints)
                            download_url = f"/api/screenshot/download/{job_id}"
                            thumbnail_url = f"/api/screenshot/thumbnail/{job_id}"
                            
                            result = JobResult(
                                filename=latest_file.name,
                                filepath=str(latest_file),
                                download_url=download_url,
                                thumbnail_url=thumbnail_url,
                                file_size=file_stats.st_size,
                                metadata={
                                    "created_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                                    "project_path": str(self.project_path),
                                    "relative_path": str(latest_file.relative_to(Path(self.project_path)))
                                }
                            )
                            
                            logger.info(f"Screenshot file detected for job {job_id}: {latest_file.name} ({file_stats.st_size} bytes)")
                            return result
                
                time.sleep(check_interval)
                
                # Exponential backoff (but cap at 2 seconds)
                check_interval = min(check_interval * 1.1, 2.0)
                
            except Exception as e:
                logger.error(f"Error during file monitoring for job {job_id}: {e}")
                time.sleep(1)
        
        logger.warning(f"Screenshot file detection timeout for job {job_id} after {max_wait_seconds}s")
        return None

    def _wait_for_file_stability(self, file_path: Path, max_wait_seconds: int = 5) -> bool:
        """Wait for file size to stabilize (indicating write completion)."""
        try:
            last_size = 0
            stable_count = 0
            check_interval = 0.2
            
            start_time = time.time()
            
            while (time.time() - start_time) < max_wait_seconds:
                if not file_path.exists():
                    return False
                
                current_size = file_path.stat().st_size
                
                if current_size == last_size:
                    stable_count += 1
                    if stable_count >= 3:  # Size stable for 3 checks
                        return True
                else:
                    stable_count = 0
                
                last_size = current_size
                time.sleep(check_interval)
            
            return True  # Assume it's done even if not perfectly stable
            
        except Exception as e:
            logger.error(f"Error checking file stability: {e}")
            return False

    def _is_screenshot_file(self, file_path: Path) -> bool:
        """Check if file matches Unreal Engine screenshot pattern."""
        if not file_path.is_file():
            return False
        
        filename = file_path.name.lower()
        return (
            filename.startswith('highresscreenshot') and 
            (filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'))
        )

    def get_screenshot_file_path(self, job_id: str) -> Optional[Path]:
        """Get the actual file path for a completed screenshot job."""
        job = self.job_manager.get_job(job_id)
        if not job or job.status != JobStatus.COMPLETED or not job.result:
            return None
        
        if job.result.filepath:
            file_path = Path(job.result.filepath)
            if file_path.exists():
                return file_path
        
        # Fallback: try to find by filename
        if job.result.filename and self.screenshots_dir:
            file_path = self.screenshots_dir / job.result.filename
            if file_path.exists():
                return file_path
        
        return None
    
    def _update_session_job_status(self, job_id: str, job_status: str, content: str, 
                                  job_progress: int = None, image_url: str = None):
        """Update job status in session conversation history."""
        if not SESSION_MANAGEMENT_AVAILABLE:
            return
        
        try:
            # Get job to find session_id
            job = self.job_manager.get_job(job_id)
            if not job or not job.session_id:
                logger.debug(f"No session_id found for job {job_id}, skipping session update")
                return
            
            # Get session manager and update job status
            session_manager = get_session_manager()
            success = session_manager.update_job_status(
                session_id=job.session_id,
                job_id=job_id,
                job_status=job_status,
                content=content,
                job_progress=job_progress,
                image_url=image_url
            )
            
            if success:
                logger.info(f"Updated session {job.session_id} with job {job_id} status: {job_status}")
            else:
                logger.warning(f"Failed to update session {job.session_id} with job {job_id} status")
                
        except Exception as e:
            logger.error(f"Error updating session for job {job_id}: {e}")