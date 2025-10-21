"""
PathManager utility for centralized path management in MegaMelange system.
Handles all path-related operations, validation, and configuration.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("PathManager")


@dataclass
class PathConfig:
    """Configuration class for path settings."""
    unreal_project_path: Optional[str] = None
    megamelange_base_path: Optional[str] = None
    fallback_enabled: bool = True
    create_directories: bool = True

    # Resource Management Configuration
    resource_base_path: Optional[str] = None
    reference_images_path: Optional[str] = None
    temp_cleanup_enabled: bool = True
    copy_on_access: bool = True  # Copy strategy vs move strategy
    enable_centralized_paths: bool = True  # Feature flag for rollback support


class PathManager:
    """
    Centralized path management for MegaMelange system.

    Handles:
    - Unreal Engine project path resolution
    - MegaMelange storage directory structure
    - Resource path management (images, videos, references)
    - Path validation and creation
    - Cross-platform path handling
    - Environment variable management
    - Copy/move strategy for resource migration
    """

    def __init__(self, config: Optional[PathConfig] = None):
        """
        Initialize PathManager with optional configuration.

        Args:
            config: PathConfig instance. If None, uses default configuration.
        """
        self.config = config or PathConfig()
        self._cached_paths: Dict[str, str] = {}

        logger.debug("PathManager initialized")

    def get_unreal_project_path(self) -> Optional[str]:
        """
        Get the Unreal Engine project path.

        Returns:
            str: Unreal project path if found, None otherwise
        """
        if 'unreal_project' in self._cached_paths:
            return self._cached_paths['unreal_project']

        # Priority order for path resolution
        sources = [
            ('config.unreal_project_path', self.config.unreal_project_path),
            ('UNREAL_PROJECT_PATH', os.getenv('UNREAL_PROJECT_PATH')),
            ('UE_PROJECT_PATH', os.getenv('UE_PROJECT_PATH')),  # Alternative env var
        ]

        for source_name, path in sources:
            if path and path.strip():
                path = path.strip()
                if self.validate_unreal_project_path(path):
                    self._cached_paths['unreal_project'] = path
                    logger.info(f"Unreal project path resolved from {source_name}: {path}")
                    return path
                else:
                    logger.warning(f"Invalid Unreal project path from {source_name}: {path}")

        logger.warning("No valid Unreal project path found")
        return None

    def validate_unreal_project_path(self, path: str) -> bool:
        """
        Validate if the given path is a valid Unreal Engine project directory.

        Args:
            path: Path to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not path or not path.strip():
            return False

        try:
            project_path = Path(path)

            # Check if directory exists
            if not project_path.exists() or not project_path.is_dir():
                return False

            # Look for .uproject files (indicates Unreal project)
            uproject_files = list(project_path.glob("*.uproject"))
            if uproject_files:
                logger.debug(f"Found .uproject file: {uproject_files[0].name}")
                return True

            # If no .uproject, check if it's a valid directory that could contain one
            # (for cases where we're setting up the project structure)
            if project_path.exists():
                logger.debug(f"Directory exists but no .uproject found: {path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error validating Unreal project path {path}: {e}")
            return False

    def get_megamelange_base_path(self) -> str:
        """
        Get the base MegaMelange storage path.

        Returns:
            str: MegaMelange base path

        Raises:
            RuntimeError: If unable to determine a valid path
        """
        if 'megamelange_base' in self._cached_paths:
            return self._cached_paths['megamelange_base']

        # Method 1: Explicit configuration
        if self.config.megamelange_base_path:
            base_path = self.config.megamelange_base_path
            logger.info(f"Using configured MegaMelange path: {base_path}")
        else:
            # Method 2: Use centralized data_storage path with PyInstaller compatibility
            import sys
            if getattr(sys, 'frozen', False):
                # Running as compiled executable (PyInstaller)
                executable_dir = Path(sys.executable).parent
                base_path = str(executable_dir / "data_storage" / "sessions")
                logger.info(f"Using executable-based sessions path (frozen): {base_path}")
            else:
                # Running as Python script
                python_dir = Path(__file__).parent.parent.parent  # Go up to Python/
                base_path = str(python_dir / "data_storage" / "sessions")
                logger.info(f"Using script-based sessions path (dev): {base_path}")

        # Validate and optionally create the path
        if self.config.create_directories:
            try:
                Path(base_path).mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured MegaMelange base directory exists: {base_path}")
            except Exception as e:
                logger.error(f"Failed to create MegaMelange directory {base_path}: {e}")
                raise RuntimeError(f"Failed to create MegaMelange directory: {e}")

        self._cached_paths['megamelange_base'] = base_path
        return base_path

    def get_sessions_directory(self) -> str:
        """Get the sessions directory path."""
        return self.get_megamelange_base_path()  # Already points to data_storage/sessions

    def get_active_sessions_directory(self) -> str:
        """Get the active sessions directory path."""
        return os.path.join(self.get_sessions_directory(), 'active')

    def get_archived_sessions_directory(self) -> str:
        """Get the archived sessions directory path."""
        return os.path.join(self.get_sessions_directory(), 'archived')

    def get_metadata_directory(self) -> str:
        """Get the metadata directory path."""
        return os.path.join(self.get_sessions_directory(), 'metadata')

    def get_logs_directory(self) -> str:
        """Get the logs directory path."""
        return os.path.join(self.get_megamelange_base_path(), 'logs')

    def get_session_index_file(self) -> str:
        """Get the session index file path."""
        return os.path.join(self.get_metadata_directory(), 'session_index.json')

    def get_stats_file(self) -> str:
        """Get the statistics file path."""
        return os.path.join(self.get_metadata_directory(), 'stats.json')

    def get_session_file_path(self, session_id: str, created_at = None) -> str:
        """
        Get the full file path for a session.

        Args:
            session_id: Session ID
            created_at: Session creation datetime (optional)

        Returns:
            str: Full path to session file
        """
        from datetime import datetime

        if created_at is None:
            created_at = datetime.now()

        # Organize by year-month and day
        year_month = created_at.strftime("%Y-%m")
        day = created_at.strftime("day-%d")

        session_dir = os.path.join(self.get_active_sessions_directory(), year_month, day)

        # Create directory if needed
        if self.config.create_directories:
            Path(session_dir).mkdir(parents=True, exist_ok=True)

        return os.path.join(session_dir, f"session_{session_id}.json")

    # ===== RESOURCE PATH MANAGEMENT =====
    # New methods for centralized resource path management

    def get_data_storage_path(self) -> str:
        """
        Get the centralized data storage path.

        Returns:
            str: Data storage base path
        """
        if 'data_storage' in self._cached_paths:
            return self._cached_paths['data_storage']

        if self.config.resource_base_path:
            base_path = self.config.resource_base_path
            logger.info(f"Using configured resource base path: {base_path}")
        else:
            # For PyInstaller compatibility: use executable directory
            import sys
            if getattr(sys, 'frozen', False):
                # Running as compiled executable (PyInstaller)
                executable_dir = Path(sys.executable).parent
                base_path = str(executable_dir / "data_storage")
                logger.info(f"Using executable-based data storage path (frozen): {base_path}")
            else:
                # Running as Python script
                python_dir = Path(__file__).parent.parent.parent  # Go up to Python/
                base_path = str(python_dir / "data_storage")
                logger.info(f"Using script-based data storage path (dev): {base_path}")

        if self.config.create_directories:
            Path(base_path).mkdir(parents=True, exist_ok=True)

        self._cached_paths['data_storage'] = base_path
        return base_path

    def get_uid_storage_path(self) -> str:
        """Get the UID storage directory path."""
        uid_path = os.path.join(self.get_data_storage_path(), 'uid')

        if self.config.create_directories:
            Path(uid_path).mkdir(parents=True, exist_ok=True)

        return uid_path

    def get_reference_images_path(self) -> str:
        """
        Get the reference images storage base path.

        Returns:
            str: Reference images base path (assets/images/references)
        """
        if 'reference_images' in self._cached_paths:
            return self._cached_paths['reference_images']

        if self.config.reference_images_path:
            ref_path = self.config.reference_images_path
            logger.debug(f"Using configured reference images path: {ref_path}")
        else:
            # Default to assets/images/references for better organization
            ref_path = os.path.join(self.get_data_storage_path(), 'assets', 'images', 'references')
            logger.debug(f"Using default reference images path: {ref_path}")

        if self.config.create_directories:
            Path(ref_path).mkdir(parents=True, exist_ok=True)

        self._cached_paths['reference_images'] = ref_path
        return ref_path

    def get_generated_images_path(self) -> str:
        """
        Get the generated/styled images storage path.

        Returns:
            str: Generated images path (assets/images/generated)
        """
        if 'generated_images' in self._cached_paths:
            return self._cached_paths['generated_images']

        # Default to assets/images/generated for AI-generated images
        gen_path = os.path.join(self.get_data_storage_path(), 'assets', 'images', 'generated')
        logger.debug(f"Using generated images path: {gen_path}")

        if self.config.create_directories:
            Path(gen_path).mkdir(parents=True, exist_ok=True)

        self._cached_paths['generated_images'] = gen_path
        return gen_path

    def get_videos_path(self) -> str:
        """
        Get the videos storage path.

        Returns:
            str: Videos path (assets/videos)
        """
        if 'videos' in self._cached_paths:
            return self._cached_paths['videos']

        # Default to assets/videos
        videos_path = os.path.join(self.get_data_storage_path(), 'assets', 'videos')
        logger.debug(f"Using videos path: {videos_path}")

        if self.config.create_directories:
            Path(videos_path).mkdir(parents=True, exist_ok=True)

        self._cached_paths['videos'] = videos_path
        return videos_path

    def get_3d_objects_path(self) -> str:
        """
        Get the 3D objects storage base path.

        Returns:
            str: 3D objects base storage path (assets/objects3d/obj)
        """
        if 'object_3d' in self._cached_paths:
            return self._cached_paths['object_3d']

        # Use assets/objects3d/obj path for better asset organization
        objects_path = os.path.join(self.get_data_storage_path(), 'assets', 'objects3d', 'obj')

        if self.config.create_directories:
            Path(objects_path).mkdir(parents=True, exist_ok=True)

        self._cached_paths['object_3d'] = objects_path
        return objects_path

    def get_3d_object_uid_path(self, uid: str, session_id: Optional[str] = None) -> str:
        """
        Get the path for a specific 3D object UID.

        Assets structure:
        - OBJ format: assets/objects3d/obj/uid/
        - FBX format: assets/objects3d/fbx/uid/

        Each object gets its own directory containing mesh files, textures, and metadata.
        Session information is stored in metadata, not directory structure.

        Args:
            uid: Object UID (e.g., obj_001 or fbx_001)
            session_id: Optional session ID (stored in metadata, not used for path)

        Returns:
            str: Path to the specific object directory
        """
        # Detect format from UID prefix
        if uid.startswith('fbx_'):
            format_dir = 'fbx'
        elif uid.startswith('obj_'):
            format_dir = 'obj'
        else:
            # Default to obj for backwards compatibility
            format_dir = 'obj'

        # Build path: assets/objects3d/{format}/uid/
        base_storage = self.get_data_storage_path()
        object_path = os.path.join(base_storage, 'assets', 'objects3d', format_dir, uid)

        if self.config.create_directories:
            Path(object_path).mkdir(parents=True, exist_ok=True)

        return object_path


    def get_unreal_saved_directory(self) -> Optional[str]:
        """
        Get the Unreal Engine Saved directory path.

        Returns:
            str: Unreal Saved directory path if project found, None otherwise
        """
        unreal_path = self.get_unreal_project_path()
        if not unreal_path:
            return None

        saved_path = os.path.join(unreal_path, 'Saved')
        return saved_path if Path(saved_path).exists() else None

    def get_unreal_screenshots_path(self) -> Optional[str]:
        """
        Get the Unreal Engine Screenshots directory path.

        Returns:
            str: Screenshots directory path if available, None otherwise
        """
        saved_path = self.get_unreal_saved_directory()
        if not saved_path:
            return None

        screenshots_path = os.path.join(saved_path, 'Screenshots', 'WindowsEditor')
        return screenshots_path

    def get_unreal_styled_images_path(self) -> Optional[str]:
        """
        Get the path for styled/processed images within Unreal project.

        Returns:
            str: Styled images directory path if available, None otherwise
        """
        saved_path = self.get_unreal_saved_directory()
        if not saved_path:
            return None

        styled_path = os.path.join(saved_path, 'Screenshots', 'styled')

        # Create styled directory if it doesn't exist
        if self.config.create_directories:
            Path(styled_path).mkdir(parents=True, exist_ok=True)

        return styled_path

    def get_temp_processing_path(self) -> str:
        """
        Get temporary processing directory for resource operations.

        Returns:
            str: Temporary processing path
        """
        if 'temp_processing' in self._cached_paths:
            return self._cached_paths['temp_processing']

        temp_path = os.path.join(self.get_data_storage_path(), 'temp', 'processing')

        if self.config.create_directories:
            Path(temp_path).mkdir(parents=True, exist_ok=True)

        self._cached_paths['temp_processing'] = temp_path
        return temp_path

    def copy_resource_to_centralized(self, source_path: str, resource_type: str, target_name: str = None) -> Optional[str]:
        """
        Copy a resource to centralized storage using copy strategy.

        Args:
            source_path: Original resource path
            resource_type: Type of resource ('uid', 'reference', 'screenshot', 'temp')
            target_name: Optional target filename

        Returns:
            str: New centralized path if successful, None otherwise
        """
        if not self.config.copy_on_access or not self.config.enable_centralized_paths:
            return source_path  # Return original path if centralization disabled

        try:
            source = Path(source_path)
            if not source.exists():
                logger.warning(f"Source resource not found: {source_path}")
                return None

            # Determine target directory based on resource type
            if resource_type == 'uid':
                target_dir = self.get_uid_storage_path()
            elif resource_type == 'reference':
                target_dir = self.get_reference_images_path()
            elif resource_type == '3d_objects':
                target_dir = self.get_3d_objects_path()
            elif resource_type == 'screenshot':
                target_dir = self.get_unreal_screenshots_path() or self.get_temp_processing_path()
            elif resource_type == 'temp':
                target_dir = self.get_temp_processing_path()
            else:
                logger.error(f"Unknown resource type: {resource_type}")
                return None

            # Determine target filename
            target_filename = target_name or source.name
            target_path = Path(target_dir) / target_filename

            # Copy file if it doesn't already exist
            if not target_path.exists():
                import shutil
                shutil.copy2(source, target_path)
                logger.info(f"Copied resource {resource_type}: {source_path} → {target_path}")

            return str(target_path)

        except Exception as e:
            logger.error(f"Failed to copy resource {source_path}: {e}")
            return None

    def cleanup_temp_resources(self, max_age_hours: int = 24) -> bool:
        """
        Clean up temporary resources based on age.

        Args:
            max_age_hours: Maximum age in hours before cleanup

        Returns:
            bool: True if cleanup succeeded, False otherwise
        """
        if not self.config.temp_cleanup_enabled:
            return True  # Skip cleanup if disabled

        try:
            temp_path = Path(self.get_temp_processing_path())
            if not temp_path.exists():
                return True  # Nothing to clean

            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            cleaned_count = 0
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} temporary files older than {max_age_hours} hours")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup temp resources: {e}")
            return False

    def sync_resource_directories(self) -> bool:
        """
        Synchronize resource directories between original and centralized locations.

        Returns:
            bool: True if sync succeeded, False otherwise
        """
        if not self.config.enable_centralized_paths:
            return True  # Skip sync if centralization disabled

        try:
            # Ensure all centralized directories exist
            directories = [
                self.get_data_storage_path(),
                self.get_uid_storage_path(),
                self.get_reference_images_path(),
                self.get_3d_objects_path(),
                self.get_temp_processing_path()
            ]

            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)

            logger.info("Resource directory synchronization completed")
            return True

        except Exception as e:
            logger.error(f"Failed to sync resource directories: {e}")
            return False

    def ensure_directory_structure(self) -> bool:
        """
        Ensure all required MegaMelange directories exist.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            directories = [
                self.get_sessions_directory(),
                self.get_active_sessions_directory(),
                self.get_archived_sessions_directory(),
                self.get_metadata_directory(),
                self.get_logs_directory()
            ]

            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory}")

            logger.info("MegaMelange directory structure ensured")
            return True

        except Exception as e:
            logger.error(f"Failed to ensure directory structure: {e}")
            return False

    def save_generated_image(
        self,
        image_data: bytes,
        filename: str,
        source: str = "nano_banana"
    ) -> str:
        """
        Save generated image to data_storage/assets/images/generated/.

        Centralized image storage method for all image generation tools.

        Args:
            image_data: Raw image bytes to save
            filename: Target filename (e.g., "img_001_20250112.png")
            source: Source identifier (nano_banana, veo, etc.) for logging

        Returns:
            str: Absolute path to saved file

        Raises:
            AppError: If unable to determine path or save file
        """
        try:
            from core.errors import AppError, ErrorCategory

            # Get generated images directory path
            generated_dir = self.get_generated_images_path()
            if not generated_dir:
                raise AppError(
                    code="IMG_PATH_ERROR",
                    message="Unable to determine generated images directory path",
                    category=ErrorCategory.INTERNAL_SERVER,
                    suggestion="Check data_storage configuration"
                )

            # Create directory if needed
            generated_path = Path(generated_dir)
            generated_path.mkdir(parents=True, exist_ok=True)

            # Save file
            file_path = generated_path / filename
            with open(file_path, 'wb') as f:
                f.write(image_data)

            logger.info(f"Generated image saved: {filename} (source: {source}, size: {len(image_data)} bytes)")
            return str(file_path)

        except AppError:
            raise  # Re-raise AppError as-is
        except Exception as e:
            from core.errors import AppError, ErrorCategory
            logger.error(f"Failed to save generated image: {e}")
            raise AppError(
                code="IMG_SAVE_FAILED",
                message=f"Failed to save generated image: {str(e)}",
                category=ErrorCategory.INTERNAL_SERVER,
                suggestion="Check file permissions and storage space"
            )

    def get_path_info(self) -> Dict[str, Any]:
        """
        Get comprehensive path information for debugging and monitoring.

        Returns:
            Dict containing all path information
        """
        try:
            unreal_path = self.get_unreal_project_path()
            megamelange_path = self.get_megamelange_base_path()

            return {
                'unreal_project_path': unreal_path,
                'megamelange_base_path': megamelange_path,
                'path_derivation': 'from_unreal_project' if unreal_path else 'fallback',
                'directories': {
                    'sessions': self.get_sessions_directory(),
                    'active': self.get_active_sessions_directory(),
                    'archived': self.get_archived_sessions_directory(),
                    'metadata': self.get_metadata_directory(),
                    'logs': self.get_logs_directory()
                },
                'resource_directories': {
                    'data_storage': self.get_data_storage_path(),
                    'uid_storage': self.get_uid_storage_path(),
                    'reference_images': self.get_reference_images_path(),
                    '3d_objects': self.get_3d_objects_path(),
                    'temp_processing': self.get_temp_processing_path(),
                    'unreal_saved': self.get_unreal_saved_directory(),
                    'unreal_screenshots': self.get_unreal_screenshots_path(),
                    'unreal_styled': self.get_unreal_styled_images_path()
                },
                'key_files': {
                    'session_index': self.get_session_index_file(),
                    'stats': self.get_stats_file()
                },
                'validation': {
                    'unreal_path_valid': self.validate_unreal_project_path(unreal_path) if unreal_path else False,
                    'megamelange_path_exists': Path(megamelange_path).exists(),
                    'directories_exist': all(Path(d).exists() for d in [
                        self.get_sessions_directory(),
                        self.get_active_sessions_directory(),
                        self.get_archived_sessions_directory(),
                        self.get_metadata_directory(),
                        self.get_logs_directory()
                    ]),
                    'resource_directories_exist': all(Path(d).exists() if d else True for d in [
                        self.get_data_storage_path(),
                        self.get_uid_storage_path(),
                        self.get_reference_images_path(),
                        self.get_3d_objects_path(),
                        self.get_temp_processing_path(),
                        self.get_unreal_saved_directory(),
                        self.get_unreal_screenshots_path(),
                        self.get_unreal_styled_images_path()
                    ])
                },
                'config': {
                    'fallback_enabled': self.config.fallback_enabled,
                    'create_directories': self.config.create_directories,
                    'configured_unreal_path': self.config.unreal_project_path,
                    'configured_megamelange_path': self.config.megamelange_base_path,
                    'resource_base_path': self.config.resource_base_path,
                    'reference_images_path': self.config.reference_images_path,
                    'copy_on_access': self.config.copy_on_access,
                    'temp_cleanup_enabled': self.config.temp_cleanup_enabled,
                    'enable_centralized_paths': self.config.enable_centralized_paths
                }
            }

        except Exception as e:
            logger.error(f"Error getting path info: {e}")
            return {'error': str(e)}

    def clear_cache(self):
        """Clear the internal path cache to force re-resolution."""
        self._cached_paths.clear()
        logger.debug("Path cache cleared")

    def health_check(self) -> bool:
        """
        Perform a health check on the path management system.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Test path resolution
            unreal_path = self.get_unreal_project_path()
            megamelange_path = self.get_megamelange_base_path()

            # Test directory creation
            if self.config.create_directories:
                self.ensure_directory_structure()
                self.sync_resource_directories()

            # Test resource path resolution
            data_storage = self.get_data_storage_path()
            uid_storage = self.get_uid_storage_path()
            reference_images = self.get_reference_images_path()
            objects_3d = self.get_3d_objects_path()
            temp_processing = self.get_temp_processing_path()

            # Test file operations
            test_file = Path(self.get_metadata_directory()) / "health_check.tmp"
            test_file.write_text("health check", encoding='utf-8')
            test_file.unlink()

            # Test temp cleanup functionality
            if self.config.temp_cleanup_enabled:
                self.cleanup_temp_resources(0.001)  # Clean very old files (test mode)

            logger.debug("PathManager health check passed (including resource paths)")
            return True

        except Exception as e:
            logger.error(f"PathManager health check failed: {e}")
            return False


# Global PathManager instance
_global_path_manager: Optional[PathManager] = None


def get_path_manager(config: Optional[PathConfig] = None) -> PathManager:
    """
    Get or create the global PathManager instance.

    Args:
        config: Optional PathConfig. Only used if creating new instance.

    Returns:
        PathManager instance
    """
    global _global_path_manager

    if _global_path_manager is None:
        _global_path_manager = PathManager(config)
        logger.info("Global PathManager initialized")

    return _global_path_manager


def reset_path_manager():
    """Reset the global PathManager instance (mainly for testing)."""
    global _global_path_manager
    _global_path_manager = None
    logger.debug("Global PathManager reset")
