"""
Main session manager with dual storage support.
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
    Main session manager with primary and fallback storage support.
    """
    
    def __init__(self, 
                 primary_storage: str = 'supabase',
                 fallback_storage: str = 'file',
                 auto_cleanup: bool = True,
                 cleanup_interval_hours: int = 6,
                 session_max_age_days: int = 30):
        """
        Initialize session manager with dual storage.
        
        Args:
            primary_storage: Primary storage backend ('supabase', 'file')
            fallback_storage: Fallback storage backend ('file', None for no fallback)
            auto_cleanup: Whether to start automatic cleanup
            cleanup_interval_hours: How often to run cleanup
            session_max_age_days: Maximum session age before deletion
        """
        self.primary_storage: Optional[BaseStorage] = None
        self.fallback_storage: Optional[BaseStorage] = None
        self.cleanup_tasks: Optional[SessionCleanupTasks] = None
        
        # Initialize storage backends
        try:
            self.primary_storage, self.fallback_storage = StorageFactory.create_with_fallback(
                primary_storage, fallback_storage
            )
            
            logger.info(f"Session manager initialized with primary: {primary_storage}, fallback: {fallback_storage}")
            
        except Exception as e:
            logger.error(f"Failed to initialize session manager: {e}")
            raise
        
        # Set up automatic cleanup
        if auto_cleanup and self._get_active_storage():
            try:
                self.cleanup_tasks = SessionCleanupTasks(
                    self._get_active_storage(),
                    cleanup_interval_hours,
                    session_max_age_days
                )
                self.cleanup_tasks.start_background_cleanup()
                logger.info("Automatic session cleanup enabled")
            except Exception as e:
                logger.warning(f"Failed to start automatic cleanup: {e}")
    
    def _get_active_storage(self) -> Optional[BaseStorage]:
        """Get the currently active storage backend (primary if healthy, fallback otherwise)."""
        if self.primary_storage and self.primary_storage.health_check():
            return self.primary_storage
        elif self.fallback_storage and self.fallback_storage.health_check():
            logger.warning("Primary storage unhealthy, using fallback")
            return self.fallback_storage
        else:
            logger.error("No healthy storage backend available")
            return None
    
    def _execute_with_fallback(self, operation_name: str, operation_func, *args, **kwargs):
        """
        Execute an operation with fallback support.
        
        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to call on storage backend
            *args, **kwargs: Arguments for the operation
            
        Returns:
            Result of the operation or None if all backends fail
        """
        # Try primary storage first
        if self.primary_storage:
            try:
                result = operation_func(self.primary_storage, *args, **kwargs)
                if result is not None:
                    return result
                logger.debug(f"Primary storage returned None for {operation_name}")
            except Exception as e:
                logger.warning(f"Primary storage failed for {operation_name}: {e}")
        
        # Try fallback storage
        if self.fallback_storage:
            try:
                result = operation_func(self.fallback_storage, *args, **kwargs)
                if result is not None:
                    logger.debug(f"Fallback storage succeeded for {operation_name}")
                    return result
                logger.debug(f"Fallback storage returned None for {operation_name}")
            except Exception as e:
                logger.error(f"Fallback storage failed for {operation_name}: {e}")
        
        logger.error(f"All storage backends failed for {operation_name}")
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
            created_at=now,
            last_accessed=now
        )
        
        # Store in all available backends
        success = False
        
        if self.primary_storage:
            try:
                if self.primary_storage.create_session(session_context):
                    success = True
                    logger.debug(f"Created session {session_id} in primary storage")
            except Exception as e:
                logger.warning(f"Failed to create session in primary storage: {e}")
        
        if self.fallback_storage:
            try:
                if self.fallback_storage.create_session(session_context):
                    success = True
                    logger.debug(f"Created session {session_id} in fallback storage")
            except Exception as e:
                logger.warning(f"Failed to create session in fallback storage: {e}")
        
        if success:
            logger.info(f"Created new session: {session_id}")
            return session_context
        else:
            logger.error(f"Failed to create session {session_id} in any storage")
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
        
        def get_operation(storage: BaseStorage, session_id: str):
            return storage.get_session(session_id)
        
        result = self._execute_with_fallback("get_session", get_operation, session_id)
        
        if result:
            logger.debug(f"Retrieved session: {session_id}")
        else:
            logger.debug(f"Session not found: {session_id}")
        
        return result
    
    def update_session(self, session_context: SessionContext) -> bool:
        """
        Update an existing session.
        
        Args:
            session_context: The updated session context
            
        Returns:
            True if successful in at least one backend, False otherwise
        """
        if not validate_session_id(session_context.session_id):
            logger.error(f"Invalid session ID: {session_context.session_id}")
            return False
        
        # Update last_accessed timestamp
        session_context.last_accessed = datetime.now()
        
        success = False
        
        # Update in all available backends
        if self.primary_storage:
            try:
                if self.primary_storage.update_session(session_context):
                    success = True
                    logger.debug(f"Updated session {session_context.session_id} in primary storage")
            except Exception as e:
                logger.warning(f"Failed to update session in primary storage: {e}")
        
        if self.fallback_storage:
            try:
                if self.fallback_storage.update_session(session_context):
                    success = True
                    logger.debug(f"Updated session {session_context.session_id} in fallback storage")
            except Exception as e:
                logger.warning(f"Failed to update session in fallback storage: {e}")
        
        if success:
            logger.debug(f"Updated session: {session_context.session_id}")
        else:
            logger.error(f"Failed to update session {session_context.session_id} in any storage")
        
        return success
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if successful in at least one backend, False otherwise
        """
        if not validate_session_id(session_id):
            logger.error(f"Invalid session ID: {session_id}")
            return False
        
        def delete_operation(storage: BaseStorage, session_id: str):
            return storage.delete_session(session_id)
        
        result = self._execute_with_fallback("delete_session", delete_operation, session_id)
        
        if result:
            logger.info(f"Deleted session: {session_id}")
            return True
        else:
            logger.error(f"Failed to delete session: {session_id}")
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
        def list_operation(storage: BaseStorage, limit: int, offset: int):
            return storage.list_sessions(limit, offset)
        
        result = self._execute_with_fallback("list_sessions", list_operation, limit, offset)
        
        if result is None:
            return []
        
        logger.debug(f"Listed {len(result)} sessions")
        return result
    
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
        
        return session
    
    def cleanup_expired_sessions(self, max_age: timedelta = timedelta(days=30)) -> int:
        """
        Manually trigger cleanup of expired sessions.
        
        Args:
            max_age: Maximum age before deletion
            
        Returns:
            Number of sessions deleted across all backends
        """
        total_deleted = 0
        
        if self.primary_storage:
            try:
                deleted = self.primary_storage.cleanup_expired_sessions(max_age)
                total_deleted += deleted
                logger.debug(f"Primary storage cleaned up {deleted} sessions")
            except Exception as e:
                logger.warning(f"Primary storage cleanup failed: {e}")
        
        if self.fallback_storage:
            try:
                deleted = self.fallback_storage.cleanup_expired_sessions(max_age)
                total_deleted += deleted
                logger.debug(f"Fallback storage cleaned up {deleted} sessions")
            except Exception as e:
                logger.warning(f"Fallback storage cleanup failed: {e}")
        
        if total_deleted > 0:
            logger.info(f"Cleaned up {total_deleted} expired sessions")
        
        return total_deleted
    
    def get_session_count(self) -> int:
        """
        Get total number of sessions.
        
        Returns:
            Total session count from primary storage, or fallback if primary fails
        """
        def count_operation(storage: BaseStorage):
            return storage.get_session_count()
        
        result = self._execute_with_fallback("get_session_count", count_operation)
        return result if result is not None else 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all storage backends.
        
        Returns:
            Dictionary with health status information
        """
        status = {
            'primary_storage': {
                'available': self.primary_storage is not None,
                'healthy': False,
                'type': None
            },
            'fallback_storage': {
                'available': self.fallback_storage is not None,
                'healthy': False,
                'type': None
            },
            'active_storage': None,
            'session_count': 0,
            'cleanup_status': None
        }
        
        # Check primary storage
        if self.primary_storage:
            status['primary_storage']['healthy'] = self.primary_storage.health_check()
            status['primary_storage']['type'] = type(self.primary_storage).__name__
        
        # Check fallback storage
        if self.fallback_storage:
            status['fallback_storage']['healthy'] = self.fallback_storage.health_check()
            status['fallback_storage']['type'] = type(self.fallback_storage).__name__
        
        # Determine active storage
        active_storage = self._get_active_storage()
        if active_storage:
            status['active_storage'] = type(active_storage).__name__
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


def get_session_manager(primary_storage: str = 'supabase',
                       fallback_storage: str = 'file') -> SessionManager:
    """
    Get or create the global session manager instance.
    
    Args:
        primary_storage: Primary storage backend
        fallback_storage: Fallback storage backend
        
    Returns:
        SessionManager instance
    """
    global _global_session_manager
    
    if _global_session_manager is None:
        try:
            _global_session_manager = SessionManager(
                primary_storage=primary_storage,
                fallback_storage=fallback_storage
            )
            logger.info("Global session manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize global session manager: {e}")
            raise
    
    return _global_session_manager