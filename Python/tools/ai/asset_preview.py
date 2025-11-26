"""
Asset naming preview generator.

Analyzes asset names and generates preview of proposed changes
according to Unreal Engine naming conventions.
"""

import logging
import re
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


def _contains_cjk_characters(text: str) -> bool:
    """
    Check if text contains Chinese, Japanese, or Korean characters.

    Args:
        text: Text to check

    Returns:
        True if text contains CJK characters
    """
    # CJK Unicode ranges:
    # - Chinese: \u4e00-\u9fff
    # - Japanese Hiragana: \u3040-\u309f
    # - Japanese Katakana: \u30a0-\u30ff
    # - Korean Hangul: \uac00-\ud7af
    cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]')
    return bool(cjk_pattern.search(text))


def _to_pascal_case(text: str) -> str:
    """
    Convert text to PascalCase.

    Args:
        text: Text to convert

    Returns:
        PascalCase formatted text
    """
    # Split by underscore, space, or hyphen
    words = re.split(r'[_\s\-]+', text)
    # Capitalize first letter of each word, remove empty strings
    return ''.join(word.capitalize() for word in words if word)


def rename_assets_batch_with_llm(assets: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Rename all assets in one LLM call following Unreal Engine standards.

    Rules applied:
    1. English only (translate CJK)
    2. Correct UE prefix based on asset type
    3. PascalCase

    Args:
        assets: List of asset dicts with 'name' and 'type' fields

    Returns:
        Dict mapping current name to new name
    """
    if not assets or not LLM_AVAILABLE:
        return {asset['name']: asset['name'] for asset in assets}

    try:
        # Build ultra-compact list: name,type
        prompt_lines = ["Fix UE naming:"]
        for i, asset in enumerate(assets, 1):
            name = asset.get('name', '')
            asset_type = asset.get('type', '')
            prompt_lines.append(f"{i}.{name},{asset_type}")
        prompt_lines.append("Output:")
        prompt = "\n".join(prompt_lines)

        # Get model provider
        from tools.ai.model_providers import get_model_provider, get_default_model
        model = get_default_model()
        provider = get_model_provider(model)

        if not provider:
            logger.warning("Could not get model provider for batch rename")
            return {asset['name']: asset['name'] for asset in assets}

        logger.info(f"Batch renaming {len(assets)} assets with LLM")
        logger.info(f"Prompt:\n{prompt}")

        # Call LLM with system prompt for rules
        system_prompt = "Fix: English+UEprefix+PascalCase"
        response = provider.generate_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            max_tokens=4096,  # Increased
            temperature=0.0
        )

        logger.info(f"LLM response:\n{response}")

        # Parse numbered response
        result = {}
        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Match "1. T_Weapon" or "1.T_Weapon,Texture2D" or "1. T_Weapon,Texture2D"
            match = re.match(r'^(\d+)\.?\s*(.+)$', line)
            if match:
                index = int(match.group(1)) - 1
                name_part = match.group(2).strip()
                # Remove asset type if present (e.g., "T_Weapon,Texture2D" → "T_Weapon")
                if ',' in name_part:
                    new_name = name_part.split(',')[0].strip()
                else:
                    new_name = name_part
                if 0 <= index < len(assets):
                    current_name = assets[index]['name']
                    result[current_name] = new_name

        logger.info(f"Batch rename complete: {len(result)} names processed")
        logger.info(f"Rename mapping: {result}")
        return result

    except Exception as e:
        logger.error(f"Batch rename failed: {e}, using original names")
        return {asset['name']: asset['name'] for asset in assets}


def translate_cjk_names_batch(names: List[str]) -> Dict[str, str]:
    """
    Translate multiple CJK names to English in a single API call (batch processing).

    Args:
        names: List of CJK names to translate

    Returns:
        Dict mapping original name to translated name
    """
    if not names or not LLM_AVAILABLE:
        return {name: name for name in names}

    try:
        # OPTIMIZATION: Remove duplicates (e.g., "体", "体_outline" → only "体")
        unique_cjk = {}  # Maps clean CJK → original names with that CJK
        for name in names:
            # Extract CJK part (remove suffixes like "_outline", "+", numbers)
            clean_cjk = name.replace("_outline", "").replace("+", "")
            clean_cjk = re.sub(r'^face_', '', clean_cjk)  # Remove "face_" prefix
            clean_cjk = re.sub(r'\d+$', '', clean_cjk)  # Remove trailing numbers

            if clean_cjk not in unique_cjk:
                unique_cjk[clean_cjk] = []
            unique_cjk[clean_cjk].append(name)

        unique_names = list(unique_cjk.keys())
        logger.info(f"Deduplicated {len(names)} names → {len(unique_names)} unique CJK parts")

        # Build compact CSV prompt with example
        names_csv = ",".join(unique_names)
        prompt = f"Translate: {names_csv}\nOutput CSV only:"

        # Get model provider
        from tools.ai.model_providers import get_model_provider, get_default_model
        model = get_default_model()
        provider = get_model_provider(model)

        if not provider:
            logger.warning("Could not get model provider for batch translation")
            return {name: name for name in names}

        logger.info(f"Batch translating {len(unique_names)} unique CJK parts in single API call")
        logger.info(f"Batch prompt: {prompt}")

        # Call LLM once for all unique names
        response = provider.generate_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="",  # Empty to save tokens
            max_tokens=2048,  # Maximum for Gemini
            temperature=0.0
        )

        logger.info(f"Batch response: {response}")

        # Parse CSV response (e.g., "Body,Weapon,Headwear,...")
        # Split by comma and clean up each entry
        translated_raw = response.split(",")
        translated = []
        for entry in translated_raw:
            # Remove newlines, extra spaces
            cleaned = entry.strip().replace("\n", " ").replace("\r", "")
            if cleaned:
                translated.append(cleaned)

        # Create translation mapping for unique CJK parts
        cjk_to_english = {}
        for i, unique_cjk in enumerate(unique_names):
            if i < len(translated):
                # Convert to PascalCase (handles spaces, hyphens, etc.)
                english = _to_pascal_case(translated[i])
                cjk_to_english[unique_cjk] = english

        # Map back to original names (including variants with _outline, +, etc.)
        result = {}
        for name in names:
            # Extract CJK part
            clean_cjk = name.replace("_outline", "").replace("+", "")
            clean_cjk = re.sub(r'^face_', '', clean_cjk)
            clean_cjk = re.sub(r'\d+$', '', clean_cjk)

            # Get translation
            if clean_cjk in cjk_to_english:
                result[name] = cjk_to_english[clean_cjk]
            else:
                result[name] = name  # Fallback

        logger.info(f"Batch translation complete: {len(unique_names)} unique → {len(result)} total names")
        logger.info(f"Translation mapping: {cjk_to_english}")
        return result

    except Exception as e:
        logger.error(f"Batch translation failed: {e}, using original names")
        return {name: name for name in names}


def generate_asset_rename_preview(assets: List[Dict[str, Any]], user_constraints: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate preview of asset rename operations.

    Uses LLM to rename ALL assets in one batch call following UE standards:
    1. English only (translate CJK)
    2. Correct UE prefix based on asset type
    3. PascalCase

    Args:
        assets: List of asset dicts with 'name', 'type', 'path' fields
        user_constraints: User preferences/constraints (optional, not used in unified approach)

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

    # UNIFIED APPROACH: Send all assets to LLM in one call
    logger.info(f"Generating preview for {len(assets)} assets using unified LLM batch rename")
    rename_map = rename_assets_batch_with_llm(assets)

    # Process each asset with rename results
    for asset in assets:
        current_name = asset.get("name", "")
        asset_type = asset.get("type", "")
        asset_path = asset.get("path", "")
        package_path = asset.get("package_path", "")

        # Get proposed name from LLM result
        proposed_name = rename_map.get(current_name, current_name)
        needs_rename = current_name != proposed_name

        logger.info(f"Asset: {current_name} → {proposed_name} (needs_rename: {needs_rename})")

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


def apply_naming_convention(current_name: str, asset_type: str, user_constraints: Optional[str] = None, translation_map: Optional[Dict[str, str]] = None) -> str:
    """
    Apply Unreal Engine naming convention to asset name.

    Args:
        current_name: Current asset name
        asset_type: Asset type (e.g., "Texture2D", "Material")
        user_constraints: User preferences/constraints (e.g., "keep HDRI", "preserve brand names")
        translation_map: Pre-translated CJK names mapping (for batch processing)

    Returns:
        Properly prefixed name
    """
    # Get expected prefix for this type
    expected_prefix = ASSET_PREFIXES.get(asset_type, "")

    if not expected_prefix:
        # No prefix needed for this type
        return current_name

    # Remove any existing prefix (even if correct) to check the name part
    clean_name = remove_existing_prefix(current_name)

    # Check if translation is needed (CJK characters present)
    needs_translation = _contains_cjk_characters(clean_name)

    # Use batch translation if available
    if translation_map and clean_name in translation_map:
        clean_name = translation_map[clean_name]
        logger.info(f"Using batch translation for: {current_name} → {expected_prefix + clean_name}")
    elif needs_translation:
        # Fallback: Use LLM for individual translation (old method)
        clean_name = clean_name_with_llm(clean_name, expected_prefix, asset_type, user_constraints)

    # Always apply PascalCase to ensure consistent formatting
    clean_name_pascal = _to_pascal_case(clean_name)

    # Check if any change is needed
    proposed_name = expected_prefix + clean_name_pascal
    if current_name == proposed_name:
        return current_name  # No change needed

    logger.info(f"Applying naming convention: {current_name} → {proposed_name}")
    return proposed_name


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


def _build_name_cleanup_prompt(current_name: str, expected_prefix: str, asset_type: str, user_constraints: Optional[str] = None, has_cjk: bool = False) -> str:
    """
    Build prompt for LLM to intelligently clean up asset name.

    Args:
        current_name: Current asset name (after prefix removal)
        expected_prefix: Expected prefix for this asset type
        asset_type: Asset type (e.g., "MaterialInstanceConstant")
        user_constraints: User preferences/constraints (e.g., "keep HDRI", "preserve brand names")
        has_cjk: Whether the name contains Chinese/Japanese/Korean characters

    Returns:
        Formatted prompt string for LLM
    """
    # Use ultra-compact prompt for CJK translation
    if has_cjk:
        # Examples: 体→Body, 前髪→FrontHair, 武器→Weapon, 头饰→Headwear
        return f"""Translate CJK to English, PascalCase, no explanation:
"{current_name}" →"""

    # Compact prompt for suffix cleanup
    constraint_note = f" Keep: {user_constraints}." if user_constraints else ""
    return f"""Clean asset name, remove redundant suffix only:{constraint_note}
Prefix={expected_prefix}, Name="{current_name}" → Output:"""


def clean_name_with_llm(name: str, expected_prefix: str, asset_type: str, user_constraints: Optional[str] = None) -> str:
    """
    Use LLM to intelligently clean up asset name by removing redundant suffixes.
    If the name contains Chinese/Japanese/Korean characters, translates them to English first.

    Args:
        name: Current asset name (after prefix removal)
        expected_prefix: Expected prefix for this asset type
        asset_type: Asset type
        user_constraints: User preferences/constraints (e.g., "keep HDRI", "preserve brand names")

    Returns:
        Cleaned name with redundant suffixes removed and CJK characters translated
    """
    # If LLM not available, return name as-is
    if not LLM_AVAILABLE:
        logger.debug(f"LLM not available, skipping intelligent cleanup for: {name}")
        return name

    try:
        # Check if name contains CJK characters
        has_cjk = _contains_cjk_characters(name)

        if has_cjk:
            logger.info(f"Detected CJK characters in asset name: '{name}', will translate to English")

        # Build prompt with user constraints and CJK translation if needed
        prompt = _build_name_cleanup_prompt(name, expected_prefix, asset_type, user_constraints, has_cjk)

        # Get model provider
        model = get_default_model()
        provider = get_model_provider(model)

        if not provider:
            logger.warning(f"Could not get model provider, skipping LLM cleanup for: {name}")
            return name

        # Call LLM with minimal tokens
        constraints_log = f" with constraints: {user_constraints}" if user_constraints else ""
        translation_log = " [CJK→EN]" if has_cjk else ""
        logger.info(f"Calling LLM to clean up name{translation_log}: '{name}' (prefix: {expected_prefix}, type: {asset_type}){constraints_log}")

        response = provider.generate_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="Clean name only.",  # Ultra-compact system prompt
            max_tokens=200,  # Sufficient for translation
            temperature=0.0  # Deterministic
        )

        # Clean up response
        cleaned_name = response.strip().strip('"').strip("'")

        # Validation: ensure we got a reasonable result
        # For CJK translation, length can increase significantly (e.g., "体" → "Body")
        max_length = len(name) * 5 if has_cjk else len(name) * 2
        if not cleaned_name or len(cleaned_name) > max_length:
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
