"""
Separate Reference UID Manager for reference images

Provides:
- Separate refer_uid counter and mapping table
- Session-based organization
- Independent from main UID system
- Persistent storage in refer_uid_mappings.json
"""

import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger("UnrealMCP")


class ReferenceUIDManager:
    """Separate UID manager specifically for reference images.

    Features:
    - Separate counter for refer_uid (refer_001, refer_002, etc.)
    - Independent mapping table from main UID system
    - Session-based organization
    - Thread-safe for concurrent access
    - Atomic file operations for reliability
    """

    def __init__(self, storage_file: str = "refer_uid_mappings.json"):
        self._storage_file = Path(storage_file)
        self._ref_counter = 0
        self._refer_mappings = {}
        self._lock = threading.Lock()
        self._initialized = False

    def get_next_reference_uid(self) -> str:
        """Generate next sequential reference UID (e.g., refer_043).

        Returns:
            Sequential reference UID string in format refer_XXX
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            self._ref_counter += 1
            self._save_state()

            uid = f"refer_{self._ref_counter:03d}"
            logger.info(f"Generated reference UID: {uid}")
            return uid

    def get_current_counter(self) -> int:
        """Get current counter value without incrementing.

        Returns:
            Current reference counter value
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True
            return self._ref_counter

    def add_mapping(self, refer_uid: str, filename: str, session_id: str,
                   purpose: str, mime_type: str, size_bytes: int,
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add reference UID mapping entry.

        Args:
            refer_uid: Reference UID (e.g., refer_001)
            filename: Name of the stored file
            session_id: Session ID for organization
            purpose: Purpose of reference (style, color, composition)
            mime_type: MIME type of the image
            size_bytes: Size of the image in bytes
            metadata: Optional additional metadata
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            self._refer_mappings[refer_uid] = {
                'filename': filename,
                'session_id': session_id,
                'purpose': purpose,
                'mime_type': mime_type,
                'size_bytes': size_bytes,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            self._save_state()
            logger.info(f"Added reference mapping: {refer_uid} -> {filename} (session: {session_id})")

    def get_mapping(self, refer_uid: str) -> Optional[Dict[str, Any]]:
        """Get mapping information for a reference UID.

        Args:
            refer_uid: Reference UID to look up

        Returns:
            Mapping dictionary or None if not found
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True
            return self._refer_mappings.get(refer_uid)

    def get_mappings_by_session_id(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all reference UID mappings for a specific session.

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
            for refer_uid, mapping in self._refer_mappings.items():
                if mapping.get('session_id') == session_id:
                    mapping_with_uid = mapping.copy()
                    mapping_with_uid['refer_uid'] = refer_uid
                    session_mappings.append(mapping_with_uid)
            return session_mappings

    def delete_mappings_by_session_id(self, session_id: str) -> List[str]:
        """Delete all reference UID mappings for a specific session.

        Args:
            session_id: Session ID to delete mappings for

        Returns:
            List of deleted reference UIDs
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True

            deleted_uids = []
            uids_to_delete = [
                refer_uid for refer_uid, mapping in self._refer_mappings.items()
                if mapping.get('session_id') == session_id
            ]

            for refer_uid in uids_to_delete:
                del self._refer_mappings[refer_uid]
                deleted_uids.append(refer_uid)

            if deleted_uids:
                self._save_state()
                logger.info(f"Deleted {len(deleted_uids)} reference mappings for session {session_id}: {deleted_uids}")

            return deleted_uids

    def get_all_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Get all reference UID mappings.

        Returns:
            Dictionary of all reference UID mappings
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True
            return self._refer_mappings.copy()

    def _load_state(self) -> None:
        """Load counter state and mappings from JSON file."""
        try:
            if self._storage_file.exists():
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self._ref_counter = data.get('ref_counter', 0)
                self._refer_mappings = data.get('refer_mappings', {})

                logger.info(f"Loaded reference state - counter: {self._ref_counter}, mappings: {len(self._refer_mappings)}")

            else:
                self._ref_counter = 0
                self._refer_mappings = {}
                logger.info("Initialized new reference UID state")
                # Create initial state file
                self._save_state()

        except Exception as e:
            logger.error(f"Failed to load reference UID state: {e}")
            logger.info("Falling back to default reference state")
            self._ref_counter = 0
            self._refer_mappings = {}

    def _save_state(self) -> None:
        """Save counter state and mappings to JSON file with atomic write."""
        try:
            # Prepare state data
            state_data = {
                'ref_counter': self._ref_counter,
                'refer_mappings': self._refer_mappings,
                'last_updated': datetime.now().isoformat()
            }

            # Atomic write: write to temp file then rename
            temp_file = self._storage_file.with_suffix('.tmp')

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_file.replace(self._storage_file)

            logger.debug(f"Saved reference UID state: counter={self._ref_counter}, mappings={len(self._refer_mappings)}")

        except Exception as e:
            logger.error(f"Failed to save reference UID state: {e}")
            # Non-fatal: continue with in-memory state


# Global instance for shared reference UID generation
_global_reference_uid_manager: Optional[ReferenceUIDManager] = None
_manager_lock = threading.Lock()


def get_reference_uid_manager() -> ReferenceUIDManager:
    """Get global reference UID manager instance (singleton pattern).

    Returns:
        Global ReferenceUIDManager instance
    """
    global _global_reference_uid_manager

    with _manager_lock:
        if _global_reference_uid_manager is None:
            # Store reference UID state in Python directory for persistence
            python_dir = Path(__file__).parent.parent.parent
            storage_path = python_dir / "refer_uid_mappings.json"
            _global_reference_uid_manager = ReferenceUIDManager(str(storage_path))
            logger.info(f"Initialized global reference UID manager: {storage_path}")

        return _global_reference_uid_manager


def generate_reference_uid() -> str:
    """Convenience function to generate next reference UID.

    Returns:
        Sequential UID string (e.g., refer_043)
    """
    return get_reference_uid_manager().get_next_reference_uid()


def add_reference_mapping(refer_uid: str, filename: str, session_id: str,
                         purpose: str, mime_type: str, size_bytes: int,
                         metadata: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to add reference UID mapping.

    Args:
        refer_uid: Reference UID (e.g., refer_001)
        filename: Name of the stored file
        session_id: Session ID for organization
        purpose: Purpose of reference (style, color, composition)
        mime_type: MIME type of the image
        size_bytes: Size of the image in bytes
        metadata: Optional additional metadata
    """
    get_reference_uid_manager().add_mapping(refer_uid, filename, session_id, purpose, mime_type, size_bytes, metadata)


def get_reference_mapping(refer_uid: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get mapping for a reference UID.

    Args:
        refer_uid: Reference UID to look up

    Returns:
        Mapping dictionary or None if not found
    """
    return get_reference_uid_manager().get_mapping(refer_uid)


def get_reference_mappings_by_session_id(session_id: str) -> List[Dict[str, Any]]:
    """Convenience function to get reference mappings by session ID.

    Args:
        session_id: Session ID to search for

    Returns:
        List of mapping dictionaries with UID included
    """
    return get_reference_uid_manager().get_mappings_by_session_id(session_id)


def delete_reference_mappings_by_session_id(session_id: str) -> List[str]:
    """Convenience function to delete reference mappings by session ID.

    Args:
        session_id: Session ID to delete mappings for

    Returns:
        List of deleted reference UIDs
    """
    return get_reference_uid_manager().delete_mappings_by_session_id(session_id)