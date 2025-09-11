"""
Utility functions for image management system.
"""

import os
import shutil
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from PIL import Image

logger = logging.getLogger("ImageManager.Utils")


class ImageUtils:
    """Utility functions for image file operations."""
    
    @staticmethod
    def generate_image_id(prefix: str = "img", timestamp: datetime = None) -> str:
        """
        Generate a unique image ID based on timestamp.
        
        Args:
            prefix: Prefix for the ID (default: "img")
            timestamp: Timestamp to use (default: now)
            
        Returns:
            Unique image ID like "img_20250911_215503"
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Format: img_YYYYMMDD_HHMMSS
        time_str = timestamp.strftime('%Y%m%d_%H%M%S')
        
        # Add milliseconds for uniqueness
        ms = timestamp.microsecond // 1000
        return f"{prefix}_{time_str}_{ms:03d}"
    
    @staticmethod
    def get_file_hash(file_path: Path) -> Optional[str]:
        """
        Calculate SHA-256 hash of a file for deduplication.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash string or None if error
        """
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def get_image_dimensions(file_path: Path) -> Optional[Tuple[int, int]]:
        """
        Get image dimensions (width, height).
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Tuple of (width, height) or None if error
        """
        try:
            with Image.open(file_path) as img:
                return img.size
        except Exception as e:
            logger.error(f"Failed to get dimensions for {file_path}: {e}")
            return None
    
    @staticmethod
    def copy_image_to_registry(source_path: Path, target_path: Path) -> bool:
        """
        Copy an image file to the registry directory.
        
        Args:
            source_path: Source file path
            target_path: Target file path in registry
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, target_path)
            
            logger.debug(f"Copied image: {source_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy image {source_path} -> {target_path}: {e}")
            return False
    
    @staticmethod
    def move_image_to_registry(source_path: Path, target_path: Path) -> bool:
        """
        Move an image file to the registry directory.
        
        Args:
            source_path: Source file path
            target_path: Target file path in registry
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source_path), str(target_path))
            
            logger.debug(f"Moved image: {source_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move image {source_path} -> {target_path}: {e}")
            return False
    
    @staticmethod
    def get_image_info(file_path: Path) -> Dict[str, Any]:
        """
        Get comprehensive information about an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with image information
        """
        info = {
            'file_path': str(file_path),
            'exists': file_path.exists(),
            'file_size': None,
            'dimensions': None,
            'file_hash': None,
            'format': None,
            'mode': None
        }
        
        if not file_path.exists():
            return info
        
        try:
            # Basic file info
            stat = file_path.stat()
            info['file_size'] = stat.st_size
            info['modified_time'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Image-specific info
            with Image.open(file_path) as img:
                info['dimensions'] = img.size
                info['format'] = img.format
                info['mode'] = img.mode
            
            # File hash for deduplication
            info['file_hash'] = ImageUtils.get_file_hash(file_path)
            
        except Exception as e:
            logger.warning(f"Failed to get complete info for {file_path}: {e}")
        
        return info
    
    @staticmethod
    def is_valid_image_file(file_path: Path) -> bool:
        """
        Check if a file is a valid image.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if valid image, False otherwise
        """
        if not file_path.exists():
            return False
        
        try:
            with Image.open(file_path) as img:
                img.verify()  # Verify it's a valid image
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_relative_image_url(image_id: str, is_transformation: bool = False) -> str:
        """
        Generate relative URL for an image based on ID and type.
        
        Args:
            image_id: Image ID
            is_transformation: Whether this is a transformation image
            
        Returns:
            Relative URL like "/images/files/screenshots/img_123.png"
        """
        subfolder = "styled" if is_transformation else "screenshots"
        
        # Default to PNG extension (could be improved to detect actual format)
        return f"/images/files/{subfolder}/{image_id}.png"
    
    @staticmethod
    def resolve_image_file_path(image_id: str, is_transformation: bool, images_dir: Path) -> Path:
        """
        Resolve the actual file path for an image ID.
        
        Args:
            image_id: Image ID
            is_transformation: Whether this is a transformation image
            images_dir: Base images directory
            
        Returns:
            Path to the image file
        """
        subfolder = "styled" if is_transformation else "screenshots"
        files_dir = images_dir / "files" / subfolder
        
        # Try different extensions
        for ext in ['.png', '.jpg', '.jpeg']:
            file_path = files_dir / f"{image_id}{ext}"
            if file_path.exists():
                return file_path
        
        # Default to PNG if not found
        return files_dir / f"{image_id}.png"
    
    @staticmethod
    def cleanup_temp_files(temp_dir: Path, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified age.
        
        Args:
            temp_dir: Directory to clean
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files deleted
        """
        if not temp_dir.exists():
            return 0
        
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        try:
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    if stat.st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                            logger.debug(f"Deleted temp file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete temp file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to cleanup temp directory {temp_dir}: {e}")
        
        return deleted_count