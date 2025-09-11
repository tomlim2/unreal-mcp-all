"""
Image management system for MegaMelange.

This package provides centralized image registry and storage using JSON files,
following the same patterns as the session management system.

Key Components:
- ImageRegistry: Main interface for image operations
- ImageStorage: JSON file storage backend
- ImageUtils: File operations and utilities

Usage:
    from tools.ai.image_management import get_image_registry
    
    registry = get_image_registry()
    image_id = registry.register_screenshot('/path/to/screenshot.png', 'session_123')
    image_url = registry.get_image_url(image_id)
"""

from .image_registry import ImageRegistry, get_image_registry
from .image_storage import ImageStorage
from .image_utils import ImageUtils
from .models import ImageRecord

__all__ = [
    'ImageRegistry',
    'get_image_registry', 
    'ImageStorage',
    'ImageUtils',
    'ImageRecord'
]