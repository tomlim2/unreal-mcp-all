"""
Tools information handlers.

Provides tools listing and health check endpoints.
"""

from typing import Dict, Any
import logging

from ..router import route
from ..middleware.trace_logger import log_request_start

logger = logging.getLogger("http_bridge.handlers.tools")


@route("/tools", method="GET", description="List available tools", tags=["Tools"])
def handle_tools_list(handler, request_data: dict, trace_id: str) -> Dict[str, Any]:
    """
    Handle tools listing request.

    Returns:
        Dict with tools information

    Response Format:
        {
            "plugin_system_enabled": bool,
            "tools": {
                "tool_id": {
                    "name": str,
                    "description": str,
                    "parameters": {...}
                },
                ...
            }
        }
    """
    log_request_start(trace_id, "GET", "/tools", None)

    try:
        from core import get_registry, get_config

        config = get_config()

        if not config.features.enable_plugin_system:
            return {
                'plugin_system_enabled': False,
                'message': 'Plugin system not enabled, using legacy handlers'
            }

        registry = get_registry()
        tools_dict = {}

        for tool_id, tool_info in registry.list_tools().items():
            tools_dict[tool_id] = {
                'name': tool_info.get('name', tool_id),
                'description': tool_info.get('description', ''),
                'parameters': tool_info.get('parameters', {})
            }

        return {
            'plugin_system_enabled': True,
            'tools': tools_dict
        }

    except Exception as e:
        logger.error(f"Error getting tools list: {e}")
        raise


@route("/tools/health", method="GET", description="Get tools health status", tags=["Tools"])
def handle_tools_health(handler, request_data: dict, trace_id: str) -> Dict[str, Any]:
    """
    Handle tools health check request.

    Returns:
        Dict with health status for each tool

    Response Format:
        {
            "plugin_system_enabled": bool,
            "tools": {
                "tool_id": "healthy" | "unhealthy" | "unknown",
                ...
            }
        }
    """
    log_request_start(trace_id, "GET", "/tools/health", None)

    try:
        from core import get_registry, get_config

        config = get_config()

        if not config.features.enable_plugin_system:
            return {
                'plugin_system_enabled': False,
                'message': 'Plugin system not enabled, using legacy handlers'
            }

        registry = get_registry()
        health_status = registry.get_health_status()

        return {
            'plugin_system_enabled': True,
            'tools': {
                tool_id: status.value
                for tool_id, status in health_status.items()
            }
        }

    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise
