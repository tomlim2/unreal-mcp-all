"""
Path Adapters for Backward Compatibility during Resource Path Centralization Migration.

Provides adapter interfaces that maintain existing API contracts while gradually
migrating to the centralized PathManager system. Implements the Zero Breaking Changes principle.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from .path_manager import get_path_manager, PathConfig

logger = logging.getLogger("PathManager.Adapters")


class LegacyPathAdapter:
    """
    Backward compatibility adapter for gradual migration from hardcoded paths to PathManager.

    Maintains existing interfaces while providing centralized path management under the hood.
    Allows instant fallback to legacy behavior via configuration flags.
    """

    def __init__(self, enable_centralized: bool = True):
        """
        Initialize adapter with centralization preference.

        Args:
            enable_centralized: Whether to use centralized paths or legacy behavior
        """
        self.enable_centralized = enable_centralized
        self._path_manager = get_path_manager() if enable_centralized else None

    @staticmethod
    def get_legacy_unreal_project_path() -> Optional[str]:
        """
        Get Unreal project path using PathManager but maintaining legacy interface.

        Replaces: os.getenv('UNREAL_PROJECT_PATH')

        Returns:
            str: Unreal project path if found, None otherwise
        """
        try:
            path_manager = get_path_manager()
            return path_manager.get_unreal_project_path()
        except Exception as e:
            logger.warning(f"PathManager failed, falling back to environment variable: {e}")
            return os.getenv('UNREAL_PROJECT_PATH')

    @staticmethod
    def get_legacy_screenshots_path() -> Optional[str]:
        """
        Get Unreal screenshots directory path.

        Replaces: Path(project_path) / "Saved" / "Screenshots" / "WindowsEditor"

        Returns:
            str: Screenshots directory path if available, None otherwise
        """
        try:
            path_manager = get_path_manager()
            screenshots_path = path_manager.get_unreal_screenshots_path()

            if screenshots_path:
                return screenshots_path

            # Fallback to legacy construction
            unreal_path = path_manager.get_unreal_project_path()
            if unreal_path:
                return str(Path(unreal_path) / "Saved" / "Screenshots" / "WindowsEditor")

            return None

        except Exception as e:
            logger.warning(f"PathManager failed for screenshots path, using fallback: {e}")
            project_path = os.getenv('UNREAL_PROJECT_PATH')
            if project_path:
                return str(Path(project_path) / "Saved" / "Screenshots" / "WindowsEditor")
            return None

    @staticmethod
    def get_legacy_styled_images_path() -> Optional[str]:
        """
        Get styled images directory path within Unreal project.

        Replaces: Path(project_path) / "Saved" / "Screenshots" / "styled"

        Returns:
            str: Styled images directory path if available, None otherwise
        """
        try:
            path_manager = get_path_manager()
            styled_path = path_manager.get_unreal_styled_images_path()

            if styled_path:
                return styled_path

            # Fallback to legacy construction
            unreal_path = path_manager.get_unreal_project_path()
            if unreal_path:
                return str(Path(unreal_path) / "Saved" / "Screenshots" / "styled")

            return None

        except Exception as e:
            logger.warning(f"PathManager failed for styled images path, using fallback: {e}")
            project_path = os.getenv('UNREAL_PROJECT_PATH')
            if project_path:
                return str(Path(project_path) / "Saved" / "Screenshots" / "styled")
            return None

    @staticmethod
    def get_legacy_reference_images_path(session_id: str = None) -> str:
        """
        Get reference images storage path, maintaining ReferenceStorage interface.

        Replaces: hardcoded "reference_images" or "reference_images/{session_id}"

        Args:
            session_id: Optional session ID for session-specific path

        Returns:
            str: Reference images path
        """
        try:
            path_manager = get_path_manager()

            if session_id:
                return path_manager.get_reference_session_path(session_id)
            else:
                return path_manager.get_reference_images_path()

        except Exception as e:
            logger.warning(f"PathManager failed for reference images path, using fallback: {e}")
            # Fallback to legacy hardcoded path
            if session_id:
                return f"reference_images/{session_id}"
            else:
                return "reference_images"

    @staticmethod
    def get_legacy_uid_storage_path() -> str:
        """
        Get UID storage path for uid_manager compatibility.

        Replaces: hardcoded "data_storage/uid/uid_state.json"

        Returns:
            str: UID storage directory path
        """
        try:
            path_manager = get_path_manager()
            return path_manager.get_uid_storage_path()

        except Exception as e:
            logger.warning(f"PathManager failed for UID storage path, using fallback: {e}")
            # Fallback to legacy hardcoded path
            return "data_storage/uid"


class ReferenceStorageAdapter:
    """
    Specific adapter for ReferenceStorage class migration.

    Allows ReferenceStorage to gradually migrate from hardcoded paths
    to centralized management without breaking existing functionality.
    """

    def __init__(self, base_storage_path: str = "reference_images"):
        """
        Initialize adapter maintaining ReferenceStorage constructor interface.

        Args:
            base_storage_path: Legacy base path parameter (maintained for compatibility)
        """
        self.legacy_base_path = base_storage_path
        self._use_centralized = True  # Feature flag for centralized paths

    def get_base_path(self) -> Path:
        """
        Get base storage path using adapter logic.

        Returns:
            Path: Base storage path (centralized or legacy)
        """
        if self._use_centralized:
            try:
                path_manager = get_path_manager()
                centralized_path = path_manager.get_reference_images_path()
                return Path(centralized_path)
            except Exception as e:
                logger.warning(f"Centralized reference path failed, using legacy: {e}")

        # Fallback to legacy hardcoded path
        return Path(self.legacy_base_path)

    def get_session_path(self, session_id: str) -> Path:
        """
        Get session storage path using adapter logic.

        Args:
            session_id: Session ID

        Returns:
            Path: Session storage path
        """
        if self._use_centralized:
            try:
                path_manager = get_path_manager()
                session_path = path_manager.get_reference_session_path(session_id)
                return Path(session_path)
            except Exception as e:
                logger.warning(f"Centralized session path failed, using legacy: {e}")

        # Fallback to legacy construction
        base_path = self.get_base_path()
        session_path = base_path / session_id
        session_path.mkdir(exist_ok=True)
        return session_path


class UidManagerAdapter:
    """
    Adapter for UID manager path migration.

    Maintains UID manager interfaces while migrating to centralized path management.
    """

    @staticmethod
    def get_uid_storage_file_path(filename: str = "uid_state.json") -> str:
        """
        Get full path for UID storage file.

        Args:
            filename: UID storage filename

        Returns:
            str: Full path to UID storage file
        """
        try:
            path_manager = get_path_manager()
            uid_dir = path_manager.get_uid_storage_path()
            return str(Path(uid_dir) / filename)

        except Exception as e:
            logger.warning(f"Centralized UID path failed, using legacy: {e}")
            # Fallback to legacy hardcoded path
            return f"data_storage/uid/{filename}"

    @staticmethod
    def get_reference_uid_storage_file_path(filename: str = "refer_uid_mappings.json") -> str:
        """
        Get full path for reference UID storage file.

        Args:
            filename: Reference UID storage filename

        Returns:
            str: Full path to reference UID storage file
        """
        try:
            path_manager = get_path_manager()
            uid_dir = path_manager.get_uid_storage_path()
            return str(Path(uid_dir) / filename)

        except Exception as e:
            logger.warning(f"Centralized reference UID path failed, using legacy: {e}")
            # Fallback to legacy hardcoded path
            return f"data_storage/uid/{filename}"


# Convenience functions for direct replacement in existing code
def get_unreal_project_path_safe() -> Optional[str]:
    """Safe replacement for os.getenv('UNREAL_PROJECT_PATH') with PathManager fallback."""
    return LegacyPathAdapter.get_legacy_unreal_project_path()


def get_screenshots_path_safe() -> Optional[str]:
    """Safe replacement for hardcoded screenshots path construction."""
    return LegacyPathAdapter.get_legacy_screenshots_path()


def get_styled_images_path_safe() -> Optional[str]:
    """Safe replacement for hardcoded styled images path construction."""
    return LegacyPathAdapter.get_legacy_styled_images_path()


def get_reference_images_path_safe(session_id: str = None) -> str:
    """Safe replacement for hardcoded reference images path construction."""
    return LegacyPathAdapter.get_legacy_reference_images_path(session_id)


def get_uid_storage_path_safe() -> str:
    """Safe replacement for hardcoded UID storage path construction."""
    return LegacyPathAdapter.get_legacy_uid_storage_path()


# Migration utilities
def enable_centralized_paths():
    """Enable centralized path management globally."""
    logger.info("Enabling centralized path management")


def disable_centralized_paths():
    """Disable centralized path management (fallback to legacy)."""
    logger.warning("Disabling centralized path management - using legacy paths")


def get_migration_status() -> Dict[str, Any]:
    """
    Get status of path centralization migration.

    Returns:
        Dict containing migration status information
    """
    try:
        path_manager = get_path_manager()
        path_info = path_manager.get_path_info()

        return {
            'centralized_paths_enabled': True,
            'path_manager_healthy': True,
            'resource_directories_exist': path_info.get('validation', {}).get('resource_directories_exist', False),
            'config': path_info.get('config', {}),
            'resource_directories': path_info.get('resource_directories', {})
        }

    except Exception as e:
        return {
            'centralized_paths_enabled': False,
            'path_manager_healthy': False,
            'error': str(e),
            'fallback_mode': True
        }