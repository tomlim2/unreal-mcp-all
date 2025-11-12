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


@route("/api/assets/preview-rename", method="POST", description="Preview asset renames without applying", tags=["Assets"])
def handle_preview_rename(handler, request_data: dict, trace_id: str) -> Dict[str, Any]:
    """
    Preview what assets will be renamed based on naming conventions.

    Request Format:
        {
            "naming_convention": "by_type",  // Apply type-based prefixes
            "custom_prefixes": {  // Optional custom prefix map
                "Texture2D": "T_",
                "Material": "M_",
                ...
            }
        }

    Returns:
        Dict with preview information

    Response Format:
        {
            "success": True,
            "preview": [
                {
                    "path": "/Game/Textures/Wall",
                    "old_name": "Wall",
                    "new_name": "T_Wall",
                    "needs_rename": True,
                    "asset_type": "Texture2D"
                },
                ...
            ]
        }
    """
    log_request_start(trace_id, "POST", "/api/assets/preview-rename", request_data)

    try:
        from tools.ai.nlp import execute_command_direct

        # First, get selected assets
        assets_result = execute_command_direct({
            "type": "get_selected_assets",
            "params": {}
        })

        if not assets_result or assets_result.get("status") == "error":
            return {
                "success": False,
                "error": assets_result.get("error", "Failed to get selected assets")
            }

        # Get assets from result
        result_data = assets_result.get("result", {})
        assets = result_data.get("assets", [])

        # Get naming convention settings
        naming_convention = request_data.get("naming_convention", "by_type")
        custom_prefixes = request_data.get("custom_prefixes", {})

        # Default type-based prefixes
        default_prefixes = {
            "Texture2D": "T_",
            "Material": "M_",
            "MaterialInstance": "MI_",
            "MaterialInstanceConstant": "MI_",
            "StaticMesh": "SM_",
            "SkeletalMesh": "SK_",
            "Blueprint": "BP_",
            "ParticleSystem": "PS_",
            "SoundCue": "SC_",
            "AnimSequence": "AS_",
            "AnimBlueprint": "ABP_",
            "PhysicsAsset": "PHYS_"
        }

        # Merge with custom prefixes
        prefixes = {**default_prefixes, **custom_prefixes}

        # Build preview
        preview = []
        for asset in assets:
            asset_type = asset.get("type", "")
            old_name = asset.get("name", "")
            path = asset.get("path", "")

            # Get prefix for this type
            prefix = prefixes.get(asset_type, "")

            # Check if already has prefix
            if prefix and old_name.startswith(prefix):
                new_name = old_name
                needs_rename = False
            elif prefix:
                # Remove any existing prefix before adding new one
                # Simple heuristic: remove text before first underscore if it looks like a prefix
                parts = old_name.split("_", 1)
                if len(parts) > 1 and len(parts[0]) <= 4:  # Likely a prefix
                    new_name = prefix + parts[1]
                else:
                    new_name = prefix + old_name
                needs_rename = True
            else:
                new_name = old_name
                needs_rename = False

            preview.append({
                "path": path,
                "old_name": old_name,
                "new_name": new_name,
                "needs_rename": needs_rename,
                "asset_type": asset_type
            })

        return {
            "success": True,
            "preview": preview,
            "total": len(preview),
            "to_rename": sum(1 for p in preview if p["needs_rename"])
        }

    except Exception as e:
        logger.error(f"Error previewing rename: {e}")
        return {
            "success": False,
            "error": str(e)
        }
