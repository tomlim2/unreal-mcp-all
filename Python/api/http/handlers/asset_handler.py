"""
Asset operations handlers.

Provides endpoints for getting selected assets and performing batch renames.
"""

from typing import Dict, Any, Optional
import logging

from ..router import route
from ..middleware.trace_logger import log_request_start

logger = logging.getLogger("http_bridge.handlers.asset")


@route("/api/assets/selected", method="POST", description="Get selected assets from Unreal", tags=["Assets"])
def handle_get_selected_assets(handler, request_data: dict, trace_id: str) -> Dict[str, Any]:
    """
    Get currently selected assets in Unreal Engine Content Browser.

    Returns:
        Dict with selected assets information

    Response Format:
        {
            "success": True,
            "assets": [
                {
                    "path": "/Game/Textures/Wall",
                    "type": "Texture2D",
                    "name": "Wall",
                    "package_path": "/Game/Textures"
                },
                ...
            ],
            "count": 5
        }
    """
    log_request_start(trace_id, "POST", "/api/assets/selected", request_data)

    try:
        from tools.ai.nlp import execute_command_direct

        # Execute get_selected_assets command
        result = execute_command_direct({
            "type": "get_selected_assets",
            "params": {}
        })

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        logger.error(f"Error getting selected assets: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@route("/api/assets/rename", method="POST", description="Rename assets in batch", tags=["Assets"])
def handle_rename_assets(handler, request_data: dict, trace_id: str) -> Dict[str, Any]:
    """
    Rename multiple assets at once.

    Request Format:
        {
            "operations": [
                {
                    "old_path": "/Game/Textures/Wall",
                    "new_name": "T_Wall"
                },
                ...
            ]
        }

    Returns:
        Dict with rename results

    Response Format:
        {
            "success": True,
            "result": {
                "success": [...],
                "failed": [...],
                "total": 5,
                "success_count": 4,
                "failed_count": 1
            }
        }
    """
    log_request_start(trace_id, "POST", "/api/assets/rename", request_data)

    try:
        from tools.ai.nlp import execute_command_direct

        # Validate request
        if "operations" not in request_data:
            return {
                "success": False,
                "error": "Missing 'operations' parameter"
            }

        # Execute rename_assets_batch command
        result = execute_command_direct({
            "type": "rename_assets_batch",
            "params": {
                "operations": request_data["operations"]
            }
        })

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        logger.error(f"Error renaming assets: {e}")
        return {
            "success": False,
            "error": str(e)
        }
