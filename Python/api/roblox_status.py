"""
Roblox download status API endpoint for HTTP bridge integration.

Provides RESTful endpoints for checking download progress and managing Roblox jobs.
Integrates with the async job system for real-time status updates.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException
from pathlib import Path

from ..tools.ai.command_handlers.roblox.roblox_job import get_job_status, cancel_job, cleanup_completed_jobs
from ..tools.ai.command_handlers.roblox.roblox_errors import RobloxError, RobloxErrorCodes

logger = logging.getLogger("UnrealMCP.API.RobloxStatus")


class RobloxStatusAPI:
    """API class for Roblox download status operations."""

    @staticmethod
    def get_download_status(uid: str) -> Dict[str, Any]:
        """
        Get status of a Roblox download job.

        Args:
            uid: Object UID to check status for

        Returns:
            Status information including progress and results

        Raises:
            HTTPException: For invalid UID or job not found
        """
        try:
            # Validate UID format
            if not uid or not isinstance(uid, str):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "Invalid UID format",
                        "code": RobloxErrorCodes.INVALID_USER_INPUT
                    }
                )

            if not uid.startswith("obj_"):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "UID must be in obj_XXX format",
                        "code": RobloxErrorCodes.INVALID_USER_INPUT
                    }
                )

            # Get job status
            status = get_job_status(uid)

            if status is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "error": f"Download job not found: {uid}",
                        "code": RobloxErrorCodes.USER_NOT_FOUND,
                        "suggestion": "Job may have completed and been cleaned up"
                    }
                )

            # Ensure success field is present
            if "success" not in status:
                status["success"] = True

            logger.debug(f"Retrieved status for Roblox download: {uid}")
            return status

        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except Exception as e:
            logger.exception(f"Error getting download status for {uid}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": f"Internal error: {str(e)}",
                    "code": RobloxErrorCodes.DOWNLOAD_FAILED
                }
            )

    @staticmethod
    def cancel_download(uid: str) -> Dict[str, Any]:
        """
        Cancel a Roblox download job.

        Args:
            uid: Object UID to cancel

        Returns:
            Cancellation result

        Raises:
            HTTPException: For invalid UID or job not found
        """
        try:
            # Validate UID format
            if not uid or not isinstance(uid, str):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "Invalid UID format",
                        "code": RobloxErrorCodes.INVALID_USER_INPUT
                    }
                )

            if not uid.startswith("obj_"):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "UID must be in obj_XXX format",
                        "code": RobloxErrorCodes.INVALID_USER_INPUT
                    }
                )

            # Attempt cancellation
            cancelled = cancel_job(uid)

            if cancelled:
                response = {
                    "success": True,
                    "uid": uid,
                    "status": "cancelled",
                    "message": f"Download job {uid} has been cancelled"
                }
                logger.info(f"Cancelled Roblox download via API: {uid}")
                return response
            else:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "error": f"Download job not found or already completed: {uid}",
                        "code": RobloxErrorCodes.USER_NOT_FOUND,
                        "suggestion": "Job may have already completed or been cleaned up"
                    }
                )

        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except Exception as e:
            logger.exception(f"Error cancelling download for {uid}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": f"Internal error: {str(e)}",
                    "code": RobloxErrorCodes.DOWNLOAD_FAILED
                }
            )

    @staticmethod
    def cleanup_jobs(max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up completed jobs older than specified age.

        Args:
            max_age_hours: Maximum age in hours for job cleanup

        Returns:
            Cleanup result information
        """
        try:
            cleanup_completed_jobs(max_age_hours)

            response = {
                "success": True,
                "message": f"Cleaned up completed jobs older than {max_age_hours} hours",
                "cleanup_age_hours": max_age_hours
            }

            logger.info(f"Cleaned up Roblox jobs via API (max age: {max_age_hours}h)")
            return response

        except Exception as e:
            logger.exception(f"Error during job cleanup: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": f"Cleanup failed: {str(e)}",
                    "code": RobloxErrorCodes.DOWNLOAD_FAILED
                }
            )

    @staticmethod
    def get_file(uid: str, file_type: str = "obj") -> Optional[Path]:
        """
        Get file path for a completed download.

        Args:
            uid: Object UID
            file_type: Type of file to retrieve (obj, mtl, metadata, etc.)

        Returns:
            Path to file if available, None otherwise

        Raises:
            HTTPException: For invalid parameters or file not found
        """
        try:
            # Validate UID format
            if not uid or not isinstance(uid, str) or not uid.startswith("obj_"):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "Invalid UID format",
                        "code": RobloxErrorCodes.INVALID_USER_INPUT
                    }
                )

            # Get job status to find file paths
            status = get_job_status(uid)
            if not status:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "error": f"Download job not found: {uid}",
                        "code": RobloxErrorCodes.USER_NOT_FOUND
                    }
                )

            # Check if job is completed
            if status.get("status") != "completed":
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": f"Download job not completed: {status.get('status')}",
                        "code": RobloxErrorCodes.DOWNLOAD_FAILED
                    }
                )

            # Get file paths from result
            result = status.get("result", {})
            file_paths = result.get("file_paths", {})

            if file_type not in file_paths:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "error": f"File type '{file_type}' not found in download",
                        "code": RobloxErrorCodes.USER_NOT_FOUND,
                        "available_types": list(file_paths.keys())
                    }
                )

            file_path = Path(file_paths[file_type])
            if not file_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "error": f"File not found on disk: {file_path}",
                        "code": RobloxErrorCodes.DOWNLOAD_FAILED
                    }
                )

            return file_path

        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except Exception as e:
            logger.exception(f"Error getting file for {uid}/{file_type}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": f"Internal error: {str(e)}",
                    "code": RobloxErrorCodes.DOWNLOAD_FAILED
                }
            )


# Convenience functions for FastAPI route integration

def get_roblox_download_status(uid: str) -> Dict[str, Any]:
    """Convenience function for FastAPI route."""
    return RobloxStatusAPI.get_download_status(uid)


def cancel_roblox_download(uid: str) -> Dict[str, Any]:
    """Convenience function for FastAPI route."""
    return RobloxStatusAPI.cancel_download(uid)


def cleanup_roblox_jobs(max_age_hours: int = 24) -> Dict[str, Any]:
    """Convenience function for FastAPI route."""
    return RobloxStatusAPI.cleanup_jobs(max_age_hours)


def get_roblox_file(uid: str, file_type: str = "obj") -> Optional[Path]:
    """Convenience function for FastAPI file serving."""
    return RobloxStatusAPI.get_file(uid, file_type)