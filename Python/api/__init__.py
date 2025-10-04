"""
API Interface Layer

This package contains all external interface implementations:
- HTTP Bridge (REST API)
- WebSocket (future)
- CLI (future)
"""

from .http import *

__all__ = ['http']
