"""
3D Format Handlers Package

Provides format-specific handlers for analyzing, validating, and processing
different 3D file formats including OBJ, FBX, GLTF, and future formats.
"""

from .base import BaseFormatHandler
from .obj_handler import OBJFormatHandler
from .fbx_handler import FBXFormatHandler
from .gltf_handler import GLTFFormatHandler
from .manager import (
    FormatManager,
    get_format_manager,
    detect_3d_format,
    analyze_3d_file,
    validate_3d_file,
    get_3d_associated_files,
    get_supported_3d_formats
)

__all__ = [
    # Base handler
    'BaseFormatHandler',

    # Format handlers
    'OBJFormatHandler',
    'FBXFormatHandler',
    'GLTFFormatHandler',

    # Format manager
    'FormatManager',
    'get_format_manager',

    # Convenience functions
    'detect_3d_format',
    'analyze_3d_file',
    'validate_3d_file',
    'get_3d_associated_files',
    'get_supported_3d_formats'
]