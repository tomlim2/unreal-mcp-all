#!/usr/bin/env python3
"""
Unreal Engine Path Utilities

Common utilities for resolving Unreal Engine project paths and directories.
Provides centralized path resolution logic for screenshots, project files, etc.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger("UnrealPathUtils")

class UnrealPathResolver:
    """Centralized Unreal Engine path resolution utility."""
    
    def __init__(self):
        self._project_path_cache: Optional[Path] = None
        
    def get_project_path(self) -> Optional[Path]:
        """Get the Unreal Engine project root directory."""
        if self._project_path_cache and self._project_path_cache.exists():
            return self._project_path_cache
            
        # Method 1: Use UNREAL_PROJECT_PATH environment variable
        unreal_project_path = os.getenv("UNREAL_PROJECT_PATH")
        if unreal_project_path:
            project_path = Path(unreal_project_path)
            if project_path.exists() and project_path.is_dir():
                # Verify it's actually a UE project by looking for .uproject file
                if list(project_path.glob("*.uproject")):
                    logger.info(f"Found project using UNREAL_PROJECT_PATH: {project_path}")
                    self._project_path_cache = project_path
                    return project_path
        
        # Method 2: Auto-discovery - search for .uproject files
        current_dir = Path(__file__).parent.parent  # Go up from tools/ to Python/
        for search_path in [current_dir, current_dir.parent]:
            # Look for .uproject files in current directory
            uproject_files = list(search_path.glob("*.uproject"))
            if uproject_files:
                project_dir = uproject_files[0].parent
                logger.info(f"Found project using auto-discovery: {project_dir}")
                self._project_path_cache = project_dir
                return project_dir
            
            # Look for subdirectories with .uproject files
            try:
                for subdir in search_path.iterdir():
                    if subdir.is_dir():
                        uproject_files = list(subdir.glob("*.uproject"))
                        if uproject_files:
                            project_dir = uproject_files[0].parent
                            logger.info(f"Found project using auto-discovery in {subdir}: {project_dir}")
                            self._project_path_cache = project_dir
                            return project_dir
            except (OSError, PermissionError):
                # Skip directories we can't read
                continue
        
        logger.warning("Could not auto-discover Unreal project path")
        return None
    
    def get_screenshots_dir(self, include_platform_subfolder: bool = True) -> Optional[Path]:
        """Get the screenshots directory path.
        
        Args:
            include_platform_subfolder: If True, includes WindowsEditor/etc subfolder where HighResShot saves
        """
        project_path = self.get_project_path()
        if not project_path:
            return None
            
        screenshots_base = project_path / "Saved" / "Screenshots"
        
        if include_platform_subfolder:
            # Try platform-specific subfolder first (where HighResShot saves)
            platform_subfolders = ["WindowsEditor", "Windows", "Editor"]
            for subfolder in platform_subfolders:
                platform_dir = screenshots_base / subfolder
                if platform_dir.exists():
                    return platform_dir
            
            # If no platform subfolder exists, return base (it will be created as needed)
            return screenshots_base / "WindowsEditor"
        
        return screenshots_base
    
    def find_screenshot_file(self, filename: str, search_subfolders: bool = True) -> Optional[Path]:
        """Find a screenshot file by name.
        
        Args:
            filename: The screenshot filename to find
            search_subfolders: If True, searches both platform subfolders and base directory
        """
        project_path = self.get_project_path()
        if not project_path:
            return None
            
        screenshots_base = project_path / "Saved" / "Screenshots"
        
        search_paths = []
        
        if search_subfolders:
            # Check platform-specific subfolders first
            platform_subfolders = ["WindowsEditor", "Windows", "Editor"]
            for subfolder in platform_subfolders:
                search_paths.append(screenshots_base / subfolder / filename)
        
        # Also check base screenshots directory
        search_paths.append(screenshots_base / filename)
        
        # Return first existing file
        for path in search_paths:
            if path.exists() and path.is_file():
                logger.info(f"Found screenshot: {path}")
                return path
        
        return None
    
    def get_saved_dir(self, subdirectory: Optional[str] = None) -> Optional[Path]:
        """Get a path within the Saved directory.
        
        Args:
            subdirectory: Optional subdirectory within Saved (e.g., "Screenshots", "Logs")
        """
        project_path = self.get_project_path()
        if not project_path:
            return None
            
        saved_dir = project_path / "Saved"
        
        if subdirectory:
            return saved_dir / subdirectory
        
        return saved_dir
    
    def clear_cache(self):
        """Clear the cached project path (useful for testing or if project changes)."""
        self._project_path_cache = None

# Global singleton instance
_path_resolver = UnrealPathResolver()

# Convenience functions using the global resolver
def get_unreal_project_path() -> Optional[Path]:
    """Get the Unreal Engine project root directory."""
    return _path_resolver.get_project_path()

def get_unreal_screenshots_dir(include_platform_subfolder: bool = True) -> Optional[Path]:
    """Get the screenshots directory path."""
    return _path_resolver.get_screenshots_dir(include_platform_subfolder)

def find_unreal_screenshot(filename: str, search_subfolders: bool = True) -> Optional[Path]:
    """Find a screenshot file by name."""
    return _path_resolver.find_screenshot_file(filename, search_subfolders)

def get_unreal_saved_dir(subdirectory: Optional[str] = None) -> Optional[Path]:
    """Get a path within the Saved directory."""
    return _path_resolver.get_saved_dir(subdirectory)

def clear_unreal_path_cache():
    """Clear the cached project path."""
    _path_resolver.clear_cache()