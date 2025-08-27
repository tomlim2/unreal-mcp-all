"""
File-based storage backend for session management (fallback option).
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from .base_storage import BaseStorage
from ..session_context import SessionContext

# Configure logging
logger = logging.getLogger("SessionManager.File")


class FileStorage(BaseStorage):
    """File-based implementation of session storage."""
    
    def __init__(self, base_path: str = None):
        """
        Initialize file storage.
        
        Args:
            base_path: Base directory for session files. If None, uses Python/sessions/
        """
        if base_path is None:
            # Default to Python/sessions/ directory
            script_dir = Path(__file__).parent.parent.parent.parent  # Go up to Python/
            base_path = script_dir / "sessions"
        
        self.base_path = Path(base_path)
        self.active_path = self.base_path / "active"
        self.archived_path = self.base_path / "archived"
        
        # Create directory structure
        self._ensure_directories()
        
        logger.info(f"File storage initialized at {self.base_path}")
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.active_path.mkdir(parents=True, exist_ok=True)
            self.archived_path.mkdir(parents=True, exist_ok=True)
            
            # Create .gitignore to prevent committing session files
            gitignore_path = self.base_path / ".gitignore"
            if not gitignore_path.exists():
                with open(gitignore_path, 'w') as f:
                    f.write("# Ignore all session files\n*\n!.gitignore\n")
            
        except Exception as e:
            logger.error(f"Failed to create session directories: {e}")
            raise
    
    def _get_session_file_path(self, session_id: str, created_at: datetime) -> Path:
        """
        Get the file path for a session based on its age.
        
        Args:
            session_id: The session ID
            created_at: When the session was created
            
        Returns:
            Path to the session file
        """
        age_days = (datetime.now() - created_at).days
        
        if age_days <= 7:  # Active sessions (last 7 days)
            year_month = created_at.strftime('%Y-%m')
            day = f"day-{created_at.day:02d}"
            
            # Create month and day directories if needed
            month_path = self.active_path / year_month
            day_path = month_path / day
            day_path.mkdir(parents=True, exist_ok=True)
            
            return day_path / f"{session_id}.json"
        else:  # Archived sessions
            year_month = created_at.strftime('%Y-%m')
            month_path = self.archived_path / year_month
            month_path.mkdir(parents=True, exist_ok=True)
            
            return month_path / f"{session_id}.json"
    
    def _find_session_file(self, session_id: str) -> Optional[Path]:
        """
        Find a session file by searching both active and archived directories.
        
        Args:
            session_id: The session ID to find
            
        Returns:
            Path to the session file if found, None otherwise
        """
        # Search in active directory first (more likely to be found here)
        for root, dirs, files in os.walk(self.active_path):
            if f"{session_id}.json" in files:
                return Path(root) / f"{session_id}.json"
        
        # Search in archived directory
        for root, dirs, files in os.walk(self.archived_path):
            if f"{session_id}.json" in files:
                return Path(root) / f"{session_id}.json"
        
        return None
    
    def create_session(self, session_context: SessionContext) -> bool:
        """Create a new session file."""
        try:
            file_path = self._get_session_file_path(session_context.session_id, session_context.created_at)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_context.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created session file {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session {session_context.session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Retrieve a session from file."""
        try:
            file_path = self._find_session_file(session_id)
            
            if file_path is None or not file_path.exists():
                logger.debug(f"Session file not found for {session_id}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session_context = SessionContext.from_dict(data)
            
            # Update last_accessed and save
            session_context.last_accessed = datetime.now()
            self.update_session(session_context)
            
            logger.debug(f"Retrieved session {session_id} from {file_path}")
            return session_context
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    def update_session(self, session_context: SessionContext) -> bool:
        """Update an existing session file."""
        try:
            file_path = self._find_session_file(session_context.session_id)
            
            if file_path is None:
                # Session doesn't exist, create it
                return self.create_session(session_context)
            
            # Update last_accessed timestamp
            session_context.last_accessed = datetime.now()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_context.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Updated session file {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session_context.session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session file."""
        try:
            file_path = self._find_session_file(session_id)
            
            if file_path is None or not file_path.exists():
                logger.warning(f"Session file not found for deletion: {session_id}")
                return False
            
            file_path.unlink()
            logger.info(f"Deleted session file {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[SessionContext]:
        """List sessions from files with pagination."""
        try:
            sessions = []
            session_files = []
            
            # Collect all session files
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith('.json') and file != '.gitignore':
                        session_files.append(Path(root) / file)
            
            # Sort by modification time (most recent first)
            session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Apply pagination
            paginated_files = session_files[offset:offset + limit]
            
            for file_path in paginated_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    sessions.append(SessionContext.from_dict(data))
                except Exception as e:
                    logger.warning(f"Failed to parse session file {file_path}: {e}")
            
            logger.debug(f"Retrieved {len(sessions)} sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    def cleanup_expired_sessions(self, max_age: timedelta = timedelta(days=30)) -> int:
        """Remove session files older than max_age."""
        try:
            cutoff_time = datetime.now() - max_age
            deleted_count = 0
            
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith('.json'):
                        file_path = Path(root) / file
                        
                        try:
                            # Check file modification time
                            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            
                            if file_mtime < cutoff_time:
                                file_path.unlink()
                                deleted_count += 1
                                logger.debug(f"Deleted expired session file {file_path}")
                                
                        except Exception as e:
                            logger.warning(f"Error processing file {file_path}: {e}")
            
            # Clean up empty directories
            self._cleanup_empty_directories()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired session files")
            else:
                logger.debug("No expired session files to clean up")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    def _cleanup_empty_directories(self):
        """Remove empty directories in the session storage."""
        try:
            for root, dirs, files in os.walk(self.base_path, topdown=False):
                root_path = Path(root)
                
                # Skip the base directories
                if root_path in [self.base_path, self.active_path, self.archived_path]:
                    continue
                
                # If directory is empty, remove it
                if not any(root_path.iterdir()):
                    root_path.rmdir()
                    logger.debug(f"Removed empty directory {root_path}")
                    
        except Exception as e:
            logger.warning(f"Error cleaning up empty directories: {e}")
    
    def get_session_count(self) -> int:
        """Get total number of session files."""
        try:
            count = 0
            
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith('.json') and file != '.gitignore':
                        count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting session count: {e}")
            return 0
    
    def health_check(self) -> bool:
        """Check if file storage is accessible."""
        try:
            # Test if we can read/write to the base directory
            test_file = self.base_path / ".health_check"
            
            with open(test_file, 'w') as f:
                f.write("health_check")
            
            with open(test_file, 'r') as f:
                content = f.read()
            
            test_file.unlink()
            
            if content == "health_check":
                logger.debug("File storage health check passed")
                return True
            else:
                logger.error("File storage health check failed: content mismatch")
                return False
                
        except Exception as e:
            logger.error(f"File storage health check failed: {e}")
            return False
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics for debugging."""
        try:
            active_count = 0
            archived_count = 0
            total_size = 0
            
            # Count active sessions
            for root, dirs, files in os.walk(self.active_path):
                for file in files:
                    if file.endswith('.json'):
                        active_count += 1
                        file_path = Path(root) / file
                        total_size += file_path.stat().st_size
            
            # Count archived sessions
            for root, dirs, files in os.walk(self.archived_path):
                for file in files:
                    if file.endswith('.json'):
                        archived_count += 1
                        file_path = Path(root) / file
                        total_size += file_path.stat().st_size
            
            return {
                'active_sessions': active_count,
                'archived_sessions': archived_count,
                'total_sessions': active_count + archived_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}