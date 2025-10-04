"""
3D Object Resource Processor

Handles 3D object processing for all APIs with copyright-safe approach.

Copyright Policy:
- User-uploaded 3D objects: IN-MEMORY ONLY (no storage, no UID)
- Generated 3D objects: PERSISTENT with UID assignment
"""

import base64
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger("UnrealMCP.Resources.Objects3D")


class Object3DProcessor:
    """
    Central 3D object resource processor.

    Responsibilities:
    - Decode/validate user-uploaded 3D objects
    - Load 3D objects from UID system
    - Enforce copyright policy (no storage for user uploads)
    """

    # 3D object constraints
    MAX_OBJECT_SIZE_MB = 50
    ALLOWED_FORMATS = {
        'fbx', 'obj', 'gltf', 'glb', 'stl',
        'blend', 'dae', 'uasset'  # Unreal assets
    }

    @classmethod
    def decode_base64_object(cls, data_str: str, format: str = 'fbx') -> Dict[str, Any]:
        """
        Decode base64 3D object data.

        Args:
            data_str: Base64 encoded object data
            format: File format (fbx, obj, gltf, etc.)

        Returns:
            {'format': str, 'data': bytes}

        Raises:
            ValueError: Invalid format or unsupported type
        """
        format = format.lower()
        if format not in cls.ALLOWED_FORMATS:
            raise ValueError(
                f"Unsupported 3D format: {format}. "
                f"Allowed: {cls.ALLOWED_FORMATS}"
            )

        decoded_data = base64.b64decode(data_str)
        return {"format": format, "data": decoded_data}

    @classmethod
    def validate_object_size(cls, object_data: bytes, max_size_mb: int = None) -> None:
        """
        Validate 3D object size.

        Raises:
            ValueError: If object exceeds limit
        """
        max_size = max_size_mb or cls.MAX_OBJECT_SIZE_MB
        size_mb = len(object_data) / (1024 * 1024)

        if size_mb > max_size:
            raise ValueError(
                f"3D object too large: {size_mb:.2f}MB (max: {max_size}MB)"
            )


def process_3d_object(
    object_request: Optional[Dict[str, Any]] = None,
    target_object_uid: Optional[str] = None
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Process 3D object from request.

    Args:
        object_request: {'data': base64_str, 'format': str}
        target_object_uid: Existing object UID (from generation)

    Returns:
        (uid, object_data)
        - Option A (UID): (str, None) - Load from UID system
        - Option B (Upload): (None, Dict) - User-uploaded (in-memory)
        - Option C (Neither): (None, None) - No object provided

    Raises:
        ValueError: Invalid object format or size
    """
    # Priority 1: Load from UID
    if target_object_uid:
        logger.info(f"Loading 3D object from UID: {target_object_uid}")
        return (target_object_uid, None)

    # Priority 2: Process user upload (IN-MEMORY, NO STORAGE)
    if object_request:
        data_str = object_request.get('data')
        format = object_request.get('format', 'fbx')

        if not data_str:
            raise ValueError("object_request missing 'data' field")

        # Decode
        decoded = Object3DProcessor.decode_base64_object(data_str, format)

        # Validate size
        Object3DProcessor.validate_object_size(decoded['data'])

        logger.info(f"Processed user-uploaded 3D object: {decoded['format']}, "
                    f"{len(decoded['data']) / 1024 / 1024:.2f}MB (IN-MEMORY)")

        return (None, decoded)

    # No object provided
    return (None, None)


def load_3d_object_from_uid(uid: str) -> Optional[Path]:
    """
    Load 3D object file path from UID.

    Args:
        uid: 3D object UID (e.g., 'fbx_013', 'obj_042')

    Returns:
        Path to object file or None if not found
    """
    from core.resources.uid_manager import get_uid_mapping

    mapping = get_uid_mapping(uid)
    if not mapping:
        logger.warning(f"3D object UID not found: {uid}")
        return None

    # Get file path from mapping
    file_path = Path(mapping.get('file_path', ''))
    if not file_path.exists():
        logger.error(f"3D object file not found: {file_path}")
        return None

    logger.info(f"Loaded 3D object from UID {uid}: {file_path}")
    return file_path
