#!/usr/bin/env python3
"""
Fix existing job messages to use Next.js proxy URLs instead of direct HTTP bridge URLs
"""

import sys
from pathlib import Path
import re

# Add the Python directory to the path
python_dir = Path(__file__).parent
sys.path.insert(0, str(python_dir))

from tools.ai.session_management import get_session_manager

def fix_job_urls_to_proxy():
    """Fix existing job messages to use proxy URLs"""
    
    session_manager = get_session_manager()
    
    # Get all sessions
    sessions = session_manager.list_sessions()
    print(f"Found {len(sessions)} sessions")
    
    fixed_count = 0
    total_jobs = 0
    
    for session in sessions:
        session_id = session.session_id
        print(f"\nChecking session: {session_id}")
        
        # Find job messages with direct HTTP bridge URLs
        job_messages = [msg for msg in session.conversation_history if msg.role == 'job']
        print(f"  Found {len(job_messages)} job messages")
        
        session_updated = False
        
        for msg in job_messages:
            total_jobs += 1
            if msg.job_info and 'image_url' in msg.job_info:
                image_url = msg.job_info['image_url']
                
                # Check if it's a direct HTTP bridge URL that needs fixing
                if image_url and 'localhost:8080/api/screenshot/download/' in image_url:
                    print(f"  Fixing direct URL: {image_url}")
                    
                    # Extract job ID from URL
                    match = re.search(r'/api/screenshot/download/([a-f0-9-]+)', image_url)
                    if match:
                        job_id = match.group(1)
                        # Convert to proxy URL
                        proxy_url = f"/api/screenshot/{job_id}"
                        msg.job_info['image_url'] = proxy_url
                        fixed_count += 1
                        session_updated = True
                        print(f"    Fixed to proxy URL: {proxy_url}")
        
        # Save session if updated
        if session_updated:
            print(f"  Saving updated session: {session_id}")
            session_manager.update_session(session)
    
    print(f"\n=== Summary ===")
    print(f"Total sessions checked: {len(sessions)}")
    print(f"Total job messages: {total_jobs}")
    print(f"Fixed to proxy URLs: {fixed_count}")
    
    return fixed_count

if __name__ == "__main__":
    fixed_count = fix_job_urls_to_proxy()
    print(f"\n✅ Fixed {fixed_count} job message URLs to use Next.js proxy")