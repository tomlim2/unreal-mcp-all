"""
Worker infrastructure for long-running tasks.

This package provides a job-based worker system for handling operations
that take variable amounts of time, such as screenshot generation.
"""

from .job_manager import JobManager, JobStatus, JobResult
from .screenshot_worker import ScreenshotWorker

__all__ = ['JobManager', 'JobStatus', 'JobResult', 'ScreenshotWorker']