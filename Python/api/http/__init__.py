"""
HTTP Bridge Interface

Provides HTTP/REST API for frontend and external clients.
"""

from .router import route, get_handler, get_all_routes

__all__ = ['route', 'get_handler', 'get_all_routes']
