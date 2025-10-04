"""
Background cleanup tasks for session management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import threading
import time

from ..storage.base_storage import BaseStorage

logger = logging.getLogger("SessionManager.Cleanup")


class SessionCleanupTasks:
    """Handles background cleanup tasks for session management."""
    
    def __init__(self, storage: BaseStorage, cleanup_interval_hours: int = 6, 
                 session_max_age_days: int = 30):
        """
        Initialize cleanup tasks.
        
        Args:
            storage: Storage backend to clean up
            cleanup_interval_hours: How often to run cleanup (in hours)
            session_max_age_days: Maximum age for sessions before deletion
        """
        self.storage = storage
        self.cleanup_interval = timedelta(hours=cleanup_interval_hours)
        self.session_max_age = timedelta(days=session_max_age_days)
        self.running = False
        self.cleanup_thread: Optional[threading.Thread] = None
        self.last_cleanup: Optional[datetime] = None
        
        logger.info(f"Cleanup tasks initialized - interval: {cleanup_interval_hours}h, max age: {session_max_age_days}d")
    
    def start_background_cleanup(self):
        """Start background cleanup thread."""
        if self.running:
            logger.warning("Cleanup tasks already running")
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("Background cleanup tasks started")
    
    def stop_background_cleanup(self):
        """Stop background cleanup thread."""
        if not self.running:
            return
        
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=10)
        
        logger.info("Background cleanup tasks stopped")
    
    def _cleanup_loop(self):
        """Main cleanup loop running in background thread."""
        while self.running:
            try:
                # Check if it's time for cleanup
                now = datetime.now()
                if (self.last_cleanup is None or 
                    now - self.last_cleanup >= self.cleanup_interval):
                    
                    logger.debug("Running scheduled cleanup")
                    self.run_cleanup()
                    self.last_cleanup = now
                
                # Sleep for a short interval before checking again
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def run_cleanup(self) -> dict:
        """
        Run cleanup tasks manually.
        
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'expired_sessions_deleted': 0,
            'cleanup_time': datetime.now().isoformat(),
            'errors': []
        }
        
        try:
            logger.info("Starting session cleanup")
            
            # Clean up expired sessions
            deleted_count = self.storage.cleanup_expired_sessions(self.session_max_age)
            stats['expired_sessions_deleted'] = deleted_count
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired sessions")
            else:
                logger.debug("No expired sessions found")
            
            # Additional cleanup tasks can be added here
            # For example: compress old sessions, generate reports, etc.
            
        except Exception as e:
            error_msg = f"Error during cleanup: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
        
        logger.debug(f"Cleanup completed: {stats}")
        return stats
    
    def get_cleanup_status(self) -> dict:
        """
        Get current cleanup status.
        
        Returns:
            Dictionary with cleanup status information
        """
        return {
            'running': self.running,
            'last_cleanup': self.last_cleanup.isoformat() if self.last_cleanup else None,
            'next_cleanup_due': (self.last_cleanup + self.cleanup_interval).isoformat() if self.last_cleanup else "Now",
            'cleanup_interval_hours': self.cleanup_interval.total_seconds() / 3600,
            'session_max_age_days': self.session_max_age.days,
            'storage_healthy': self.storage.health_check()
        }
    
    def force_cleanup_now(self) -> dict:
        """
        Force cleanup to run immediately.
        
        Returns:
            Dictionary with cleanup results
        """
        logger.info("Forcing immediate cleanup")
        return self.run_cleanup()


class SessionMaintenanceTasks:
    """Additional maintenance tasks for sessions."""
    
    def __init__(self, storage: BaseStorage):
        """
        Initialize maintenance tasks.
        
        Args:
            storage: Storage backend to maintain
        """
        self.storage = storage
    
    def compress_old_conversations(self, age_threshold_days: int = 7, 
                                  max_messages_to_keep: int = 10) -> int:
        """
        Compress conversation history in old sessions to save space.
        
        Args:
            age_threshold_days: Sessions older than this will be compressed
            max_messages_to_keep: Maximum messages to keep after compression
            
        Returns:
            Number of sessions compressed
        """
        try:
            logger.info(f"Starting conversation compression for sessions older than {age_threshold_days} days")
            
            sessions = self.storage.list_sessions(limit=1000)  # Process in batches
            compressed_count = 0
            cutoff_date = datetime.now() - timedelta(days=age_threshold_days)
            
            for session in sessions:
                if session.created_at < cutoff_date and len(session.conversation_history) > max_messages_to_keep:
                    # Keep only the most recent messages
                    original_count = len(session.conversation_history)
                    session.conversation_history = session.conversation_history[-max_messages_to_keep:]
                    
                    # Add a note about compression
                    session.metadata['compressed'] = True
                    session.metadata['original_message_count'] = original_count
                    session.metadata['compressed_at'] = datetime.now().isoformat()
                    
                    # Update the session
                    if self.storage.update_session(session):
                        compressed_count += 1
                        logger.debug(f"Compressed session {session.session_id}: {original_count} -> {max_messages_to_keep} messages")
            
            if compressed_count > 0:
                logger.info(f"Compressed {compressed_count} sessions")
            else:
                logger.debug("No sessions needed compression")
            
            return compressed_count
            
        except Exception as e:
            logger.error(f"Error compressing conversations: {e}")
            return 0
    
    def generate_usage_report(self) -> dict:
        """
        Generate a usage report for sessions.
        
        Returns:
            Dictionary with usage statistics
        """
        try:
            sessions = self.storage.list_sessions(limit=1000)
            
            total_sessions = len(sessions)
            total_messages = sum(len(s.conversation_history) for s in sessions)
            
            # Age distribution
            now = datetime.now()
            age_buckets = {
                'today': 0,
                'this_week': 0,
                'this_month': 0,
                'older': 0
            }
            
            for session in sessions:
                age_days = (now - session.created_at).days
                if age_days == 0:
                    age_buckets['today'] += 1
                elif age_days <= 7:
                    age_buckets['this_week'] += 1
                elif age_days <= 30:
                    age_buckets['this_month'] += 1
                else:
                    age_buckets['older'] += 1
            
            # Activity distribution
            activity_buckets = {
                'very_active': 0,    # >20 messages
                'active': 0,         # 10-20 messages
                'moderate': 0,       # 5-10 messages
                'light': 0           # <5 messages
            }
            
            for session in sessions:
                msg_count = len(session.conversation_history)
                if msg_count > 20:
                    activity_buckets['very_active'] += 1
                elif msg_count > 10:
                    activity_buckets['active'] += 1
                elif msg_count > 5:
                    activity_buckets['moderate'] += 1
                else:
                    activity_buckets['light'] += 1
            
            return {
                'report_date': now.isoformat(),
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'average_messages_per_session': round(total_messages / total_sessions, 2) if total_sessions > 0 else 0,
                'age_distribution': age_buckets,
                'activity_distribution': activity_buckets,
                'storage_healthy': self.storage.health_check()
            }
            
        except Exception as e:
            logger.error(f"Error generating usage report: {e}")
            return {'error': str(e)}