"""
PathManager utility for centralized path management in MegaMelange session system.
Handles all path-related operations, validation, and configuration.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("SessionManager.PathManager")


@dataclass
class PathConfig:
    """Configuration class for path settings."""
    unreal_project_path: Optional[str] = None
    megamelange_base_path: Optional[str] = None
    fallback_enabled: bool = True
    create_directories: bool = True


class PathManager:
    """
    Centralized path management for MegaMelange session system.
    
    Handles:
    - Unreal Engine project path resolution
    - MegaMelange storage directory structure
    - Path validation and creation
    - Cross-platform path handling
    - Environment variable management
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
            # Method 2: Derive from Unreal project path
            unreal_path = self.get_unreal_project_path()
            if unreal_path:
                base_path = os.path.join(unreal_path, 'Saved', 'MegaMelange')
                logger.info(f"Derived MegaMelange path from Unreal project: {base_path}")
            else:
                # Method 3: Fallback path
                if self.config.fallback_enabled:
                    base_path = os.path.join('.', 'Saved', 'MegaMelange')
                    logger.warning(f"Using fallback MegaMelange path: {base_path}")
                else:
                    raise RuntimeError("Unable to determine MegaMelange path and fallback is disabled")
        
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
        return os.path.join(self.get_megamelange_base_path(), 'sessions')
    
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
                    ])
                },
                'config': {
                    'fallback_enabled': self.config.fallback_enabled,
                    'create_directories': self.config.create_directories,
                    'configured_unreal_path': self.config.unreal_project_path,
                    'configured_megamelange_path': self.config.megamelange_base_path
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
            
            # Test file operations
            test_file = Path(self.get_metadata_directory()) / "health_check.tmp"
            test_file.write_text("health check", encoding='utf-8')
            test_file.unlink()
            
            logger.debug("PathManager health check passed")
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