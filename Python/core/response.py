"""
Standardized success response system for MegaMelange backend.
Provides consistent response formatting across all API endpoints.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class SuccessResponse:
    """
    Standardized success response builder.

    Examples:
        Basic success:
        >>> response = SuccessResponse(
        ...     message="Operation completed successfully",
        ...     data={"result": "value"}
        ... )
        >>> response.to_response()

        With metadata:
        >>> response = SuccessResponse(
        ...     message="Image processed",
        ...     data={"uid": "img_001", "url": "/api/screenshot/..."},
        ...     metadata={"processing_time_ms": 1234, "model": "nanobanana"}
        ... )
    """
    message: str
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    status_code: int = 200

    def to_response(self) -> Dict[str, Any]:
        """
        Convert to HTTP response format.

        Returns flat structure with success, status_code, message, and optional data/metadata.
        """
        response = {
            "success": True,
            "status_code": self.status_code,
            "message": self.message
        }

        # Merge data into response (keeps existing patterns working)
        if self.data:
            response.update(self.data)

        # Add metadata as separate field
        if self.metadata:
            response["metadata"] = self.metadata

        return response


# Helper functions for common patterns

def success_response(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Create a generic success response.

    Args:
        message: Human-readable success message
        data: Optional data to include in response
        metadata: Optional metadata (timing, model info, etc.)
        status_code: HTTP status code (default 200)

    Returns:
        Formatted success response dictionary

    Example:
        >>> success_response(
        ...     message="Image uploaded successfully",
        ...     data={"uid": "img_001", "url": "/api/screenshot/file.png"},
        ...     metadata={"file_size_kb": 256}
        ... )
    """
    return SuccessResponse(
        message=message,
        data=data,
        metadata=metadata,
        status_code=status_code
    ).to_response()


def job_success(
    uid: str,
    message: str,
    status: str = "queued",
    estimated_time: Optional[str] = None,
    poll_url: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create success response for async job submission.

    Args:
        uid: Unique identifier for the job
        message: Human-readable message
        status: Job status (default "queued")
        estimated_time: Estimated completion time (e.g., "2-5 minutes")
        poll_url: URL to poll for job status
        additional_data: Additional job-specific data

    Returns:
        Formatted job success response

    Example:
        >>> job_success(
        ...     uid="obj_001",
        ...     message="Roblox download queued",
        ...     estimated_time="2-5 minutes",
        ...     poll_url="/api/roblox-status/obj_001"
        ... )
    """
    data = {
        "uid": uid,
        "status": status
    }

    if estimated_time:
        data["estimated_time"] = estimated_time

    if poll_url:
        data["poll_url"] = poll_url

    if additional_data:
        data.update(additional_data)

    return success_response(message=message, data=data)


def resource_success(
    uid: str,
    resource_type: str,
    message: str,
    url: Optional[str] = None,
    parent_uid: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    processing_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create success response for resource creation (image/video/object).

    Args:
        uid: Resource UID
        resource_type: Type of resource ("image", "video", "object", "fbx")
        message: Human-readable message
        url: Resource URL
        parent_uid: Optional parent resource UID
        metadata: Resource metadata (size, dimensions, etc.)
        processing_info: Processing metadata (model, origin, timing)

    Returns:
        Formatted resource success response

    Example:
        >>> resource_success(
        ...     uid="img_001",
        ...     resource_type="image",
        ...     message="Image styled successfully",
        ...     url="/api/screenshot/styled.png",
        ...     parent_uid="img_000",
        ...     metadata={"size": "1920x1080", "file_size_kb": 512},
        ...     processing_info={"model": "nanobanana", "processing_time_ms": 2340}
        ... )
    """
    data = {
        "uids": {resource_type: uid}
    }

    if parent_uid:
        data["uids"]["parent"] = parent_uid

    resource_data = {}
    if url:
        resource_data["url"] = url
    if metadata:
        resource_data["metadata"] = metadata

    if resource_data:
        data[resource_type] = resource_data

    return success_response(
        message=message,
        data=data,
        metadata=processing_info
    )


def conversion_success(
    source_uid: str,
    target_uid: str,
    source_type: str,
    target_type: str,
    message: str,
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create success response for format conversion operations.

    Args:
        source_uid: Source resource UID
        target_uid: Target resource UID
        source_type: Source format (e.g., "obj")
        target_type: Target format (e.g., "fbx")
        message: Human-readable message
        additional_data: Additional conversion-specific data

    Returns:
        Formatted conversion success response

    Example:
        >>> conversion_success(
        ...     source_uid="obj_123",
        ...     target_uid="fbx_456",
        ...     source_type="obj",
        ...     target_type="fbx",
        ...     message="FBX conversion successful"
        ... )
    """
    data = {
        f"{source_type}_uid": source_uid,
        f"{target_type}_uid": target_uid
    }

    if additional_data:
        data.update(additional_data)

    return success_response(message=message, data=data)
