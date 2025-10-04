"""
Core utilities module.

Provides general-purpose utilities for the MegaMelange system.
"""

from .path_manager import (
    PathManager,
    PathConfig,
    get_path_manager,
    reset_path_manager
)

__all__ = [
    'PathManager',
    'PathConfig',
    'get_path_manager',
    'reset_path_manager'
]
