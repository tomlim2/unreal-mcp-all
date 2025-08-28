#!/usr/bin/env python3
"""
Test Supabase Python syntax and basic operations.
This will help verify the library is working correctly.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_import():
    """Test if supabase library can be imported."""
    print("🔍 Testing Supabase Import...")
    
    try:
        from supabase import create_client, Client
        print("✅ Successfully imported: create_client, Client")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_supabase_client_creation():
    """Test creating a Supabase client."""
    print("\n🔍 Testing Supabase Client Creation...")
    
    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Missing environment variables: SUPABASE_URL or SUPABASE_ANON_KEY")
        return False
    
    try:
        from supabase import create_client
        
        # Create client
        supabase = create_client(url, key)
        print(f"✅ Client created successfully")
        print(f"   URL: {url}")
        print(f"   Key: {key[:20]}...")
        print(f"   Client type: {type(supabase)}")
        return supabase
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        return None

def test_basic_operations(client):
    """Test basic Supabase operations."""
    print("\n🔍 Testing Basic Operations...")
    
    if not client:
        print("❌ No client provided")
        return False
    
    try:
        # Test 1: Simple table query (should work even if table doesn't exist)
        print("   Testing table query...")
        result = client.table('user_sessions').select('*').limit(1).execute()
        print(f"✅ Table query successful")
        print(f"   Returned {len(result.data)} rows")
        print(f"   Data type: {type(result.data)}")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if "relation" in error_msg and "does not exist" in error_msg:
            print("⚠️  Table 'user_sessions' doesn't exist yet")
            print("   This is expected if you haven't created the table")
            return True
        else:
            print(f"❌ Query failed: {e}")
            return False

def show_table_creation_sql():
    """Show SQL to create the user_sessions table."""
    print("\n📋 SQL to create user_sessions table:")
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

def show_correct_syntax():
    """Show the correct Supabase Python syntax."""
    print("\n📚 Correct Supabase Python Syntax:")
    print("""
# 1. Import
from supabase import create_client, Client

# 2. Create client
supabase: Client = create_client(url, key)

# 3. Insert data
result = supabase.table('user_sessions').insert({
    'session_id': 'abc123',
    'context': {'key': 'value'},
    'created_at': '2025-01-01T00:00:00Z',
    'last_accessed': '2025-01-01T00:00:00Z'
}).execute()

# 4. Select data
result = supabase.table('user_sessions').select('*').eq('session_id', 'abc123').execute()

# 5. Update data
result = supabase.table('user_sessions').update({
    'last_accessed': '2025-01-01T01:00:00Z'
}).eq('session_id', 'abc123').execute()

# 6. Delete data
result = supabase.table('user_sessions').delete().eq('session_id', 'abc123').execute()

# 7. Check result
if result.data:
    print("Success:", result.data)
else:
    print("No data returned")
""")

def main():
    """Run all Supabase syntax tests."""
    print("🧪 Supabase Python Syntax Test")
    print("=" * 40)
    
    # Test 1: Import
    import_ok = test_supabase_import()
    if not import_ok:
        print("\n❌ Cannot proceed without Supabase library")
        show_correct_syntax()
        return False
    
    # Test 2: Client creation
    client = test_supabase_client_creation()
    
    # Test 3: Basic operations
    operations_ok = test_basic_operations(client)
    
    # Show helpful information
    show_table_creation_sql()
    show_correct_syntax()
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 Test Results:")
    print(f"   Import: {'✅ PASS' if import_ok else '❌ FAIL'}")
    print(f"   Client: {'✅ PASS' if client else '❌ FAIL'}")
    print(f"   Operations: {'✅ PASS' if operations_ok else '❌ FAIL'}")
    
    if import_ok and client and operations_ok:
        print("\n🎉 All syntax tests passed! Supabase is ready to use.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)