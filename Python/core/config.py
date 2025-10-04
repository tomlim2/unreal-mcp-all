"""
Creative Hub Configuration Management

Centralized configuration with feature flags for gradual migration.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("UnrealMCP.Config")


@dataclass
class FeatureFlags:
    """Feature flags for gradual migration to Creative Hub architecture."""

    # Core Features
    enable_plugin_system: bool = False  # Use new plugin-based tool system
    enable_orchestrator: bool = False   # Use multi-tool orchestrator
    enable_legacy_handlers: bool = True  # Keep old command handler system

    # Tool Features
    enable_nano_banana: bool = True     # Nano Banana image API
    enable_unreal_engine: bool = True   # Unreal Engine TCP connection
    enable_blender: bool = False        # Blender integration (future)
    enable_video_gen: bool = False      # Video generation (future)

    # Resource Management
    enable_video_resources: bool = True  # Video resource processing
    enable_3d_resources: bool = True     # 3D object resource processing

    # UI Features
    enable_tool_selector: bool = False  # Frontend tool selector UI
    enable_workflow_builder: bool = False  # Visual workflow builder


class Config:
    """
    Central configuration for Creative Hub.

    Loads settings from environment variables with sensible defaults.
    """

    def __init__(self):
        self._feature_flags = self._load_feature_flags()
        self._settings = self._load_settings()

    def _load_feature_flags(self) -> FeatureFlags:
        """Load feature flags from environment variables."""
        return FeatureFlags(
            # Core Features
            enable_plugin_system=self._get_bool_env('FEATURE_PLUGIN_SYSTEM', False),
            enable_orchestrator=self._get_bool_env('FEATURE_ORCHESTRATOR', False),
            enable_legacy_handlers=self._get_bool_env('FEATURE_LEGACY_HANDLERS', True),

            # Tool Features
            enable_nano_banana=self._get_bool_env('FEATURE_NANO_BANANA', True),
            enable_unreal_engine=self._get_bool_env('FEATURE_UNREAL_ENGINE', True),
            enable_blender=self._get_bool_env('FEATURE_BLENDER', False),
            enable_video_gen=self._get_bool_env('FEATURE_VIDEO_GEN', False),

            # Resource Management
            enable_video_resources=self._get_bool_env('FEATURE_VIDEO_RESOURCES', True),
            enable_3d_resources=self._get_bool_env('FEATURE_3D_RESOURCES', True),

            # UI Features
            enable_tool_selector=self._get_bool_env('FEATURE_TOOL_SELECTOR', False),
            enable_workflow_builder=self._get_bool_env('FEATURE_WORKFLOW_BUILDER', False),
        )

    def _load_settings(self) -> Dict[str, Any]:
        """Load general settings from environment."""
        return {
            # Server Settings
            'http_port': int(os.getenv('HTTP_PORT', '8080')),
            'tcp_port': int(os.getenv('UNREAL_TCP_PORT', '55557')),
            'tcp_host': os.getenv('UNREAL_TCP_HOST', '127.0.0.1'),

            # API Keys
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'google_api_key': os.getenv('GOOGLE_API_KEY'),

            # Paths
            'unreal_project_path': os.getenv('UNREAL_PROJECT_PATH'),

            # Debug
            'debug_mode': self._get_bool_env('DEBUG', False),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        }

    @staticmethod
    def _get_bool_env(key: str, default: bool) -> bool:
        """Parse boolean from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')

    @property
    def features(self) -> FeatureFlags:
        """Get feature flags."""
        return self._feature_flags

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._settings.get(key, default)

    def is_plugin_mode(self) -> bool:
        """Check if running in new plugin mode."""
        return self._feature_flags.enable_plugin_system

    def is_legacy_mode(self) -> bool:
        """Check if legacy handlers are enabled."""
        return self._feature_flags.enable_legacy_handlers

    def get_enabled_tools(self) -> list[str]:
        """Get list of enabled tool IDs."""
        enabled = []
        if self._feature_flags.enable_unreal_engine:
            enabled.append('unreal_engine')
        if self._feature_flags.enable_nano_banana:
            enabled.append('nano_banana')
        if self._feature_flags.enable_blender:
            enabled.append('blender')
        if self._feature_flags.enable_video_gen:
            enabled.append('video_generation')
        return enabled

    def log_status(self) -> None:
        """Log current configuration status."""
        logger.info("=" * 60)
        logger.info("Creative Hub Configuration")
        logger.info("=" * 60)
        logger.info(f"Plugin System: {'ENABLED' if self.features.enable_plugin_system else 'DISABLED'}")
        logger.info(f"Legacy Handlers: {'ENABLED' if self.features.enable_legacy_handlers else 'DISABLED'}")
        logger.info(f"Orchestrator: {'ENABLED' if self.features.enable_orchestrator else 'DISABLED'}")
        logger.info(f"Enabled Tools: {', '.join(self.get_enabled_tools())}")
        logger.info(f"HTTP Port: {self.get('http_port')}")
        logger.info(f"TCP Port: {self.get('tcp_port')}")
        logger.info("=" * 60)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance (singleton pattern).

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Reset the global config (primarily for testing)."""
    global _config
    _config = None
