"""
3D Object Management System

Provides comprehensive 3D object resource management with UID-based storage,
multi-format support, metadata management, and quality assessment.
"""

from .manager import (
    Object3DManager,
    Object3DMetadata,
    get_object_3d_manager,
    store_3d_object,
    get_3d_object,
    get_session_objects,
    search_3d_objects,
    get_3d_object_statistics,
    get_supported_3d_formats,
    get_format_statistics
)

from .roblox_integration import (
    RobloxObject3DIntegration,
    get_roblox_3d_integration,
    download_roblox_avatar,
    get_roblox_avatars_by_session,
    validate_roblox_avatar
)

from .formats import (
    BaseFormatHandler,
    OBJFormatHandler,
    FBXFormatHandler,
    GLTFFormatHandler,
    FormatManager,
    get_format_manager,
    detect_3d_format,
    analyze_3d_file,
    validate_3d_file,
    get_3d_associated_files
)

__all__ = [
    # Core manager
    'Object3DManager',
    'Object3DMetadata',
    'get_object_3d_manager',

    # Storage functions
    'store_3d_object',
    'get_3d_object',
    'get_session_objects',
    'search_3d_objects',
    'get_3d_object_statistics',
    'get_supported_3d_formats',
    'get_format_statistics',

    # Roblox integration
    'RobloxObject3DIntegration',
    'get_roblox_3d_integration',
    'download_roblox_avatar',
    'get_roblox_avatars_by_session',
    'validate_roblox_avatar',

    # Format handlers
    'BaseFormatHandler',
    'OBJFormatHandler',
    'FBXFormatHandler',
    'GLTFFormatHandler',
    'FormatManager',
    'get_format_manager',
    'detect_3d_format',
    'analyze_3d_file',
    'validate_3d_file',
    'get_3d_associated_files'
]