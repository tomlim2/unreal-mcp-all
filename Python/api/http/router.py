"""
Decorator-based routing system for HTTP Bridge.

Enables clean route registration with metadata for auto-documentation.
"""

from typing import Callable, Dict, Any, List, Optional
import logging

logger = logging.getLogger("http_bridge.router")

# Global route registry
ROUTES: Dict[tuple, Dict[str, Any]] = {}


def route(path: str, method: str = "GET", description: str = "", tags: Optional[List[str]] = None):
    """
    Register a route handler with metadata.

    Args:
        path: URL path (e.g., "/", "/sessions", "/api/screenshot-file/")
        method: HTTP method (GET, POST, PUT, DELETE, OPTIONS, HEAD)
        description: Human-readable description for documentation
        tags: Categories for grouping in documentation

    Returns:
        Decorator function that registers the handler

    Example:
        @route("/nlp", method="POST", description="Process NLP request", tags=["NLP"])
        def handle_nlp(handler, request_data, trace_id):
            return {"success": True}
    """
    def decorator(func: Callable) -> Callable:
        route_key = (path, method.upper())
        ROUTES[route_key] = {
            'handler': func,
            'description': description,
            'tags': tags or [],
            'name': func.__name__,
            'path': path,
            'method': method.upper()
        }
        logger.debug(f"Registered route: {method.upper()} {path} -> {func.__name__}")
        return func
    return decorator


def get_handler(path: str, method: str) -> Optional[Dict[str, Any]]:
    """
    Look up route handler by path and method.

    Args:
        path: Request path
        method: HTTP method

    Returns:
        Route info dict with 'handler' key, or None if not found
    """
    route_key = (path, method.upper())
    return ROUTES.get(route_key)


def get_all_routes() -> List[Dict[str, Any]]:
    """
    Get all registered routes.

    Returns:
        List of route metadata dicts

    Useful for:
        - Auto-generating OpenAPI/Swagger docs
        - Debug/introspection
        - Route listing endpoints
    """
    return list(ROUTES.values())


def clear_routes():
    """Clear all registered routes (useful for testing)"""
    ROUTES.clear()
