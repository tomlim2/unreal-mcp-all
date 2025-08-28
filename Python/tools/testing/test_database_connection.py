#!/usr/bin/env python3
"""
Test database connection for session management.
Run this to verify Supabase connection and table setup.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_supabase_connection():
    """Test Supabase connection and basic operations."""
    print("🔍 Testing Supabase Connection...")
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        print("   Required: SUPABASE_URL and SUPABASE_ANON_KEY")
        return False
    
    print(f"✅ Found Supabase URL: {supabase_url}")
    print(f"✅ Found Supabase Key: {supabase_key[:20]}...")
    
    # Test Supabase import
    try:
        from supabase import create_client
        print("✅ Supabase library imported successfully")
    except ImportError:
        print("❌ Supabase library not installed")
        print("   Run: uv add supabase")
        return False
    
    # Test connection
    try:
        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return False
    
    # Test table existence and access
    try:
        result = client.table('user_sessions').select('*').limit(1).execute()
        print("✅ user_sessions table accessible")
        print(f"   Table query successful, returned {len(result.data)} rows")
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if "relation" in error_msg and "does not exist" in error_msg:
            print("⚠️  user_sessions table doesn't exist yet")
            print("\n📋 To create the table, run this SQL in your Supabase dashboard:")
            print("""
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    context JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_user_sessions_last_accessed ON user_sessions(last_accessed);
            """)
            return False
        else:
            print(f"❌ Cannot access user_sessions table: {e}")
            return False

def test_session_manager():
    """Test session manager functionality."""
    print("\n🔍 Testing Session Manager...")
    
    try:
        from tools.ai.session_management import get_session_manager, SessionContext
        print("✅ Session management imports successful")
    except ImportError as e:
        print(f"❌ Failed to import session management: {e}")
        return False
    
    try:
        # Test session manager initialization
        session_manager = get_session_manager(primary_storage='supabase', fallback_storage='file')
        print("✅ Session manager initialized")
        
        # Test health status
        health_status = session_manager.get_health_status()
        print(f"📊 Health Status:")
        print(f"   Primary Storage (Supabase): {'✅ Healthy' if health_status['primary_storage']['healthy'] else '❌ Unhealthy'}")
        print(f"   Fallback Storage (File): {'✅ Healthy' if health_status['fallback_storage']['healthy'] else '❌ Unhealthy'}")
        print(f"   Active Storage: {health_status['active_storage']}")
        print(f"   Session Count: {health_status['session_count']}")
        
        return health_status['primary_storage']['healthy']
        
    except Exception as e:
        print(f"❌ Session manager test failed: {e}")
        return False

def test_file_storage():
    """Test file storage fallback."""
    print("\n🔍 Testing File Storage Fallback...")
    
    try:
        from tools.ai.session_management.storage.file_storage import FileStorage
        
        file_storage = FileStorage()
        health_check = file_storage.health_check()
        
        if health_check:
            print("✅ File storage is healthy")
            stats = file_storage.get_storage_stats()
            print(f"📊 File Storage Stats:")
            print(f"   Active Sessions: {stats.get('active_sessions', 0)}")
            print(f"   Archived Sessions: {stats.get('archived_sessions', 0)}")
            print(f"   Total Size: {stats.get('total_size_mb', 0)} MB")
        else:
            print("❌ File storage health check failed")
        
        return health_check
        
    except Exception as e:
        print(f"❌ File storage test failed: {e}")
        return False

def main():
    """Run all connection tests."""
    print("🚀 Database Connection Test Suite")
    print("=" * 50)
    
    supabase_ok = test_supabase_connection()
    session_manager_ok = test_session_manager() 
    file_storage_ok = test_file_storage()
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"   Supabase Connection: {'✅ PASS' if supabase_ok else '❌ FAIL'}")
    print(f"   Session Manager: {'✅ PASS' if session_manager_ok else '❌ FAIL'}")
    print(f"   File Storage Fallback: {'✅ PASS' if file_storage_ok else '❌ FAIL'}")
    
    if supabase_ok and session_manager_ok:
        print("\n🎉 All tests passed! Your session management is ready to use with Supabase!")
    elif file_storage_ok:
        print("\n⚠️  Supabase issues detected, but file storage fallback is working.")
        print("    The system will work offline using local file storage.")
    else:
        print("\n❌ Multiple issues detected. Please fix the errors above.")
    
    return supabase_ok and session_manager_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)