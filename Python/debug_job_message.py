#!/usr/bin/env python3
"""
Debug script to check job message in session database
"""

import sys
from pathlib import Path
import json

# Add the Python directory to the path
python_dir = Path(__file__).parent
sys.path.insert(0, str(python_dir))

from tools.ai.session_management import get_session_manager

def debug_latest_job_message():
    """Debug the latest job message to see its structure"""
    
    session_manager = get_session_manager()
    
    # Get sessions
    sessions = session_manager.list_sessions()
    if not sessions:
        print("No sessions found")
        return
        
    print(f"Found {len(sessions)} sessions")
    
    # Get the most recent session
    latest_session = sessions[0]  # Assuming sessions are ordered by recency
    session_id = latest_session.session_id
    print(f"Checking session: {session_id}")
    
    # The session is already a SessionContext object
    session_context = latest_session
    
    print(f"Session has {len(session_context.conversation_history)} messages")
    
    # Find job messages
    job_messages = [msg for msg in session_context.conversation_history if msg.role == 'job']
    print(f"Found {len(job_messages)} job messages")
    
    if job_messages:
        latest_job = job_messages[-1]  # Get the most recent job message
        print("\nLatest Job Message:")
        print("=" * 50)
        print(f"Role: {latest_job.role}")
        print(f"Content: {latest_job.content}")
        print(f"Job ID: {latest_job.job_id}")
        print(f"Job Info: {latest_job.job_info}")
        
        # Convert to dict (what frontend receives)
        job_dict = latest_job.to_dict()
        print("\nSerialized for Frontend:")
        print("=" * 50)
        print(json.dumps(job_dict, indent=2))
        
        # Check for image_url
        if 'image_url' in job_dict:
            print(f"\n✅ image_url found: {job_dict['image_url']}")
            
            # Try to make a HEAD request to check if URL is accessible
            try:
                import requests
                response = requests.head(job_dict['image_url'], timeout=5)
                print(f"URL status: {response.status_code}")
            except Exception as e:
                print(f"URL test failed: {e}")
        else:
            print("\n❌ image_url not found in serialized message")

if __name__ == "__main__":
    debug_latest_job_message()