"""
Asset naming preview generator.

Analyzes asset names and generates preview of proposed changes
according to Unreal Engine naming conventions.
"""

import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("UnrealMCP")


# Unreal Engine asset type prefixes
ASSET_PREFIXES = {
    # Textures
    "Texture2D": "T_",
    "TextureCube": "TC_",
    "TextureRenderTarget2D": "RT_",
    # Materials
    "Material": "M_",
    "MaterialInstance": "MI_",
    "MaterialInstanceConstant": "MI_",
    "MaterialFunction": "MF_",
    "MaterialParameterCollection": "MPC_",
    # Meshes
    "StaticMesh": "SM_",
    "SkeletalMesh": "SK_",
    "DestructibleMesh": "DM_",
    # Blueprints
    "Blueprint": "BP_",
    "WidgetBlueprint": "WBP_",
    "AnimBlueprint": "ABP_",
    "GameplayAbilityBlueprint": "GA_",
    # Animations
    "AnimSequence": "AS_",
    "AnimMontage": "AM_",
    "BlendSpace": "BS_",
    "AimOffsetBlendSpace": "AO_",
    # Particles & Effects
    "ParticleSystem": "PS_",
    "NiagaraSystem": "NS_",
    "NiagaraEmitter": "NE_",
    # Audio
    "SoundCue": "SC_",
    "SoundWave": "SW_",
    "SoundAttenuation": "SA_",
    "SoundConcurrency": "SCon_",
    # Physics
    "PhysicsAsset": "PHYS_",
    "PhysicsMaterial": "PM_",
    # AI
    "BehaviorTree": "BT_",
    "Blackboard": "BB_",
    "EnvironmentQuery": "EQ_",
    # UI
    "Font": "Font_",
    "SlateWidgetStyle": "SWS_",
    "SlateBrush": "SB_",
    # Data
    "DataTable": "DT_",
    "CurveTable": "CT_",
    "DataAsset": "DA_",
    # Other
    "LevelSequence": "LS_",
    "MediaPlayer": "MP_",
    "MediaTexture": "MT_",
    "Paper2DSprite": "SPR_",
    "PaperFlipbook": "FB_",
}


def generate_asset_rename_preview(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate preview of asset rename operations.

    Args:
        assets: List of asset dicts with 'name', 'type', 'path' fields

    Returns:
        Dict with:
        - preview_items: List of {current_name, proposed_name, needs_rename, asset_type, path}
        - operations: List of {old_path, new_name} for rename_assets_batch
        - preview_text: Formatted text preview for user
        - total_count: Total assets
        - rename_count: Assets needing rename
    """
    preview_items = []
    operations = []

    for asset in assets:
        current_name = asset.get("name", "")
        asset_type = asset.get("type", "")
        asset_path = asset.get("path", "")
        package_path = asset.get("package_path", "")

        logger.info(f"Processing asset for preview:")
        logger.info(f"  - name: {current_name}")
        logger.info(f"  - type: {asset_type}")
        logger.info(f"  - path (ObjectPath): {asset_path}")
        logger.info(f"  - package_path (PackagePath): {package_path}")
        logger.info(f"  - Full asset dict: {asset}")

        # Generate proposed name
        proposed_name = apply_naming_convention(current_name, asset_type)
        needs_rename = current_name != proposed_name

        preview_items.append({
            "current_name": current_name,
            "proposed_name": proposed_name,
            "needs_rename": needs_rename,
            "asset_type": asset_type,
            "path": asset_path
        })

        if needs_rename:
            # Verify path format - should be like "/Game/Path/AssetName.AssetName"
            if not asset_path or asset_path == "":
                logger.error(f"Empty path for asset {current_name}, skipping")
                continue

            # Use the full ObjectPath format for Unreal Asset Library
            # UEditorAssetLibrary expects: "/Game/Path/AssetName.AssetName"
            operations.append({
                "old_path": asset_path,
                "new_name": proposed_name
            })
            logger.info(f"Added operation: {asset_path} → {proposed_name}")

    # Generate formatted preview text
    preview_text = format_preview_text(preview_items)

    return {
        "preview_items": preview_items,
        "operations": operations,
        "preview_text": preview_text,
        "total_count": len(assets),
        "rename_count": len(operations)
    }


def apply_naming_convention(current_name: str, asset_type: str) -> str:
    """
    Apply Unreal Engine naming convention to asset name.

    Args:
        current_name: Current asset name
        asset_type: Asset type (e.g., "Texture2D", "Material")

    Returns:
        Properly prefixed name
    """
    # Get expected prefix for this type
    expected_prefix = ASSET_PREFIXES.get(asset_type, "")

    if not expected_prefix:
        # No prefix needed for this type
        return current_name

    # Check if already has correct prefix
    if current_name.startswith(expected_prefix):
        return current_name

    # Remove any existing incorrect prefix
    clean_name = remove_existing_prefix(current_name)

    # Apply correct prefix
    return expected_prefix + clean_name


def remove_existing_prefix(name: str) -> str:
    """
    Remove existing prefix from asset name if present.

    Args:
        name: Asset name possibly with prefix

    Returns:
        Name without prefix
    """
    # Check if name starts with a prefix pattern (1-4 chars + underscore)
    parts = name.split("_", 1)
    if len(parts) > 1 and len(parts[0]) <= 4 and parts[0].isupper():
        return parts[1]
    return name


def format_preview_text(preview_items: List[Dict[str, Any]]) -> str:
    """
    Format preview items into human-readable text.

    Args:
        preview_items: List of preview item dicts

    Returns:
        Formatted preview text
    """
    lines = []
    lines.append("\n📋 **Asset Rename Preview:**\n")

    # Group by needs_rename
    needs_rename = [item for item in preview_items if item["needs_rename"]]
    already_correct = [item for item in preview_items if not item["needs_rename"]]

    if needs_rename:
        lines.append(f"**{len(needs_rename)} asset(s) will be renamed:**\n")
        for item in needs_rename:
            lines.append(
                f"• `{item['current_name']}` ({item['asset_type']}) → `{item['proposed_name']}`"
            )
        lines.append("")

    if already_correct:
        lines.append(f"**{len(already_correct)} asset(s) already have correct naming:**\n")
        for item in already_correct:
            lines.append(f"• `{item['current_name']}` ✓")
        lines.append("")

    if needs_rename:
        lines.append("💡 **Say 'okay', 'apply', or 'execute' to apply these changes.**")
    else:
        lines.append("✅ **All assets already follow Unreal Engine naming conventions!**")

    return "\n".join(lines)


def should_generate_preview(user_input: str, command_type: str) -> bool:
    """
    Check if we should generate an asset rename preview.

    Args:
        user_input: Original user input
        command_type: Type of command that was executed

    Returns:
        True if preview should be generated
    """
    if command_type != "get_selected_assets":
        return False

    # Check if user input is about fixing/renaming assets
    rename_keywords = [
        "fix", "rename", "prefix", "casing", "capitalization",
        "naming", "convention", "proper", "correct"
    ]

    user_lower = user_input.lower()
    return any(keyword in user_lower for keyword in rename_keywords)
