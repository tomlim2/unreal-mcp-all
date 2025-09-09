"""
Main session manager with database-only storage.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .session_context import SessionContext
from .storage.storage_factory import StorageFactory
from .storage.base_storage import BaseStorage
from .utils.session_helpers import generate_session_id, validate_session_id
from .utils.cleanup_tasks import SessionCleanupTasks

logger = logging.getLogger("SessionManager")


class SessionManager:
    """
    Main session manager with file-based storage for MegaMelange.
    """
    
    def __init__(self, 
                 storage_type: str = 'file',
                 auto_cleanup: bool = True,
                 cleanup_interval_hours: int = 6,
                 session_max_age_days: int = 30):
        """
        Initialize session manager with file-based storage.
        
        Args:
            storage_type: Storage backend type (default: 'file')
            auto_cleanup: Whether to start automatic cleanup
            cleanup_interval_hours: How often to run cleanup
            session_max_age_days: Maximum session age before deletion
        """
        self.storage: Optional[BaseStorage] = None
        self.cleanup_tasks: Optional[SessionCleanupTasks] = None
        
        # Initialize storage backend
        try:
            self.storage = StorageFactory.create(storage_type)
            logger.info(f"Session manager initialized with storage: {storage_type}")
            
        except Exception as e:
            logger.error(f"Failed to initialize session manager: {e}")
            raise
        
        # Set up automatic cleanup
        if auto_cleanup and self.storage:
            try:
                self.cleanup_tasks = SessionCleanupTasks(
                    self.storage,
                    cleanup_interval_hours,
                    session_max_age_days
                )
                self.cleanup_tasks.start_background_cleanup()
                logger.info("Automatic session cleanup enabled")
            except Exception as e:
                logger.warning(f"Failed to start automatic cleanup: {e}")
    
    def _get_storage(self) -> Optional[BaseStorage]:
        """Get the active storage backend."""
        if self.storage and self.storage.health_check():
            return self.storage
        else:
            logger.error("Storage backend not available or unhealthy")
            return None
    
    def create_session(self, session_id: str = None) -> Optional[SessionContext]:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID. If None, generates a new one.
            
        Returns:
            SessionContext if successful, None otherwise
        """
        if session_id is None:
            session_id = generate_session_id()
        elif not validate_session_id(session_id):
            logger.error(f"Invalid session ID: {session_id}")
            return None
        
        # Check if session already exists
        if self.get_session(session_id) is not None:
            logger.warning(f"Session {session_id} already exists")
            return None
        
        # Create new session context
        now = datetime.now()
        session_context = SessionContext(
            session_id=session_id,
            session_name="New Session",
            llm_model="gemini-2",
            created_at=now,
            last_accessed=now
        )
        
        # Store in database
        storage = self._get_storage()
        if not storage:
            logger.error("No healthy storage backend available")
            return None
        
        try:
            if storage.create_session(session_context):
                logger.info(f"Created new session: {session_id}")
                return session_context
            else:
                logger.error(f"Failed to create session {session_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to create session in storage: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            SessionContext if found, None otherwise
        """
        if not validate_session_id(session_id):
            logger.error(f"Invalid session ID: {session_id}")
            return None
        
        storage = self._get_storage()
        if not storage:
            return None
        
        try:
            result = storage.get_session(session_id)
            if result:
                logger.debug(f"Retrieved session: {session_id}")
            else:
                logger.debug(f"Session not found: {session_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def update_session(self, session_context: SessionContext) -> bool:
        """
        Update an existing session.
        
        Args:
            session_context: The updated session context
            
        Returns:
            True if successful, False otherwise
        """
        if not validate_session_id(session_context.session_id):
            logger.error(f"Invalid session ID: {session_context.session_id}")
            return False
        
        # Update last_accessed timestamp
        session_context.last_accessed = datetime.now()
        
        storage = self._get_storage()
        if not storage:
            logger.error("No healthy storage backend available")
            return False
        
        try:
            if storage.update_session(session_context):
                logger.debug(f"Updated session: {session_context.session_id}")
                return True
            else:
                logger.error(f"Failed to update session {session_context.session_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to update session in storage: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not validate_session_id(session_id):
            logger.error(f"Invalid session ID: {session_id}")
            return False
        
        storage = self._get_storage()
        if not storage:
            logger.error("No healthy storage backend available")
            return False
        
        try:
            if storage.delete_session(session_id):
                logger.info(f"Deleted session: {session_id}")
                return True
            else:
                logger.error(f"Failed to delete session: {session_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete session in storage: {e}")
            return False
    
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[SessionContext]:
        """
        List sessions with pagination.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of SessionContext objects
        """
        storage = self._get_storage()
        if not storage:
            logger.error("No healthy storage backend available")
            return []
        
        try:
            result = storage.list_sessions(limit, offset)
            if result is None:
                return []
            logger.debug(f"Listed {len(result)} sessions")
            return result
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
    
    def add_interaction(self, session_id: str, user_input: str, ai_response: Dict[str, Any]) -> bool:
        """
        Add a complete user-AI interaction to a session.
        
        Args:
            session_id: The session ID
            user_input: The user's input
            ai_response: The AI's response (from NLP processing)
            
        Returns:
            True if successful, False otherwise
        """
        # Get or create session
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
            if session is None:
                logger.error(f"Failed to create session for interaction: {session_id}")
                return False
        
        # Add the interaction
        session.add_interaction(user_input, ai_response)
        
        # Update the session
        return self.update_session(session)
    
    def get_or_create_session(self, session_id: str = None) -> Optional[SessionContext]:
        """
        Get an existing session or create a new one.
        
        Args:
            session_id: Session ID to get/create. If None, creates new session.
            
        Returns:
            SessionContext if successful, None otherwise
        """
        if session_id is None:
            return self.create_session()
        
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
            # If create_session failed because session already exists,
            # try to get it again (race condition protection)
            if session is None:
                session = self.get_session(session_id)
        
        return session
    
    def update_job_status(self, session_id: str, job_id: str, job_status: str, 
                         content: str = None, job_progress: int = None, 
                         image_url: str = None) -> bool:
        """
        Update job status in session conversation history.
        
        Args:
            session_id: The session ID
            job_id: The job ID to update
            job_status: New job status ('pending', 'running', 'completed', 'failed')
            content: Optional content for the job message
            job_progress: Optional progress percentage (0-100)
            image_url: Optional image URL when job completes
            
        Returns:
            True if successful, False otherwise
        """
        # Get session
        session = self.get_session(session_id)
        if session is None:
            logger.error(f"Session not found for job update: {session_id}")
            return False
        
        # Update job message in conversation history
        default_content = {
            'pending': f"Screenshot job {job_id} is starting...",
            'running': f"Processing screenshot job {job_id}...",
            'completed': f"Screenshot job {job_id} completed successfully!",
            'failed': f"Screenshot job {job_id} failed"
        }.get(job_status, f"Job {job_id} status: {job_status}")
        
        session.update_job_message(
            job_id=job_id,
            job_status=job_status,
            content=content or default_content,
            job_progress=job_progress,
            image_url=image_url
        )
        
        # Update the session in storage
        success = self.update_session(session)
        if success:
            logger.info(f"Updated job {job_id} status to {job_status} in session {session_id}")
        else:
            logger.error(f"Failed to update job {job_id} status in session {session_id}")
        
        return success
    
    
    def cleanup_expired_sessions(self, max_age: timedelta = timedelta(days=30)) -> int:
        """
        Manually trigger cleanup of expired sessions.
        
        Args:
            max_age: Maximum age before deletion
            
        Returns:
            Number of sessions deleted
        """
        storage = self._get_storage()
        if not storage:
            logger.error("No healthy storage backend available")
            return 0
        
        try:
            deleted = storage.cleanup_expired_sessions(max_age)
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired sessions")
            return deleted
        except Exception as e:
            logger.error(f"Storage cleanup failed: {e}")
            return 0
    
    def get_session_count(self) -> int:
        """
        Get total number of sessions.
        
        Returns:
            Total session count
        """
        storage = self._get_storage()
        if not storage:
            return 0
        
        try:
            return storage.get_session_count()
        except Exception as e:
            logger.error(f"Failed to get session count: {e}")
            return 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of storage backend.
        
        Returns:
            Dictionary with health status information
        """
        status = {
            'storage': {
                'available': self.storage is not None,
                'healthy': False,
                'type': None
            },
            'session_count': 0,
            'cleanup_status': None
        }
        
        # Check storage
        if self.storage:
            status['storage']['healthy'] = self.storage.health_check()
            status['storage']['type'] = type(self.storage).__name__
            
            if status['storage']['healthy']:
                status['session_count'] = self.get_session_count()
        
        # Get cleanup status
        if self.cleanup_tasks:
            status['cleanup_status'] = self.cleanup_tasks.get_cleanup_status()
        
        return status
    
    def shutdown(self):
        """Clean shutdown of session manager."""
        if self.cleanup_tasks:
            self.cleanup_tasks.stop_background_cleanup()
            logger.info("Stopped background cleanup")
        
        logger.info("Session manager shutdown complete")


# Global session manager instance
_global_session_manager: Optional[SessionManager] = None


def get_session_manager(storage_type: str = 'file') -> SessionManager:
    """
    Get or create the global session manager instance.
    
    Args:
        storage_type: Storage backend type (default: 'file')
        
    Returns:
        SessionManager instance
    """
    global _global_session_manager
    
    if _global_session_manager is None:
        try:
            _global_session_manager = SessionManager(
                storage_type=storage_type
            )
            logger.info("Global session manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize global session manager: {e}")
            raise
    
    return _global_session_manager