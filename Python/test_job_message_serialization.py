#!/usr/bin/env python3
"""
Test script to verify job message serialization includes image_url
"""

import sys
from pathlib import Path
import json

# Add the Python directory to the path
python_dir = Path(__file__).parent
sys.path.insert(0, str(python_dir))

from tools.ai.session_management.session_context import ChatMessage
from datetime import datetime

def test_job_message_serialization():
    """Test that job messages with image_url serialize correctly for frontend"""
    
    # Create a job message with image_url
    job_message = ChatMessage(
        timestamp=datetime.now(),
        role='job',
        content='Screenshot completed successfully',
        job_id='test_job_123',
        job_info={
            'job_status': 'completed',
            'job_progress': 100,
            'image_url': 'http://localhost:8080/api/screenshot/download/test_job_123'
        }
    )
    
    # Convert to dict (what gets sent to frontend)
    message_dict = job_message.to_dict()
    
    print("Job Message Serialization Test")
    print("=" * 50)
    print(f"Original job_info: {job_message.job_info}")
    print(f"Serialized message dict:")
    print(json.dumps(message_dict, indent=2))
    
    # Check if image_url is flattened to top level
    if 'image_url' in message_dict:
        print(f"✅ SUCCESS: image_url is available at top level: {message_dict['image_url']}")
    else:
        print("❌ FAIL: image_url not found at top level")
    
    # Check if job status fields are also flattened
    if 'job_status' in message_dict and 'job_progress' in message_dict:
        print(f"✅ SUCCESS: job fields flattened - status: {message_dict['job_status']}, progress: {message_dict['job_progress']}")
    else:
        print("❌ FAIL: job status fields not properly flattened")

if __name__ == "__main__":
    test_job_message_serialization()