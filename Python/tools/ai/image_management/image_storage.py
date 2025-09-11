"""
File-based storage backend for image registry using JSON files.
Follows the same pattern as session management file storage.
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from threading import Lock

from .models import ImageRecord, ImageBatch
from ..session_management.utils.path_manager import get_path_manager, PathManager

logger = logging.getLogger("ImageManager.FileStorage")


class ImageStorage:
    """
    File-based storage for image registry using organized JSON files.
    
    Directory Structure:
    {PROJECT_PATH}/Saved/MegaMelange/
    ├── images/                      # NEW: Image registry files
    │   ├── registry/                # Image metadata registry
    │   │   ├── 2025-09/            # Year-month folders
    │   │   │   ├── day-11/         # Day folders  
    │   │   │   │   ├── images_2025091121.json
    │   │   │   │   └── images_2025091122.json
    │   │   │   └── day-12/
    │   │   └── 2025-10/
    │   ├── index/                   # Fast lookup indexes
    │   │   ├── image_index.json    # image_id -> file mapping
    │   │   ├── session_index.json  # session_id -> images mapping
    │   │   └── stats.json          # Usage statistics
    │   └── files/                   # Actual image files (organized)
    │       ├── screenshots/        # Original screenshots
    │       └── styled/             # Styled transformations
    └── sessions/                   # Existing session files
    """
    
    def __init__(self, path_manager: PathManager = None):
        """Initialize image storage with directory structure."""
        self._lock = Lock()  # Thread safety for file operations
        
        # Initialize path manager
        if path_manager is None:
            self.path_manager = get_path_manager()
        else:
            self.path_manager = path_manager
        
        # Get base path from path manager
        base_path = self.path_manager.get_megamelange_base_path()
        self.base_path = Path(base_path)
        
        # Define image directory structure
        self.images_dir = self.base_path / "images"
        self.registry_dir = self.images_dir / "registry"
        self.index_dir = self.images_dir / "index"
        self.files_dir = self.images_dir / "files"
        self.screenshots_dir = self.files_dir / "screenshots"
        self.styled_dir = self.files_dir / "styled"
        
        # Ensure directory structure exists
        self._ensure_directories()
        
        # Initialize indexes
        self.image_index_file = self.index_dir / "image_index.json"
        self.session_index_file = self.index_dir / "session_index.json"
        self.stats_file = self.index_dir / "stats.json"
        
        self._load_or_create_indexes()
        
        logger.info(f"ImageStorage initialized with base path: {self.base_path}")
    
    def _ensure_directories(self):
        """Create required directories if they don't exist."""
        directories = [
            self.images_dir,
            self.registry_dir,
            self.index_dir,
            self.files_dir,
            self.screenshots_dir,
            self.styled_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_or_create_indexes(self):
        """Load or create index files for fast lookups."""
        try:
            # Image index: image_id -> file location
            if self.image_index_file.exists():
                with open(self.image_index_file, 'r', encoding='utf-8') as f:
                    self.image_index = json.load(f)
            else:
                self.image_index = {}
            
            # Session index: session_id -> list of image_ids
            if self.session_index_file.exists():
                with open(self.session_index_file, 'r', encoding='utf-8') as f:
                    self.session_index = json.load(f)
            else:
                self.session_index = {}
            
            self._save_indexes()
            
        except Exception as e:
            logger.warning(f"Failed to load indexes, creating new: {e}")
            self.image_index = {}
            self.session_index = {}
    
    def _save_indexes(self):
        """Save index files."""
        try:
            with open(self.image_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.image_index, f, indent=2, default=str)
            
            with open(self.session_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_index, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save indexes: {e}")
    
    def _get_batch_file_path(self, created_at: datetime = None) -> Path:
        """
        Get the file path for storing image batch based on creation date.
        
        Args:
            created_at: Creation datetime (defaults to now)
            
        Returns:
            Path to the batch file
        """
        if created_at is None:
            created_at = datetime.now()
        
        # Create year-month and day directories
        year_month = created_at.strftime('%Y-%m')
        day = f"day-{created_at.strftime('%d')}"
        hour = created_at.strftime('%H')
        
        batch_dir = self.registry_dir / year_month / day
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate batch filename with hour for better organization
        batch_filename = f"images_{created_at.strftime('%Y%m%d%H')}.json"
        return batch_dir / batch_filename
    
    def _find_image_batch_file(self, image_id: str) -> Optional[Path]:
        """Find the batch file containing a specific image."""
        # Check index first
        if image_id in self.image_index:
            batch_file_path = self.base_path / self.image_index[image_id]['batch_file']
            if batch_file_path.exists():
                return batch_file_path
            else:
                # Index is stale, remove entry
                del self.image_index[image_id]
                self._save_indexes()
        
        # Fallback: search through batch files
        for year_month_dir in self.registry_dir.iterdir():
            if not year_month_dir.is_dir():
                continue
            for day_dir in year_month_dir.iterdir():
                if not day_dir.is_dir():
                    continue
                for batch_file in day_dir.glob("images_*.json"):
                    try:
                        with open(batch_file, 'r', encoding='utf-8') as f:
                            batch_data = json.load(f)
                        
                        if image_id in batch_data.get('images', {}):
                            # Update index
                            relative_path = batch_file.relative_to(self.base_path)
                            self.image_index[image_id] = {
                                'batch_file': str(relative_path),
                                'last_accessed': datetime.now().isoformat()
                            }
                            self._save_indexes()
                            return batch_file
                    except Exception as e:
                        logger.warning(f"Failed to read batch file {batch_file}: {e}")
        
        return None
    
    def register_image(self, image_record: ImageRecord) -> bool:
        """Register a new image in the storage."""
        with self._lock:
            try:
                # Get or create batch file for this time period
                batch_file_path = self._get_batch_file_path(image_record.created_at)
                
                # Load existing batch or create new one
                if batch_file_path.exists():
                    with open(batch_file_path, 'r', encoding='utf-8') as f:
                        batch_data = json.load(f)
                    image_batch = ImageBatch.from_dict(batch_data)
                else:
                    image_batch = ImageBatch(batch_created_at=datetime.now())
                
                # Add image to batch
                image_batch.add_image(image_record)
                
                # Save batch file
                with open(batch_file_path, 'w', encoding='utf-8') as f:
                    json.dump(image_batch.to_dict(), f, indent=2, default=str)
                
                # Update indexes
                relative_batch_path = batch_file_path.relative_to(self.base_path)
                self.image_index[image_record.image_id] = {
                    'batch_file': str(relative_batch_path),
                    'last_accessed': datetime.now().isoformat()
                }
                
                # Update session index
                session_id = image_record.session_id
                if session_id not in self.session_index:
                    self.session_index[session_id] = []
                
                if image_record.image_id not in self.session_index[session_id]:
                    self.session_index[session_id].append(image_record.image_id)
                
                self._save_indexes()
                
                # Update statistics
                self._update_stats('images_registered')
                
                logger.info(f"Registered image: {image_record.image_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register image {image_record.image_id}: {e}")
                return False
    
    def get_image(self, image_id: str) -> Optional[ImageRecord]:
        """Retrieve an image record by ID."""
        with self._lock:
            try:
                batch_file = self._find_image_batch_file(image_id)
                if not batch_file:
                    return None
                
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                
                image_batch = ImageBatch.from_dict(batch_data)
                image_record = image_batch.get_image(image_id)
                
                if image_record:
                    # Update last accessed in index
                    if image_id in self.image_index:
                        self.image_index[image_id]['last_accessed'] = datetime.now().isoformat()
                        self._save_indexes()
                
                return image_record
                
            except Exception as e:
                logger.error(f"Failed to get image {image_id}: {e}")
                return None
    
    def get_session_images(self, session_id: str, limit: int = 50) -> List[ImageRecord]:
        """Get all images for a session."""
        try:
            if session_id not in self.session_index:
                return []
            
            image_ids = self.session_index[session_id][-limit:]  # Get most recent
            images = []
            
            for image_id in reversed(image_ids):  # Most recent first
                image_record = self.get_image(image_id)
                if image_record:
                    images.append(image_record)
            
            return images
            
        except Exception as e:
            logger.error(f"Failed to get session images for {session_id}: {e}")
            return []
    
    def delete_image(self, image_id: str) -> bool:
        """Delete an image record."""
        with self._lock:
            try:
                batch_file = self._find_image_batch_file(image_id)
                if not batch_file:
                    return False
                
                # Load batch and remove image
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                
                image_batch = ImageBatch.from_dict(batch_data)
                if image_batch.remove_image(image_id):
                    # Save updated batch
                    with open(batch_file, 'w', encoding='utf-8') as f:
                        json.dump(image_batch.to_dict(), f, indent=2, default=str)
                    
                    # Remove from indexes
                    if image_id in self.image_index:
                        del self.image_index[image_id]
                    
                    # Remove from session index
                    for session_images in self.session_index.values():
                        if image_id in session_images:
                            session_images.remove(image_id)
                    
                    self._save_indexes()
                    
                    # Update statistics
                    self._update_stats('images_deleted')
                    
                    logger.info(f"Deleted image: {image_id}")
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Failed to delete image {image_id}: {e}")
                return False
    
    def get_image_count(self) -> int:
        """Get total number of registered images."""
        return len(self.image_index)
    
    def get_session_image_count(self, session_id: str) -> int:
        """Get number of images for a specific session."""
        return len(self.session_index.get(session_id, []))
    
    def _update_stats(self, stat_name: str):
        """Update usage statistics."""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {}
            
            if stat_name not in stats:
                stats[stat_name] = 0
            stats[stat_name] += 1
            stats['last_updated'] = datetime.now().isoformat()
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to update stats: {e}")
    
    def cleanup_expired_images(self, max_age: timedelta = timedelta(days=30)) -> int:
        """Clean up old images (move to archived folder or delete)."""
        # This is a placeholder for future cleanup functionality
        # Could implement similar to session cleanup
        return 0
    
    def health_check(self) -> bool:
        """Check if image storage is healthy."""
        try:
            # Check if base directories exist and are writable
            if not self.images_dir.exists():
                return False
            
            # Try to write a test file
            test_file = self.index_dir / "health_check_test.tmp"
            test_file.write_text("health check", encoding='utf-8')
            test_file.unlink()  # Delete test file
            
            return True
            
        except Exception as e:
            logger.error(f"Image storage health check failed: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the image storage system."""
        return {
            'storage_type': 'file',
            'base_path': str(self.base_path),
            'images_directory': str(self.images_dir),
            'total_images': self.get_image_count(),
            'sessions_with_images': len([s for s in self.session_index.values() if s]),
            'health': self.health_check()
        }