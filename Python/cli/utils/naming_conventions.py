"""Asset naming conventions for Unreal Engine"""
from typing import Dict, Tuple


# Standard Unreal Engine asset type prefixes
ASSET_PREFIXES: Dict[str, str] = {
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
    "DestructibleMesh": "DM_",

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


def remove_existing_prefix(name: str) -> str:
    """
    Remove existing prefix from asset name if present.

    Args:
        name: Asset name potentially with prefix

    Returns:
        Asset name without prefix
    """
    # Check if name starts with a prefix pattern (1-4 chars + underscore)
    parts = name.split("_", 1)
    if len(parts) > 1 and len(parts[0]) <= 4 and parts[0].isupper():
        return parts[1]
    return name


def apply_naming_convention(asset_name: str, asset_type: str,
                           prefixes: Dict[str, str] = None) -> Tuple[str, bool]:
    """
    Apply naming convention to an asset name.

    Args:
        asset_name: Current asset name
        asset_type: Asset type (class name)
        prefixes: Optional custom prefix mapping (uses ASSET_PREFIXES if None)

    Returns:
        Tuple of (new_name, needs_rename)
    """
    if prefixes is None:
        prefixes = ASSET_PREFIXES

    # Get the expected prefix for this asset type
    expected_prefix = prefixes.get(asset_type, "")

    if not expected_prefix:
        # No prefix defined for this type, return as-is
        return asset_name, False

    # Check if already has the correct prefix
    if asset_name.startswith(expected_prefix):
        return asset_name, False

    # Remove any existing prefix and add the correct one
    clean_name = remove_existing_prefix(asset_name)
    new_name = expected_prefix + clean_name

    return new_name, True


def validate_asset_name(name: str) -> Tuple[bool, str]:
    """
    Validate an asset name for Unreal Engine.

    Args:
        name: Asset name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Asset name cannot be empty"

    if name[0].isdigit():
        return False, "Asset name cannot start with a number"

    # Check for invalid characters
    invalid_chars = set(' \\/:*?"<>|')
    if any(char in invalid_chars for char in name):
        return False, f"Asset name contains invalid characters: {invalid_chars}"

    if len(name) > 100:
        return False, "Asset name is too long (max 100 characters)"

    return True, ""


def get_asset_type_category(asset_type: str) -> str:
    """
    Get the category of an asset type.

    Args:
        asset_type: Asset type (class name)

    Returns:
        Category name
    """
    categories = {
        "Texture": ["Texture2D", "TextureCube", "TextureRenderTarget2D"],
        "Material": ["Material", "MaterialInstance", "MaterialInstanceConstant", "MaterialFunction"],
        "Mesh": ["StaticMesh", "SkeletalMesh", "DestructibleMesh"],
        "Blueprint": ["Blueprint", "WidgetBlueprint", "AnimBlueprint"],
        "Animation": ["AnimSequence", "AnimMontage", "BlendSpace"],
        "Audio": ["SoundCue", "SoundWave"],
        "Particle": ["ParticleSystem", "NiagaraSystem"],
        "Physics": ["PhysicsAsset", "PhysicsMaterial"],
        "AI": ["BehaviorTree", "Blackboard"],
        "Data": ["DataTable", "CurveTable", "DataAsset"],
    }

    for category, types in categories.items():
        if asset_type in types:
            return category

    return "Other"
