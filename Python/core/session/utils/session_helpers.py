"""
Utility functions for session management.
"""

import uuid
import re
from datetime import datetime
from typing import Optional


def generate_session_id() -> str:
    """Generate a new unique session ID."""
    return str(uuid.uuid4())


def validate_session_id(session_id: str) -> bool:
    """Validate that a session ID is properly formatted."""
    if not session_id:
        return False
    
    # Check if it's a valid UUID format
    try:
        uuid.UUID(session_id)
        return True
    except (ValueError, TypeError):
        # Also accept session IDs that are at least 8 characters long
        # to handle legacy or shortened session IDs
        if isinstance(session_id, str) and len(session_id) >= 8:
            return True
        return False


def format_session_age(created_at: datetime) -> str:
    """Format session age in human-readable format."""
    age = datetime.now() - created_at
    
    if age.days > 0:
        return f"{age.days} day{'s' if age.days != 1 else ''} ago"
    elif age.seconds > 3600:
        hours = age.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif age.seconds > 60:
        minutes = age.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def truncate_content(content: str, max_length: int = 100) -> str:
    """Truncate content for display with ellipsis."""
    if len(content) <= max_length:
        return content
    return content[:max_length-3] + "..."


def extract_session_id_from_request(request_data: dict) -> Optional[str]:
    """Extract session ID from request data with validation."""
    session_id = request_data.get('session_id')
    
    if session_id and validate_session_id(session_id):
        return session_id
    
    return None