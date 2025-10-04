"""
3D Object Resource Processing Module

Central module for all 3D object processing operations.

Copyright Policy:
- User uploads: In-memory only (no storage, no UID)
- Generated 3D assets: Persistent with UID

Usage:
    from core.resources.objects_3d import process_3d_object, load_3d_object_from_uid

    uid, object_data = process_3d_object(
        object_request={'data': 'base64...', 'format': 'fbx'},
        target_object_uid='fbx_013'
    )
"""

from .processor import (
    Object3DProcessor,
    process_3d_object,
    load_3d_object_from_uid
)

__all__ = [
    'Object3DProcessor',
    'process_3d_object',
    'load_3d_object_from_uid'
]
