"""
File-based storage backend for MegaMelange session management.
Uses E:\CINEVStudio\CINEVStudio\Saved\MegaMelange\ as the storage directory.
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
from threading import Lock

from .base_storage import BaseStorage
from ..session_context import SessionContext
from ..utils.path_manager import get_path_manager, PathManager, PathConfig

logger = logging.getLogger("SessionManager.FileStorage")


class FileStorage(BaseStorage):
    """
    File-based storage for session management using MegaMelange directory structure.
    
    Directory Structure:
    E:\CINEVStudio\CINEVStudio\Saved\MegaMelange\
    ├── sessions/
    │   ├── active/                    # Active sessions
    │   │   ├── 2025-01/              # Year-month folders
    │   │   │   ├── day-09/           # Day folders
    │   │   │   │   ├── session_abc123.json
    │   │   │   │   └── session_def456.json
    │   │   │   └── day-10/
    │   │   └── 2025-02/
    │   ├── archived/                  # Old sessions for cleanup
    │   └── metadata/                  # Session indices and metadata
    │       ├── session_index.json    # Quick lookup index
    │       └── stats.json            # Usage statistics
    └── logs/                         # Session-related logs
        └── session_storage.log
    """
    
    def __init__(self, base_path: str = None, path_manager: PathManager = None):
        """
        Initialize file storage with MegaMelange directory structure.
        
        Args:
            base_path: Optional explicit base path. If provided, overrides PathManager.
            path_manager: Optional PathManager instance. If None, uses global instance.
        """
        self._lock = Lock()  # Thread safety for file operations
        
        # Initialize path manager
        if path_manager is None:
            self.path_manager = get_path_manager()
        else:
            self.path_manager = path_manager
        
        # Determine base path
        if base_path is not None:
            # Explicit base path provided - use it directly
            self.base_path = Path(base_path)
            logger.info(f"FileStorage using explicit base path: {base_path}")
        else:
            # Use PathManager to determine path
            base_path = self.path_manager.get_megamelange_base_path()
            self.base_path = Path(base_path)
            logger.info(f"FileStorage using PathManager-derived path: {base_path}")
        
        # Define directory structure using PathManager
        self.sessions_dir = Path(self.path_manager.get_sessions_directory())
        self.active_dir = Path(self.path_manager.get_active_sessions_directory())
        self.archived_dir = Path(self.path_manager.get_archived_sessions_directory())
        self.metadata_dir = Path(self.path_manager.get_metadata_directory())
        self.logs_dir = Path(self.path_manager.get_logs_directory())
        
        # Ensure directory structure exists
        self.path_manager.ensure_directory_structure()
        
        # Initialize session index
        self.index_file = Path(self.path_manager.get_session_index_file())
        self.stats_file = Path(self.path_manager.get_stats_file())
        self._load_or_create_index()
        
        # Log path information
        path_info = self.path_manager.get_path_info()
        logger.info(f"FileStorage initialized - Path derivation: {path_info.get('path_derivation', 'unknown')}")
        if path_info.get('unreal_project_path'):
            logger.info(f"Unreal project path: {path_info['unreal_project_path']}")
    
    # Removed _ensure_directories method - now handled by PathManager
    
    def _load_or_create_index(self):
        """Load or create the session index for fast lookups."""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.session_index = json.load(f)
            else:
                self.session_index = {}
                self._save_index()
        except Exception as e:
            logger.warning(f"Failed to load session index, creating new: {e}")
            self.session_index = {}
    
    def _save_index(self):
        """Save the session index."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_index, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save session index: {e}")
    
    def _get_session_path(self, session_id: str, created_at: datetime = None) -> Path:
        """
        Get the file path for a session using PathManager.
        
        Args:
            session_id: Session ID
            created_at: Session creation date (for organizing into folders)
            
        Returns:
            Path to the session file
        """
        return Path(self.path_manager.get_session_file_path(session_id, created_at))
    
    def _find_session_path(self, session_id: str) -> Optional[Path]:
        """
        Find the path for an existing session using the index.
        
        Args:
            session_id: Session ID to find
            
        Returns:
            Path to session file if found, None otherwise
        """
        # Check index first for fast lookup
        if session_id in self.session_index:
            relative_path = self.session_index[session_id]['file_path']
            full_path = self.base_path / relative_path
            if full_path.exists():
                return full_path
            else:
                # Index is stale, remove entry
                del self.session_index[session_id]
                self._save_index()
        
        # Fallback: search the active directory structure
        for year_month_dir in self.active_dir.iterdir():
            if not year_month_dir.is_dir():
                continue
            for day_dir in year_month_dir.iterdir():
                if not day_dir.is_dir():
                    continue
                session_file = day_dir / f"session_{session_id}.json"
                if session_file.exists():
                    # Update index
                    relative_path = session_file.relative_to(self.base_path)
                    self.session_index[session_id] = {
                        'file_path': str(relative_path),
                        'last_accessed': datetime.now().isoformat()
                    }
                    self._save_index()
                    return session_file
        
        return None
    
    def create_session(self, session_context: SessionContext) -> bool:
        """Create a new session file."""
        with self._lock:
            try:
                session_path = self._get_session_path(
                    session_context.session_id, 
                    session_context.created_at
                )
                
                # Check if session already exists
                if session_path.exists():
                    logger.warning(f"Session file already exists: {session_path}")
                    return False
                
                # Save session data
                session_data = session_context.to_dict()
                with open(session_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, default=str)
                
                # Update index
                relative_path = session_path.relative_to(self.base_path)
                self.session_index[session_context.session_id] = {
                    'file_path': str(relative_path),
                    'created_at': session_context.created_at.isoformat(),
                    'last_accessed': datetime.now().isoformat()
                }
                self._save_index()
                
                # Update statistics
                self._update_stats('sessions_created')
                
                logger.info(f"Created session file: {session_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to create session {session_context.session_id}: {e}")
                return False
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Retrieve a session from file."""
        with self._lock:
            try:
                session_path = self._find_session_path(session_id)
                if not session_path:
                    return None
                
                with open(session_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Update last accessed in index
                if session_id in self.session_index:
                    self.session_index[session_id]['last_accessed'] = datetime.now().isoformat()
                    self._save_index()
                
                return SessionContext.from_dict(session_data)
                
            except Exception as e:
                logger.error(f"Failed to get session {session_id}: {e}")
                return None
    
    def update_session(self, session_context: SessionContext) -> bool:
        """Update an existing session file."""
        with self._lock:
            try:
                session_path = self._find_session_path(session_context.session_id)
                if not session_path:
                    logger.error(f"Session file not found for update: {session_context.session_id}")
                    return False
                
                # Save updated session data
                session_data = session_context.to_dict()
                with open(session_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, default=str)
                
                # Update index
                if session_context.session_id in self.session_index:
                    self.session_index[session_context.session_id]['last_accessed'] = datetime.now().isoformat()
                    self._save_index()
                
                # Update statistics
                self._update_stats('sessions_updated')
                
                logger.debug(f"Updated session file: {session_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to update session {session_context.session_id}: {e}")
                return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session file."""
        with self._lock:
            try:
                session_path = self._find_session_path(session_id)
                if not session_path:
                    logger.warning(f"Session file not found for deletion: {session_id}")
                    return False
                
                # Move to archived folder instead of permanent deletion
                archived_path = self.archived_dir / f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                archived_path.parent.mkdir(parents=True, exist_ok=True)
                
                session_path.rename(archived_path)
                
                # Remove from index
                if session_id in self.session_index:
                    del self.session_index[session_id]
                    self._save_index()
                
                # Update statistics
                self._update_stats('sessions_deleted')
                
                logger.info(f"Archived session file: {session_path} -> {archived_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")
                return False
    
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[SessionContext]:
        """List sessions with pagination."""
        try:
            sessions = []
            
            # Get all session IDs from index, sorted by last_accessed
            session_items = list(self.session_index.items())
            session_items.sort(key=lambda x: x[1].get('last_accessed', ''), reverse=True)
            
            # Apply pagination
            paginated_items = session_items[offset:offset + limit]
            
            for session_id, index_data in paginated_items:
                session = self.get_session(session_id)
                if session:
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
    
    def cleanup_expired_sessions(self, max_age: timedelta = timedelta(days=30)) -> int:
        """Move expired sessions to archived folder."""
        with self._lock:
            try:
                cutoff_date = datetime.now() - max_age
                deleted_count = 0
                sessions_to_remove = []
                
                # Check each session in the index
                for session_id, index_data in self.session_index.items():
                    try:
                        last_accessed = datetime.fromisoformat(index_data['last_accessed'])
                        if last_accessed < cutoff_date:
                            # This session is expired, move to archived
                            if self.delete_session(session_id):
                                sessions_to_remove.append(session_id)
                                deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Error checking session {session_id} expiration: {e}")
                
                # Update statistics
                if deleted_count > 0:
                    self._update_stats('cleanup_operations')
                    logger.info(f"Cleaned up {deleted_count} expired sessions")
                
                return deleted_count
                
            except Exception as e:
                logger.error(f"Failed to cleanup expired sessions: {e}")
                return 0
    
    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self.session_index)
    
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
    
    def health_check(self) -> bool:
        """Check if file storage is healthy."""
        try:
            # Check if base directories exist and are writable
            if not self.base_path.exists():
                return False
            
            # Try to write a test file
            test_file = self.metadata_dir / "health_check_test.tmp"
            test_file.write_text("health check", encoding='utf-8')
            test_file.unlink()  # Delete test file
            
            return True
            
        except Exception as e:
            logger.error(f"File storage health check failed: {e}")
            return False
    
    def get_storage_info(self) -> dict:
        """Get information about the storage system."""
        path_info = self.path_manager.get_path_info()
        
        return {
            'storage_type': 'file',
            'base_path': str(self.base_path),
            'active_sessions': len(self.session_index),
            'path_manager_info': path_info,
            'directories': path_info.get('directories', {}),
            'health': self.health_check()
        }