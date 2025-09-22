"""
Minimal persistent UID manager for image tracking.

Provides continuous UID generation across server restarts with minimal state.
"""

import json
import logging
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger("UnrealMCP")


class UIDManager:
    """Simple persistent UID counter for image identification.
    
    Stores only the current counter value in JSON format.
    Thread-safe for concurrent access.
    SQL-migration ready (counter maps to AUTO_INCREMENT).
    """
    
    def __init__(self, storage_file: str = "uid_state.json"):
        self._storage_file = Path(storage_file)
        self._current_counter = 0
        self._lock = threading.Lock()
        self._initialized = False
    
    def get_next_uid(self) -> str:
        """Generate next sequential UID (e.g., img_043).
        
        Returns:
            Sequential UID string in format img_XXX
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True
            
            self._current_counter += 1
            self._save_state()
            
            uid = f"img_{self._current_counter:03d}"
            logger.info(f"Generated UID: {uid}")
            return uid
    
    def get_current_counter(self) -> int:
        """Get current counter value without incrementing.
        
        Returns:
            Current counter value
        """
        with self._lock:
            if not self._initialized:
                self._load_state()
                self._initialized = True
            return self._current_counter
    
    def _load_state(self) -> None:
        """Load counter state from JSON file."""
        try:
            if self._storage_file.exists():
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._current_counter = data.get('current_counter', 0)
                    logger.info(f"Loaded UID counter: {self._current_counter}")
            else:
                self._current_counter = 0
                logger.info("Initialized new UID counter: 0")
                # Create initial state file
                self._save_state()
                
        except Exception as e:
            logger.error(f"Failed to load UID state: {e}")
            logger.info("Falling back to counter: 0")
            self._current_counter = 0
    
    def _save_state(self) -> None:
        """Save counter state to JSON file with atomic write."""
        try:
            # Prepare state data
            state_data = {
                'current_counter': self._current_counter,
                'last_updated': datetime.now().isoformat()
            }
            
            # Atomic write: write to temp file then rename
            temp_file = self._storage_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self._storage_file)
            
            logger.debug(f"Saved UID state: counter={self._current_counter}")
            
        except Exception as e:
            logger.error(f"Failed to save UID state: {e}")
            # Non-fatal: continue with in-memory counter


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
            # Store UID state in Python directory for persistence
            python_dir = Path(__file__).parent.parent.parent
            storage_path = python_dir / "uid_state.json"
            _global_uid_manager = UIDManager(str(storage_path))
            logger.info(f"Initialized global UID manager: {storage_path}")
        
        return _global_uid_manager


def generate_image_uid() -> str:
    """Convenience function to generate next image UID.

    Returns:
        Sequential UID string (e.g., img_043)
    """
    return get_uid_manager().get_next_uid()


def generate_video_uid() -> str:
    """Convenience function to generate next video UID.

    Returns:
        Sequential UID string (e.g., vid_043)
    """
    image_uid = get_uid_manager().get_next_uid()
    return image_uid.replace('img_', 'vid_')