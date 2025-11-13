"""
Asset naming preview generator.

Analyzes asset names and generates preview of proposed changes
according to Unreal Engine naming conventions.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("UnrealMCP")

# Import model providers for LLM-based name cleanup
try:
    from tools.ai.model_providers import get_model_provider, get_default_model
    LLM_AVAILABLE = True
except ImportError:
    logger.warning("Model providers not available - LLM-based name cleanup disabled")
    LLM_AVAILABLE = False


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


def generate_asset_rename_preview(assets: List[Dict[str, Any]], user_constraints: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate preview of asset rename operations.

    Args:
        assets: List of asset dicts with 'name', 'type', 'path' fields
        user_constraints: User preferences/constraints (e.g., "keep HDRI", "preserve brand names")

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

    # Log constraints if provided
    if user_constraints:
        logger.info(f"Generating preview with user constraints: {user_constraints}")

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

        # Generate proposed name with user constraints
        proposed_name = apply_naming_convention(current_name, asset_type, user_constraints)
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


def apply_naming_convention(current_name: str, asset_type: str, user_constraints: Optional[str] = None) -> str:
    """
    Apply Unreal Engine naming convention to asset name.

    Args:
        current_name: Current asset name
        asset_type: Asset type (e.g., "Texture2D", "Material")
        user_constraints: User preferences/constraints (e.g., "keep HDRI", "preserve brand names")

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

    # Use LLM to intelligently remove redundant suffixes with user constraints
    clean_name = clean_name_with_llm(clean_name, expected_prefix, asset_type, user_constraints)

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


def _build_name_cleanup_prompt(current_name: str, expected_prefix: str, asset_type: str, user_constraints: Optional[str] = None) -> str:
    """
    Build prompt for LLM to intelligently clean up asset name.

    Args:
        current_name: Current asset name (after prefix removal)
        expected_prefix: Expected prefix for this asset type
        asset_type: Asset type (e.g., "MaterialInstanceConstant")
        user_constraints: User preferences/constraints (e.g., "keep HDRI", "preserve brand names")

    Returns:
        Formatted prompt string for LLM
    """
    # Build constraints section
    constraints_text = ""
    if user_constraints:
        constraints_text = f"""

**IMPORTANT USER CONSTRAINTS:**
{user_constraints}

- If user said "keep HDRI" or "HDRI 유지" → preserve HDRI in the name
  Example: "HDRI_Attributes" → return "HDRI_Attributes" (keep HDRI)
- If user said "keep [word]" → preserve that word in the name
- User constraints take HIGHEST PRIORITY over standard cleanup rules
"""

    return f"""You are an Unreal Engine asset naming expert.

Task: Clean up the asset name by removing ONLY redundant suffixes that duplicate the prefix meaning.

Context:
- Current name: "{current_name}"
- Asset type: {asset_type}
- New prefix to be added: "{expected_prefix}"
{constraints_text}
Rules:
1. Remove suffixes that are redundant with the prefix meaning
   - Example: "Cakes2_MI" with prefix "MI_" → return "Cakes2" (remove _MI, it's redundant)
   - Example: "UV_Exterior_Inst" with prefix "MI_" → return "UV_Exterior" (remove Inst, MI already means Instance)
   - Example: "WoodTexture_T" with prefix "T_" → return "WoodTexture" (remove _T)

2. Keep suffixes that provide additional meaningful information
   - Example: "Wood_Floor_Rough" with prefix "M_" → return "Wood_Floor_Rough" (keep Rough, it describes material property)
   - Example: "Brick_Wall_02" with prefix "M_" → return "Brick_Wall_02" (keep 02, it's a variant number)
   - Example: "Metal_Rusted" with prefix "M_" → return "Metal_Rusted" (keep Rusted, meaningful descriptor)

3. Common redundant patterns to remove:
   - "_MI", "_Mat", "_Material" when prefix is "M_" or "MI_"
   - "_Tex", "_Texture" when prefix is "T_"
   - "_Mesh" when prefix is "SM_" or "SK_"
   - "_Inst", "_Instance" when prefix is "MI_"
   - "_BP" when prefix is "BP_"

4. Return ONLY the cleaned name without any prefix
5. Do not add any explanation, just the cleaned name
6. Preserve PascalCase and underscores in the cleaned name

Current name: {current_name}
Cleaned name:"""


def clean_name_with_llm(name: str, expected_prefix: str, asset_type: str, user_constraints: Optional[str] = None) -> str:
    """
    Use LLM to intelligently clean up asset name by removing redundant suffixes.

    Args:
        name: Current asset name (after prefix removal)
        expected_prefix: Expected prefix for this asset type
        asset_type: Asset type
        user_constraints: User preferences/constraints (e.g., "keep HDRI", "preserve brand names")

    Returns:
        Cleaned name with redundant suffixes removed
    """
    # If LLM not available, return name as-is
    if not LLM_AVAILABLE:
        logger.debug(f"LLM not available, skipping intelligent cleanup for: {name}")
        return name

    try:
        # Build prompt with user constraints
        prompt = _build_name_cleanup_prompt(name, expected_prefix, asset_type, user_constraints)

        # Get model provider
        model = get_default_model()
        provider = get_model_provider(model)

        if not provider:
            logger.warning(f"Could not get model provider, skipping LLM cleanup for: {name}")
            return name

        # Call LLM with minimal tokens
        constraints_log = f" with constraints: {user_constraints}" if user_constraints else ""
        logger.info(f"Calling LLM to clean up name: '{name}' (prefix: {expected_prefix}, type: {asset_type}){constraints_log}")

        response = provider.generate_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an Unreal Engine naming expert. Return only the cleaned asset name without prefix or explanation.",
            max_tokens=50,  # Small, we just need the cleaned name
            temperature=0.0  # Deterministic
        )

        # Clean up response
        cleaned_name = response.strip().strip('"').strip("'")

        # Validation: ensure we got a reasonable result
        if not cleaned_name or len(cleaned_name) > len(name) * 2:
            logger.warning(f"LLM returned unexpected result: '{cleaned_name}', falling back to original: '{name}'")
            return name

        logger.info(f"LLM cleanup: '{name}' → '{cleaned_name}'")
        return cleaned_name

    except Exception as e:
        logger.warning(f"LLM cleanup failed for '{name}': {e}, using original name")
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
        # English keywords
        "fix", "rename", "prefix", "casing", "capitalization",
        "naming", "convention", "proper", "correct",
        # Korean keywords (including conjugations)
        "접두어", "정리", "수정", "이름", "명명", "규칙",
        "바꾸", "바꿔", "바꾸세요", "바꿔주세요", "바꿔줘",  # change (various forms)
        "변경", "변경해", "변경해주세요",  # modify
        "프로세스", "처리",  # process
        "고치", "고쳐"  # fix
    ]

    user_lower = user_input.lower()
    return any(keyword in user_lower for keyword in rename_keywords)
