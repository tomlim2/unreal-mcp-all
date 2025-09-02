"""
Supabase storage backend for session management.
"""

import os
import json
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from .base_storage import BaseStorage
from ..session_context import SessionContext

# Configure logging
logger = logging.getLogger("SessionManager.Supabase")
datatable_user_sessions_name = "chat_context"

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase library not available. Install with: pip install supabase")


class SupabaseStorage(BaseStorage):
    """Supabase implementation of session storage."""
    
    def __init__(self):
        """Initialize Supabase client."""
        if not SUPABASE_AVAILABLE:
            raise RuntimeError("Supabase library not available. Install with: pip install supabase")
        
        # Get credentials from environment
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError(
                "Supabase credentials not found. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
            )
        
        try:
            self.supabase: Client = create_client(url, key)
            logger.info("Supabase client initialized successfully")
            
            # Test connection
            if not self.health_check():
                raise RuntimeError("Failed to connect to Supabase")
                
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def create_session(self, session_context: SessionContext) -> bool:
        """Create a new session in Supabase."""
        try:
            data = {
                'session_id': session_context.session_id,
                'session_name': getattr(session_context, 'session_name', None),
                'llm_model': getattr(session_context, 'llm_model', 'gemini-2'),
                'context': json.dumps(session_context.to_dict()),
                'created_at': session_context.created_at.isoformat(),
                'last_accessed': session_context.last_accessed.isoformat()
            }
            
            result = self.supabase.table(datatable_user_sessions_name).insert(data).execute()
            
            if result.data:
                logger.info(f"Created session {session_context.session_id}")
                return True
            else:
                logger.error(f"Failed to create session {session_context.session_id}: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error creating session {session_context.session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Retrieve a session from Supabase."""
        try:
            result = self.supabase.table(datatable_user_sessions_name)\
                .select('*')\
                .eq('session_id', session_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                session_data = result.data[0]
                context_dict = json.loads(session_data['context'])
                
                # Add session_name to context if available
                if session_data.get('session_name'):
                    context_dict['session_name'] = session_data['session_name']
                
                # Add llm_model to context if available
                if session_data.get('llm_model'):
                    context_dict['llm_model'] = session_data['llm_model']
                
                # Update last_accessed timestamp
                self.supabase.table(datatable_user_sessions_name)\
                    .update({'last_accessed': datetime.now().isoformat()})\
                    .eq('session_id', session_id)\
                    .execute()
                
                logger.debug(f"Retrieved session {session_id}")
                return SessionContext.from_dict(context_dict)
            else:
                logger.debug(f"Session {session_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    def update_session(self, session_context: SessionContext) -> bool:
        """Update an existing session in Supabase."""
        try:
            # Update last_accessed timestamp
            session_context.last_accessed = datetime.now()
            
            data = {
                'context': json.dumps(session_context.to_dict()),
                'session_name': getattr(session_context, 'session_name', None),
                'llm_model': getattr(session_context, 'llm_model', 'gemini-2'),
                'last_accessed': session_context.last_accessed.isoformat()
            }
            
            result = self.supabase.table(datatable_user_sessions_name)\
                .update(data)\
                .eq('session_id', session_context.session_id)\
                .execute()
            
            if result.data:
                logger.debug(f"Updated session {session_context.session_id}")
                return True
            else:
                logger.error(f"Failed to update session {session_context.session_id}: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error updating session {session_context.session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from Supabase."""
        try:
            result = self.supabase.table(datatable_user_sessions_name)\
                .delete()\
                .eq('session_id', session_id)\
                .execute()
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[SessionContext]:
        """List sessions with pagination."""
        try:
            result = self.supabase.table(datatable_user_sessions_name)\
                .select('*')\
                .order('last_accessed', desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            sessions = []
            for session_data in result.data:
                try:
                    context_dict = json.loads(session_data['context'])
                    
                    # Add session_name to context if available
                    if session_data.get('session_name'):
                        context_dict['session_name'] = session_data['session_name']
                    
                    sessions.append(SessionContext.from_dict(context_dict))
                except Exception as e:
                    logger.warning(f"Failed to parse session {session_data.get('session_id', 'unknown')}: {e}")
            
            logger.debug(f"Retrieved {len(sessions)} sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    def update_session_name(self, session_id: str, session_name: str) -> bool:
        """Update just the session name for a specific session."""
        try:
            result = self.supabase.table(datatable_user_sessions_name)\
                .update({'session_name': session_name})\
                .eq('session_id', session_id)\
                .execute()
            
            if result.data:
                logger.debug(f"Updated session name for {session_id}")
                return True
            else:
                logger.error(f"Failed to update session name for {session_id}: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error updating session name for {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self, max_age: timedelta = timedelta(days=30)) -> int:
        """Remove sessions older than max_age."""
        try:
            cutoff_time = datetime.now() - max_age
            
            # Get sessions to delete (for counting)
            expired_sessions = self.supabase.table(datatable_user_sessions_name)\
                .select('session_id')\
                .lt('last_accessed', cutoff_time.isoformat())\
                .execute()
            
            count = len(expired_sessions.data) if expired_sessions.data else 0
            
            if count > 0:
                # Delete expired sessions
                self.supabase.table(datatable_user_sessions_name)\
                    .delete()\
                    .lt('last_accessed', cutoff_time.isoformat())\
                    .execute()
                
                logger.info(f"Cleaned up {count} expired sessions")
            else:
                logger.debug("No expired sessions to clean up")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    def get_session_count(self) -> int:
        """Get total number of sessions."""
        try:
            result = self.supabase.table(datatable_user_sessions_name)\
                .select('session_id', count='exact')\
                .execute()
            
            return result.count if result.count is not None else 0
            
        except Exception as e:
            logger.error(f"Error getting session count: {e}")
            return 0
    
    def health_check(self) -> bool:
        """Check if Supabase is accessible."""
        try:
            # Simple query to test connection
            result = self.supabase.table(datatable_user_sessions_name)\
                .select('session_id')\
                .limit(1)\
                .execute()
            
            logger.debug("Supabase health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False
    
    def create_table_if_not_exists(self) -> bool:
        """
        Create the sessions table if it doesn't exist.
        Note: This requires admin privileges in Supabase.
        Typically the table should be created manually in the Supabase dashboard.
        """
        try:
            # This is just for reference - actual table creation should be done via Supabase dashboard
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_id TEXT UNIQUE NOT NULL,
                context JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_accessed TIMESTAMPTZ DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_last_accessed ON sessions(last_accessed);
            """
            
            logger.info("Table creation SQL (run this in Supabase dashboard):")
            logger.info(create_table_sql)
            
            return True
            
        except Exception as e:
            logger.error(f"Error with table creation reference: {e}")
            return False