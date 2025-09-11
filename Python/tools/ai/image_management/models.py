"""
Data models for image management system.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, Optional
import json


@dataclass
class ImageRecord:
    """Represents a single image in the registry."""
    image_id: str
    image_name: str
    image_url: str
    session_id: str
    is_runtime: bool = False  # True for runtime screenshots, False for editor screenshots
    base_image_id: Optional[str] = None  # ID of the original base image (for transformations)
    meta: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'image_id': self.image_id,
            'image_name': self.image_name,
            'image_url': self.image_url,
            'session_id': self.session_id,
            'is_runtime': self.is_runtime,
            'base_image_id': self.base_image_id,
            'meta': self.meta,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageRecord':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            image_id=data['image_id'],
            image_name=data['image_name'],
            image_url=data['image_url'], 
            session_id=data['session_id'],
            is_runtime=data.get('is_runtime', False),
            base_image_id=data.get('base_image_id'),
            meta=data.get('meta', {}),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        )
    
    def is_screenshot(self) -> bool:
        """Check if this is an original screenshot (base image)."""
        return self.base_image_id is None
    
    def is_transformation(self) -> bool:
        """Check if this is a transformation of another image."""
        return self.base_image_id is not None
    
    def get_base_image_id(self) -> Optional[str]:
        """Get base image ID if this is a transformation."""
        return self.base_image_id
    
    def get_style_info(self) -> Optional[Dict[str, Any]]:
        """Get style information if this is a styled transformation."""
        return self.meta.get('style_info')
    
    def get_dimensions(self) -> Optional[Dict[str, int]]:
        """Get image dimensions if available."""
        return self.meta.get('dimensions')
    
    def set_base_image_id(self, base_image_id: str):
        """Set base image ID for transformations."""
        self.base_image_id = base_image_id
    
    def set_style_info(self, style_prompt: str, intensity: float = 0.8):
        """Set style information for styled transformations."""
        self.meta['style_info'] = {
            'prompt': style_prompt,
            'intensity': intensity
        }
    
    def set_dimensions(self, width: int, height: int):
        """Set image dimensions."""
        self.meta['dimensions'] = {
            'width': width,
            'height': height
        }
    
    def set_screenshot_info(self, resolution_multiplier: float = 1.0, include_ui: bool = False):
        """Set screenshot-specific metadata."""
        self.meta.update({
            'source_type': 'screenshot',
            'resolution_multiplier': resolution_multiplier,
            'include_ui': include_ui
        })


@dataclass
class ImageBatch:
    """Represents a batch of images stored in a single JSON file."""
    batch_created_at: datetime
    images: Dict[str, ImageRecord] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'batch_created_at': self.batch_created_at.isoformat(),
            'images': {img_id: img.to_dict() for img_id, img in self.images.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageBatch':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            batch_created_at=datetime.fromisoformat(data['batch_created_at']),
            images={
                img_id: ImageRecord.from_dict(img_data) 
                for img_id, img_data in data.get('images', {}).items()
            }
        )
    
    def add_image(self, image_record: ImageRecord):
        """Add an image to this batch."""
        self.images[image_record.image_id] = image_record
    
    def get_image(self, image_id: str) -> Optional[ImageRecord]:
        """Get an image from this batch."""
        return self.images.get(image_id)
    
    def remove_image(self, image_id: str) -> bool:
        """Remove an image from this batch."""
        if image_id in self.images:
            del self.images[image_id]
            return True
        return False
    
    def get_image_count(self) -> int:
        """Get number of images in this batch."""
        return len(self.images)