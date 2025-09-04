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

# Configure logging
logger = logging.getLogger("ScreenshotWorker")

class ScreenshotWorker:
    """Handles screenshot job execution and file detection."""
    
    def __init__(self, job_manager: JobManager, unreal_connection, project_path: Optional[str] = None):
        """Initialize screenshot worker."""
        self.job_manager = job_manager
        self.unreal_connection = unreal_connection
        
        # Determine project path
        self.project_path = project_path or os.getenv('UNREAL_PROJECT_PATH')
        if self.project_path:
            self.screenshots_dir = Path(self.project_path) / "Saved" / "Screenshots"
        else:
            self.screenshots_dir = None
            logger.warning("No Unreal project path configured - file serving will be limited")
        
        logger.info(f"ScreenshotWorker initialized with project path: {self.project_path}")

    def start_screenshot_job(self, job_id: str) -> bool:
        """Start a screenshot job in the background."""
        job = self.job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False
        
        if job.status != JobStatus.PENDING:
            logger.error(f"Job {job_id} is not in pending status: {job.status}")
            return False
        
        # Mark job as in progress
        self.job_manager.update_job_status(job_id, JobStatus.IN_PROGRESS)
        
        # Start background thread
        thread = threading.Thread(target=self._execute_screenshot_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started background thread for screenshot job {job_id}")
        return True

    def _execute_screenshot_job(self, job_id: str):
        """Execute screenshot job in background thread."""
        try:
            job = self.job_manager.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found during execution")
                return
            
            logger.info(f"Executing screenshot job {job_id} with params: {job.params}")
            
            # Get file count before screenshot
            file_count_before = self._get_screenshot_file_count()
            
            # Execute screenshot command via Unreal connection
            response = self.unreal_connection.send_command("take_highresshot", job.params)
            
            if not response or response.get("status") == "error":
                error_msg = response.get("error", "Unknown Unreal Engine error") if response else "No response from Unreal Engine"
                logger.error(f"Screenshot command failed for job {job_id}: {error_msg}")
                self.job_manager.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
                return
            
            logger.info(f"Screenshot command sent successfully for job {job_id}")
            
            # Monitor for file creation
            result = self._monitor_screenshot_completion(job_id, file_count_before, max_wait_seconds=30)
            
            if result:
                self.job_manager.update_job_status(job_id, JobStatus.COMPLETED, result=result)
                logger.info(f"Screenshot job {job_id} completed successfully: {result.filename}")
            else:
                error_msg = "Screenshot file detection timeout or failed"
                self.job_manager.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
                logger.error(f"Screenshot job {job_id} failed: {error_msg}")
                
        except Exception as e:
            error_msg = f"Screenshot job execution error: {str(e)}"
            logger.error(f"Job {job_id} failed with exception: {error_msg}")
            self.job_manager.update_job_status(job_id, JobStatus.FAILED, error=error_msg)

    def _get_screenshot_file_count(self) -> int:
        """Get current number of screenshot files."""
        if not self.screenshots_dir or not self.screenshots_dir.exists():
            return 0
        
        try:
            screenshot_files = list(self.screenshots_dir.glob("*.png")) + list(self.screenshots_dir.glob("*.jpg"))
            return len(screenshot_files)
        except Exception as e:
            logger.warning(f"Failed to count screenshot files: {e}")
            return 0

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