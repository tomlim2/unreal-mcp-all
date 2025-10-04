"""
Abstract base class for session storage backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime, timedelta

from ..session_context import SessionContext


class BaseStorage(ABC):
    """Abstract base class for session storage implementations."""
    
    @abstractmethod
    def create_session(self, session_context: SessionContext) -> bool:
        """
        Create a new session.
        
        Args:
            session_context: The session context to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            SessionContext if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update_session(self, session_context: SessionContext) -> bool:
        """
        Update an existing session.
        
        Args:
            session_context: The updated session context
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[SessionContext]:
        """
        List sessions with pagination.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of SessionContext objects
        """
        pass
    
    @abstractmethod
    def cleanup_expired_sessions(self, max_age: timedelta = timedelta(days=30)) -> int:
        """
        Remove sessions older than max_age.
        
        Args:
            max_age: Maximum age before deletion
            
        Returns:
            Number of sessions deleted
        """
        pass
    
    @abstractmethod
    def get_session_count(self) -> int:
        """
        Get total number of sessions.
        
        Returns:
            Total session count
        """
        pass
    
    def health_check(self) -> bool:
        """
        Check if the storage backend is healthy and accessible.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Default implementation - try to get session count
            self.get_session_count()
            return True
        except Exception:
            return False