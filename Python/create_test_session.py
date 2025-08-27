#!/usr/bin/env python3
"""Create a test session to verify Supabase storage."""

import os
from dotenv import load_dotenv
load_dotenv()

def create_test_session():
    try:
        from tools.ai.session_management import get_session_manager
        
        session_manager = get_session_manager()
        
        # Create test session
        test_session = session_manager.create_session()
        print(f"✅ Created test session: {test_session.session_id}")
        
        # Add test interaction
        test_response = {
            "explanation": "Testing Supabase database storage",
            "commands": [{"type": "test_command", "params": {"test": True}}],
            "executionResults": [{"command": "test_command", "success": True, "result": {"status": "test"}}]
        }
        
        success = session_manager.add_interaction(
            test_session.session_id,
            "Test message to verify Supabase storage",
            test_response
        )
        
        if success:
            print(f"✅ Test interaction added successfully!")
            print(f"Session ID: {test_session.session_id}")
            
            # Check session count
            count = session_manager.get_session_count()
            print(f"Total sessions in active storage: {count}")
            
        else:
            print("❌ Failed to add test interaction")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_test_session()