"""
Enhanced persistent UID manager for image and video tracking with mapping.

Provides:
- Separate counters for images and videos
- UID-to-file mapping table
- Parent-child relationship tracking
- Continuous UID generation across server restarts
"""

import json
import logging
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from core.session.utils.path_manager import get_path_manager

logger = logging.getLogger("UnrealMCP")


class UIDManager:
    """Enhanced UID manager with separate counters and mapping table.

    Features:
    - Separate counters for images (img_XXX) and videos (vid_XXX)
    - UID-to-file mapping with parent-child relationships
    - Thread-safe for concurrent access
    - Atomic file operations for reliability
    """

    def __init__(self, storage_file: str = None):
        # Use PathManager for centralized UID storage path
        if storage_file is None:
            path_manager = get_path_manager()
            uid_storage_dir = path_manager.get_uid_storage_path()
            storage_file = str(Path(uid_storage_dir) / "uid_state.json")
        self._storage_file = Path(storage_file)
        self._img_counter = 0
        self._vid_counter = 0
        self._obj_counter = 0  # New counter for 3D objects (OBJ format)
        self._fbx_counter = 0  # New counter for FBX format 3D objects
        self._uid_mappings = {}
        self._lock = threading.Lock()
        self._initialized = False
    
    def get_next_image_uid(self) -> str:
        """Generate next sequential image UID (e.g., img_043).

        Returns:
            Sequential image UID string in format img_XXX
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            self._img_counter += 1
            self._save_state()

            uid = f"img_{self._img_counter:03d}"
            logger.info(f"Generated image UID: {uid}")
            return uid

    def get_next_video_uid(self) -> str:
        """Generate next sequential video UID (e.g., vid_001).

        Returns:
            Sequential video UID string in format vid_XXX
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            self._vid_counter += 1
            self._save_state()

            uid = f"vid_{self._vid_counter:03d}"
            logger.info(f"Generated video UID: {uid}")
            return uid

    def get_next_object_uid(self) -> str:
        """Generate next sequential 3D object UID for OBJ format (e.g., obj_001).

        Returns:
            Sequential object UID string in format obj_XXX
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            self._obj_counter += 1
            self._save_state()

            uid = f"obj_{self._obj_counter:03d}"
            logger.info(f"Generated OBJ UID: {uid}")
            return uid

    def get_next_fbx_uid(self) -> str:
        """Generate next sequential FBX UID (e.g., fbx_001).

        Returns:
            Sequential FBX UID string in format fbx_XXX
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            self._fbx_counter += 1
            self._save_state()

            uid = f"fbx_{self._fbx_counter:03d}"
            logger.info(f"Generated FBX UID: {uid}")
            return uid

    def get_current_counters(self) -> Dict[str, int]:
        """Get current counter values without incrementing.

        Returns:
            Dictionary with all counter values
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True
            return {
                'img_counter': self._img_counter,
                'vid_counter': self._vid_counter,
                'obj_counter': self._obj_counter,
                'fbx_counter': self._fbx_counter
            }

    def add_mapping(self, uid: str, content_type: str, filename: str,
                   parent_uid: Optional[str] = None, session_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add UID-to-file mapping entry.

        Args:
            uid: Unique identifier (e.g., img_001, vid_001)
            content_type: Type of content ('image' or 'video')
            filename: Name of the file
            parent_uid: Optional parent UID for relationships
            session_id: Optional session ID for batch cleanup
            metadata: Optional additional metadata
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            self._uid_mappings[uid] = {
                'type': content_type,
                'filename': filename,
                'parent_uid': parent_uid,
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            self._save_state()
            logger.info(f"Added mapping: {uid} -> {filename} (session: {session_id})")

    def get_mapping(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get mapping information for a UID.

        Args:
            uid: Unique identifier to look up

        Returns:
            Mapping dictionary or None if not found
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True
            return self._uid_mappings.get(uid)

    def get_children_by_parent_uid(self, parent_uid: str) -> List[Dict[str, Any]]:
        """Get all child mappings for a given parent UID.

        Args:
            parent_uid: Parent UID to search for

        Returns:
            List of child mapping dictionaries
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            children = []
            for uid, mapping in self._uid_mappings.items():
                if mapping.get('parent_uid') == parent_uid:
                    child_info = mapping.copy()
                    child_info['uid'] = uid
                    children.append(child_info)
            return children

    def get_mappings_by_session_id(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all UID mappings for a specific session.

        Args:
            session_id: Session ID to search for

        Returns:
            List of mapping dictionaries with UID included
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            session_mappings = []
            for uid, mapping in self._uid_mappings.items():
                if mapping.get('session_id') == session_id:
                    mapping_with_uid = mapping.copy()
                    mapping_with_uid['uid'] = uid
                    session_mappings.append(mapping_with_uid)
            return session_mappings

    def delete_mappings_by_session_id(self, session_id: str) -> List[str]:
        """Delete all UID mappings for a specific session.

        Args:
            session_id: Session ID to delete mappings for

        Returns:
            List of deleted UIDs
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            deleted_uids = []
            uids_to_delete = [
                uid for uid, mapping in self._uid_mappings.items()
                if mapping.get('session_id') == session_id
            ]

            for uid in uids_to_delete:
                del self._uid_mappings[uid]
                deleted_uids.append(uid)

            if deleted_uids:
                self._save_state()
                logger.info(f"Deleted {len(deleted_uids)} mappings for session {session_id}: {deleted_uids}")

            return deleted_uids

    def get_all_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Get all UID mappings.

        Returns:
            Dictionary of all UID mappings
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True
            return self._uid_mappings.copy()
    
    def _load_state(self) -> None:
        """Load counter state and mappings from JSON file."""
        try:
            if self._storage_file.exists():
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Handle migration from old format
                    if 'current_counter' in data:
                        # Migrate from old single counter to img_counter
                        self._img_counter = data.get('current_counter', 0)
                        self._vid_counter = 0
                        logger.info(f"Migrated old counter to img_counter: {self._img_counter}")
                    else:
                        # New format with separate counters
                        self._img_counter = data.get('img_counter', 0)
                        self._vid_counter = data.get('vid_counter', 0)
                        self._obj_counter = data.get('obj_counter', 0)  # Load 3D object counter (OBJ)
                        self._fbx_counter = data.get('fbx_counter', 0)  # Load FBX counter
                        logger.info(f"Loaded counters - img: {self._img_counter}, vid: {self._vid_counter}, obj: {self._obj_counter}, fbx: {self._fbx_counter}")

                    # Load mappings
                    self._uid_mappings = data.get('uid_mappings', {})

                    # Migrate existing mappings to include session_id field if missing
                    migration_count = 0
                    for uid, mapping in self._uid_mappings.items():
                        if 'session_id' not in mapping:
                            mapping['session_id'] = None  # Set to None for existing mappings
                            migration_count += 1

                    if migration_count > 0:
                        logger.info(f"Migrated {migration_count} existing mappings to include session_id field")
                        # Save the migrated data
                        self._save_state()

                    logger.info(f"Loaded {len(self._uid_mappings)} UID mappings")

            else:
                self._img_counter = 0
                self._vid_counter = 0
                self._uid_mappings = {}
                logger.info("Initialized new UID state")
                # Create initial state file
                self._save_state()

        except Exception as e:
            logger.error(f"Failed to load UID state: {e}")
            logger.info("Falling back to default state")
            self._img_counter = 0
            self._vid_counter = 0
            self._uid_mappings = {}
    
    def _save_state(self) -> None:
        """Save counter state and mappings to JSON file with atomic write."""
        try:
            # Prepare state data
            state_data = {
                'img_counter': self._img_counter,
                'vid_counter': self._vid_counter,
                'obj_counter': self._obj_counter,  # Save 3D object counter (OBJ)
                'fbx_counter': self._fbx_counter,  # Save FBX counter
                'uid_mappings': self._uid_mappings,
                'last_updated': datetime.now().isoformat()
            }

            # Atomic write: write to temp file then rename
            temp_file = self._storage_file.with_suffix('.tmp')

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_file.replace(self._storage_file)

            logger.debug(f"Saved UID state: img={self._img_counter}, vid={self._vid_counter}, mappings={len(self._uid_mappings)}")

        except Exception as e:
            logger.error(f"Failed to save UID state: {e}")
            # Non-fatal: continue with in-memory state


# Global instance for shared UID generation
_global_uid_manager: Optional[UIDManager] = None
_manager_lock = threading.Lock()


def get_uid_manager() -> UIDManager:
    """Get global UID manager instance (singleton pattern).
    
    Returns:
        Global UIDManager instance
    """
    global _global_uid_manager
    
    with _manager_lock:
        if _global_uid_manager is None:
            # Store UID state in data_storage directory for centralized management
            python_dir = Path(__file__).parent.parent.parent
            storage_path = python_dir / "data_storage" / "uid" / "uid_state.json"
            _global_uid_manager = UIDManager(str(storage_path))
            logger.info(f"Initialized global UID manager: {storage_path}")
        
        return _global_uid_manager


def generate_image_uid() -> str:
    """Convenience function to generate next image UID.

    Returns:
        Sequential UID string (e.g., img_043)
    """
    return get_uid_manager().get_next_image_uid()


def generate_video_uid() -> str:
    """Convenience function to generate next video UID.

    Returns:
        Sequential UID string (e.g., vid_001)
    """
    return get_uid_manager().get_next_video_uid()


def generate_object_uid() -> str:
    """Convenience function to generate next 3D object UID.

    Returns:
        Sequential UID string (e.g., obj_001)
    """
    return get_uid_manager().get_next_object_uid()


def add_uid_mapping(uid: str, content_type: str, filename: str,
                   parent_uid: Optional[str] = None, session_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to add UID mapping.

    Args:
        uid: Unique identifier (e.g., img_001, vid_001)
        content_type: Type of content ('image' or 'video')
        filename: Name of the file
        parent_uid: Optional parent UID for relationships
        session_id: Optional session ID for batch cleanup
        metadata: Optional additional metadata
    """
    get_uid_manager().add_mapping(uid, content_type, filename, parent_uid, session_id, metadata)


def get_uid_mapping(uid: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get mapping for a UID.

    Args:
        uid: Unique identifier to look up

    Returns:
        Mapping dictionary or None if not found
    """
    return get_uid_manager().get_mapping(uid)


def get_children_by_parent_uid(parent_uid: str) -> List[Dict[str, Any]]:
    """Convenience function to get children by parent UID.

    Args:
        parent_uid: Parent UID to search for

    Returns:
        List of child mapping dictionaries
    """
    return get_uid_manager().get_children_by_parent_uid(parent_uid)


def get_mappings_by_session_id(session_id: str) -> List[Dict[str, Any]]:
    """Convenience function to get mappings by session ID.

    Args:
        session_id: Session ID to search for

    Returns:
        List of mapping dictionaries with UID included
    """
    return get_uid_manager().get_mappings_by_session_id(session_id)


def delete_mappings_by_session_id(session_id: str) -> List[str]:
    """Convenience function to delete mappings by session ID.

    Args:
        session_id: Session ID to delete mappings for

    Returns:
        List of deleted UIDs
    """
    return get_uid_manager().delete_mappings_by_session_id(session_id)


def get_latest_image_uid() -> Optional[str]:
    """Get the most recently created image UID across all sessions.

    Returns:
        Latest image UID (img_XXX) or None if no images exist
    """
    manager = get_uid_manager()
    all_mappings = manager.get_all_mappings()

    # Filter for image UIDs only
    image_mappings = {
        uid: data for uid, data in all_mappings.items()
        if uid.startswith('img_') and data.get('content_type') == 'image'
    }

    if not image_mappings:
        return None

    # Sort by created_at timestamp (newest first)
    sorted_images = sorted(
        image_mappings.items(),
        key=lambda x: x[1].get('created_at', ''),
        reverse=True
    )

    latest_uid = sorted_images[0][0]
    logger.debug(f"Latest image UID from UID manager: {latest_uid}")
    return latest_uid