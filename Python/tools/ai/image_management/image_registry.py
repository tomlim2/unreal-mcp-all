"""
Main image registry for centralized image management.
Provides the primary interface for registering, retrieving, and managing images.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .image_storage import ImageStorage
from .image_utils import ImageUtils
from .models import ImageRecord
from ..session_management.utils.path_manager import get_path_manager

logger = logging.getLogger("ImageManager.Registry")

# Global registry instance
_image_registry_instance = None


class ImageRegistry:
    """
    Main image registry providing centralized image management.
    
    This class serves as the primary interface for all image operations:
    - Registering new screenshots and styled images
    - Retrieving image information and URLs
    - Managing image metadata and relationships
    - Providing gallery data for frontend
    """
    
    def __init__(self, storage: ImageStorage = None):
        """
        Initialize the image registry.
        
        Args:
            storage: ImageStorage instance (creates default if None)
        """
        self.storage = storage or ImageStorage()
        self.utils = ImageUtils()
        self.path_manager = get_path_manager()
        
        logger.info("ImageRegistry initialized")
    
    def register_screenshot(self, 
                          file_path: str, 
                          session_id: str,
                          is_runtime: bool = False,
                          image_name: str = None,
                          resolution_multiplier: float = 1.0,
                          include_ui: bool = False) -> Optional[str]:
        """
        Register a new screenshot in the image registry.
        
        Args:
            file_path: Path to the screenshot file
            session_id: Session that created this screenshot
            is_runtime: True for runtime screenshots, False for editor screenshots
            image_name: Human-readable name for the image (optional)
            resolution_multiplier: Screenshot resolution multiplier
            include_ui: Whether UI was included in screenshot
            
        Returns:
            Generated image_id if successful, None otherwise
        """
        try:
            source_path = Path(file_path)
            
            if not source_path.exists():
                logger.error(f"Screenshot file not found: {file_path}")
                return None
            
            # Generate unique image ID
            image_id = self.utils.generate_image_id("img")
            
            # Get creation timestamp
            created_at = datetime.now()
            
            # Generate image name if not provided
            if image_name is None:
                screenshot_type = "Runtime Screenshot" if is_runtime else "Editor Screenshot"
                image_name = f"{screenshot_type} {created_at.strftime('%H:%M:%S')}"
            
            # Get image dimensions
            dimensions = self.utils.get_image_dimensions(source_path)
            
            # Create image record (screenshot has no base_image_id)
            image_record = ImageRecord(
                image_id=image_id,
                image_name=image_name,
                image_url=self.utils.get_relative_image_url(image_id, is_transformation=False),
                session_id=session_id,
                is_runtime=is_runtime,
                base_image_id=None,  # Screenshots are base images
                created_at=created_at
            )
            
            # Set screenshot metadata
            image_record.set_screenshot_info(resolution_multiplier, include_ui)
            if dimensions:
                image_record.set_dimensions(dimensions[0], dimensions[1])
            
            # Copy file to registry location
            target_path = self.utils.resolve_image_file_path(
                image_id, False, self.storage.images_dir
            )
            
            if not self.utils.copy_image_to_registry(source_path, target_path):
                logger.error(f"Failed to copy screenshot to registry")
                return None
            
            # Register in storage
            if self.storage.register_image(image_record):
                logger.info(f"Registered screenshot: {image_id} for session {session_id}")
                return image_id
            else:
                # Clean up copied file if registration failed
                try:
                    target_path.unlink()
                except:
                    pass
                return None
                
        except Exception as e:
            logger.error(f"Failed to register screenshot {file_path}: {e}")
            return None
    
    def register_styled_image(self,
                             file_path: str,
                             session_id: str,
                             base_image_id: str,
                             image_name: str = None,
                             style_prompt: str = "",
                             intensity: float = 0.8) -> Optional[str]:
        """
        Register a new styled image transformation.
        
        Args:
            file_path: Path to the styled image file
            session_id: Session that created this image
            base_image_id: ID of the base image that was transformed
            image_name: Human-readable name for the image (optional)
            style_prompt: Style prompt used for transformation
            intensity: Style intensity
            
        Returns:
            Generated image_id if successful, None otherwise
        """
        try:
            source_path = Path(file_path)
            
            if not source_path.exists():
                logger.error(f"Styled image file not found: {file_path}")
                return None
            
            # Verify base image exists
            base_image = self.storage.get_image(base_image_id)
            if not base_image:
                logger.error(f"Base image not found: {base_image_id}")
                return None
            
            # Generate unique image ID
            image_id = self.utils.generate_image_id("img")
            
            # Get creation timestamp
            created_at = datetime.now()
            
            # Generate image name if not provided
            if image_name is None:
                if style_prompt:
                    style_desc = style_prompt[:20] + "..." if len(style_prompt) > 20 else style_prompt
                    image_name = f"Styled: {style_desc} ({created_at.strftime('%H:%M:%S')})"
                else:
                    image_name = f"Transformation {created_at.strftime('%H:%M:%S')}"
            
            # Get image dimensions
            dimensions = self.utils.get_image_dimensions(source_path)
            
            # Create image record (inherit is_runtime from base image)
            image_record = ImageRecord(
                image_id=image_id,
                image_name=image_name,
                image_url=self.utils.get_relative_image_url(image_id, is_transformation=True),
                session_id=session_id,
                is_runtime=base_image.is_runtime,  # Inherit from base image
                base_image_id=base_image_id,  # Set base image relationship
                created_at=created_at
            )
            
            # Set styled image metadata
            image_record.set_style_info(style_prompt, intensity)
            if dimensions:
                image_record.set_dimensions(dimensions[0], dimensions[1])
            
            # Copy file to registry location
            target_path = self.utils.resolve_image_file_path(
                image_id, True, self.storage.images_dir
            )
            
            if not self.utils.copy_image_to_registry(source_path, target_path):
                logger.error(f"Failed to copy styled image to registry")
                return None
            
            # Register in storage
            if self.storage.register_image(image_record):
                logger.info(f"Registered styled image: {image_id} (base: {base_image_id})")
                return image_id
            else:
                # Clean up copied file if registration failed
                try:
                    target_path.unlink()
                except:
                    pass
                return None
                
        except Exception as e:
            logger.error(f"Failed to register styled image {file_path}: {e}")
            return None
    
    def get_image(self, image_id: str) -> Optional[ImageRecord]:
        """
        Get an image record by ID.
        
        Args:
            image_id: Image ID to retrieve
            
        Returns:
            ImageRecord if found, None otherwise
        """
        return self.storage.get_image(image_id)
    
    def get_image_url(self, image_id: str) -> Optional[str]:
        """
        Get the URL for an image by ID.
        
        Args:
            image_id: Image ID
            
        Returns:
            Image URL if found, None otherwise
        """
        image_record = self.storage.get_image(image_id)
        return image_record.image_url if image_record else None
    
    def get_image_file_path(self, image_id: str) -> Optional[Path]:
        """
        Get the actual file path for an image by ID.
        
        Args:
            image_id: Image ID
            
        Returns:
            Path to image file if found, None otherwise
        """
        image_record = self.storage.get_image(image_id)
        if not image_record:
            return None
        
        return self.utils.resolve_image_file_path(
            image_id, image_record.is_transformation(), self.storage.images_dir
        )
    
    def get_session_images(self, session_id: str, limit: int = 50) -> List[ImageRecord]:
        """
        Get all images for a session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of images to return
            
        Returns:
            List of ImageRecord objects
        """
        return self.storage.get_session_images(session_id, limit)
    
    def get_session_image_gallery(self, session_id: str) -> Dict[str, Any]:
        """
        Get gallery data for a session (formatted for frontend).
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with gallery data
        """
        images = self.get_session_images(session_id)
        
        gallery_data = {
            'session_id': session_id,
            'total_images': len(images),
            'images': []
        }
        
        for img in images:
            image_data = {
                'image_id': img.image_id,
                'image_name': img.image_name,
                'image_url': img.image_url,
                'is_runtime': img.is_runtime,
                'is_transformation': img.is_transformation(),
                'base_image_id': img.base_image_id,
                'created_at': img.created_at.isoformat(),
                'meta': img.meta
            }
            
            # Add transformation info
            if img.is_transformation():
                image_data['style_info'] = img.get_style_info()
            
            gallery_data['images'].append(image_data)
        
        return gallery_data
    
    def get_latest_image_id(self, session_id: str) -> Optional[str]:
        """
        Get the most recent image ID for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Latest image ID if found, None otherwise
        """
        images = self.get_session_images(session_id, limit=1)
        return images[0].image_id if images else None
    
    def get_latest_screenshot_id(self, session_id: str) -> Optional[str]:
        """
        Get the most recent screenshot ID for a session (not styled).
        
        Args:
            session_id: Session ID
            
        Returns:
            Latest screenshot ID if found, None otherwise
        """
        images = self.get_session_images(session_id, limit=10)  # Check recent images
        
        for img in images:
            if img.is_screenshot():  # Find first screenshot (base image)
                return img.image_id
        
        return None
    
    def delete_image(self, image_id: str) -> bool:
        """
        Delete an image from the registry.
        
        Args:
            image_id: Image ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get image info before deletion
            image_record = self.storage.get_image(image_id)
            if not image_record:
                logger.warning(f"Image not found for deletion: {image_id}")
                return False
            
            # Delete from storage
            if self.storage.delete_image(image_id):
                # Try to delete actual file
                file_path = self.utils.resolve_image_file_path(
                    image_id, image_record.is_transformation(), self.storage.images_dir
                )
                
                try:
                    if file_path.exists():
                        file_path.unlink()
                        logger.debug(f"Deleted image file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete image file {file_path}: {e}")
                
                logger.info(f"Deleted image: {image_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete image {image_id}: {e}")
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the image registry.
        
        Returns:
            Dictionary with registry statistics
        """
        storage_info = self.storage.get_storage_info()
        
        return {
            'total_images': storage_info['total_images'],
            'sessions_with_images': storage_info['sessions_with_images'],
            'storage_path': storage_info['images_directory'],
            'health': storage_info['health']
        }
    
    def health_check(self) -> bool:
        """
        Check if the image registry is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return self.storage.health_check()


def get_image_registry() -> ImageRegistry:
    """
    Get the global image registry instance.
    
    Returns:
        Global ImageRegistry instance
    """
    global _image_registry_instance
    
    if _image_registry_instance is None:
        _image_registry_instance = ImageRegistry()
    
    return _image_registry_instance