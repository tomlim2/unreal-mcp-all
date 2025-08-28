#!/usr/bin/env python3
"""
Check if chat sessions are being saved to Supabase database.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database_sessions():
    """Check what sessions are stored in Supabase."""
    print("🔍 Checking Supabase Database for Chat Sessions...")
    
    try:
        from supabase import create_client
        
        # Connect to Supabase
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        supabase = create_client(url, key)
        
        # Get all sessions
        result = supabase.table('user_sessions').select('*').order('last_accessed', desc=True).execute()
        
        if not result.data:
            print("📭 No sessions found in database")
            return
        
        print(f"📊 Found {len(result.data)} session(s) in database:")
        print("-" * 80)
        
        for i, session in enumerate(result.data, 1):
            # Parse the context
            context = json.loads(session['context']) if isinstance(session['context'], str) else session['context']
            
            print(f"🔹 Session {i}:")
            print(f"   ID: {session['session_id']}")
            print(f"   Created: {session['created_at']}")
            print(f"   Last Access: {session['last_accessed']}")
            
            # Show conversation history
            conv_history = context.get('conversation_history', [])
            print(f"   Messages: {len(conv_history)}")
            
            if conv_history:
                print(f"   Recent Messages:")
                for j, msg in enumerate(conv_history[-3:], 1):  # Show last 3 messages
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:50] + "..." if len(msg.get('content', '')) > 50 else msg.get('content', '')
                    timestamp = msg.get('timestamp', 'unknown')
                    print(f"     {j}. [{role}] {content} ({timestamp})")
            
            # Show scene state
            scene_state = context.get('scene_state', {})
            lights = scene_state.get('lights', [])
            sky_settings = scene_state.get('sky_settings', {})
            cesium_location = scene_state.get('cesium_location')
            
            print(f"   Scene State:")
            print(f"     Lights: {len(lights)}")
            print(f"     Sky Settings: {len(sky_settings)} items")
            print(f"     Cesium Location: {'Yes' if cesium_location else 'No'}")
            
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def check_file_sessions():
    """Check what sessions are stored in local files."""
    print("\n🔍 Checking Local File Storage for Chat Sessions...")
    
    try:
        from tools.ai.session_management.storage.file_storage import FileStorage
        
        file_storage = FileStorage()
        stats = file_storage.get_storage_stats()
        
        print(f"📊 Local File Storage Stats:")
        print(f"   Active Sessions: {stats.get('active_sessions', 0)}")
        print(f"   Archived Sessions: {stats.get('archived_sessions', 0)}")
        print(f"   Total Size: {stats.get('total_size_mb', 0)} MB")
        
        # List recent sessions
        sessions = file_storage.list_sessions(limit=5)
        if sessions:
            print(f"\n📝 Recent Local Sessions:")
            for i, session in enumerate(sessions, 1):
                print(f"   {i}. {session.session_id} - {len(session.conversation_history)} messages")
        else:
            print("📭 No local sessions found")
            
    except Exception as e:
        print(f"❌ Error checking local files: {e}")

def check_session_manager_status():
    """Check the current session manager status."""
    print("\n🔍 Checking Session Manager Status...")
    
    try:
        from tools.ai.session_management import get_session_manager
        
        session_manager = get_session_manager()
        health_status = session_manager.get_health_status()
        
        print(f"📊 Session Manager Health:")
        print(f"   Primary Storage (Supabase): {'✅ Healthy' if health_status['primary_storage']['healthy'] else '❌ Unhealthy'}")
        print(f"   Fallback Storage (File): {'✅ Healthy' if health_status['fallback_storage']['healthy'] else '❌ Unhealthy'}")
        print(f"   Active Storage: {health_status['active_storage']}")
        print(f"   Total Session Count: {health_status['session_count']}")
        
        if health_status.get('cleanup_status'):
            cleanup = health_status['cleanup_status']
            print(f"   Cleanup Running: {cleanup.get('running', False)}")
            print(f"   Last Cleanup: {cleanup.get('last_cleanup', 'Never')}")
        
    except Exception as e:
        print(f"❌ Error checking session manager: {e}")

def simulate_test_session():
    """Create a test session to verify database storage."""
    print("\n🧪 Creating Test Session...")
    
    try:
        from tools.ai.session_management import get_session_manager
        
        session_manager = get_session_manager()
        
        # Create a test session
        test_session = session_manager.create_session()
        if test_session:
            print(f"✅ Created test session: {test_session.session_id}")
            
            # Add a test interaction
            test_response = {
                "explanation": "Test interaction for database verification",
                "commands": [{"type": "test_command", "params": {"test": True}}],
                "executionResults": [{"command": "test_command", "success": True, "result": {"status": "test"}}]
            }
            
            success = session_manager.add_interaction(
                test_session.session_id, 
                "This is a test message to verify database storage", 
                test_response
            )
            
            if success:
                print("✅ Added test interaction to session")
                print(f"   You should now see this session in your database!")
                print(f"   Session ID: {test_session.session_id}")
            else:
                print("❌ Failed to add test interaction")
        else:
            print("❌ Failed to create test session")
            
    except Exception as e:
        print(f"❌ Error creating test session: {e}")

def main():
    """Run all database checks."""
    print("🚀 Chat Database Checker")
    print("=" * 80)
    
    check_session_manager_status()
    check_database_sessions()
    check_file_sessions()
    
    print("\n" + "=" * 80)
    user_input = input("Would you like to create a test session? (y/N): ")
    if user_input.lower() in ['y', 'yes']:
        simulate_test_session()
        print("\n" + "=" * 80)
        print("🔄 Checking database again after test session:")
        check_database_sessions()

if __name__ == "__main__":
    main()