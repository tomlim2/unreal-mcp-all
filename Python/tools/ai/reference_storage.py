"""
Reference Images Storage System

Handles storage and retrieval of reference images using refer_uid system.
Provides session-based storage with metadata management.
"""

import json
import logging
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from .reference_uid_manager import generate_reference_uid, add_reference_mapping, get_reference_mapping
from .session_management.utils.path_manager import get_path_manager

logger = logging.getLogger("UnrealMCP")


class ReferenceStorage:
    """Manages reference image storage with UID-based access."""

    def __init__(self, base_storage_path: str = None):
        # Use direct PathManager for centralized path management
        path_manager = get_path_manager()
        if base_storage_path is None:
            self.base_path = Path(path_manager.get_reference_images_path())
        else:
            # Legacy support: use provided path but ensure it exists
            self.base_path = Path(base_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_reference_uid_path(self, refer_uid: str) -> Path:
        """Get storage path for a specific reference UID using UID-based structure."""
        path_manager = get_path_manager()
        # Use UID-based path structure instead of session-based
        uid_path = Path(path_manager.get_reference_uid_path(refer_uid))
        uid_path.mkdir(parents=True, exist_ok=True)
        return uid_path

    def store_reference_image(
        self,
        session_id: str,
        image_data: str,  # base64 encoded
        purpose: str,
        mime_type: str = "image/jpeg"
    ) -> str:
        try:
            # Generate unique refer_uid
            refer_uid = generate_reference_uid()

            # Get UID-based storage path
            uid_path = self.get_reference_uid_path(refer_uid)

            # Determine file extension from mime_type
            ext = self._get_extension_from_mime_type(mime_type)

            # Store image file (use just the extension, UID is in directory name)
            image_filename = f"image{ext}"
            image_path = uid_path / image_filename

            # Decode and save image
            image_bytes = base64.b64decode(image_data)
            with open(image_path, 'wb') as f:
                f.write(image_bytes)

            # Store metadata
            metadata = {
                "refer_uid": refer_uid,
                "purpose": purpose,
                "mime_type": mime_type,
                "session_id": session_id,
                "filename": image_filename,
                "size_bytes": len(image_bytes)
            }

            metadata_path = uid_path / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            # Add to reference UID mapping system
            add_reference_mapping(
                refer_uid=refer_uid,
                filename=image_filename,
                session_id=session_id,
                purpose=purpose,
                mime_type=mime_type,
                size_bytes=len(image_bytes),
                metadata=metadata
            )

            logger.info(f"Stored reference image {refer_uid} for session {session_id}")
            return refer_uid

        except Exception as e:
            logger.error(f"Failed to store reference image: {e}")
            raise

    def get_reference_image(self, refer_uid: str) -> Optional[Dict[str, Any]]:
        try:
            # Get mapping from reference UID manager
            mapping = get_reference_mapping(refer_uid)
            if not mapping:
                logger.warning(f"No mapping found for refer_uid: {refer_uid}")
                return None

            # Load metadata from UID-based structure
            uid_path = self.get_reference_uid_path(refer_uid)
            metadata_path = uid_path / "metadata.json"

            if not metadata_path.exists():
                logger.warning(f"Metadata not found: {metadata_path}")
                return None

            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Load image data
            image_path = uid_path / metadata['filename']
            if not image_path.exists():
                logger.warning(f"Image file not found: {image_path}")
                return None

            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # Return complete reference image data
            return {
                'refer_uid': refer_uid,
                'data': base64.b64encode(image_bytes).decode('utf-8'),
                'purpose': metadata['purpose'],
                'mime_type': metadata['mime_type'],
                'session_id': metadata['session_id'],
                'size_bytes': metadata['size_bytes']
            }

        except Exception as e:
            logger.error(f"Failed to retrieve reference image {refer_uid}: {e}")
            return None

    def get_session_references(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all reference images for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of reference image metadata
        """
        try:
            from .reference_uid_manager import get_reference_mappings_by_session_id

            # Get references from the separate reference UID manager
            references = get_reference_mappings_by_session_id(session_id)

            # Format for API response
            formatted_references = []
            for ref in references:
                formatted_references.append({
                    'refer_uid': ref['refer_uid'],
                    'purpose': ref['purpose'],
                    'mime_type': ref['mime_type'],
                    'size_bytes': ref['size_bytes'],
                    'filename': ref['filename']
                })

            return formatted_references

        except Exception as e:
            logger.error(f"Failed to get session references for {session_id}: {e}")
            return []

    def delete_reference_image(self, refer_uid: str) -> bool:
        """Delete a reference image by refer_uid.

        Args:
            refer_uid: Reference UID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Get mapping to find session
            mapping = get_reference_mapping(refer_uid)
            if not mapping:
                logger.warning(f"No mapping found for refer_uid: {refer_uid}")
                return False

            # Delete using UID-based structure
            uid_path = self.get_reference_uid_path(refer_uid)

            # Delete image file and metadata
            metadata_path = uid_path / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                image_path = uid_path / metadata['filename']
                if image_path.exists():
                    image_path.unlink()

                metadata_path.unlink()

                # Remove the entire UID directory if empty
                try:
                    uid_path.rmdir()
                except OSError:
                    pass  # Directory not empty, leave it

            logger.info(f"Deleted reference image {refer_uid}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete reference image {refer_uid}: {e}")
            return False

    def _get_extension_from_mime_type(self, mime_type: str) -> str:
        """Convert MIME type to file extension."""
        mime_to_ext = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp'
        }
        return mime_to_ext.get(mime_type.lower(), '.jpg')


# Global reference storage instance
_reference_storage = None


def get_reference_storage() -> ReferenceStorage:
    """Get global reference storage instance."""
    global _reference_storage
    if _reference_storage is None:
        _reference_storage = ReferenceStorage()
    return _reference_storage


# Convenience functions
def store_reference_image(session_id: str, image_data: str, purpose: str, mime_type: str = "image/jpeg") -> str:
    """Store reference image and return refer_uid."""
    return get_reference_storage().store_reference_image(session_id, image_data, purpose, mime_type)


def get_reference_image(refer_uid: str) -> Optional[Dict[str, Any]]:
    """Get reference image data by refer_uid."""
    return get_reference_storage().get_reference_image(refer_uid)


def get_session_references(session_id: str) -> List[Dict[str, Any]]:
    """Get all reference images for a session."""
    return get_reference_storage().get_session_references(session_id)