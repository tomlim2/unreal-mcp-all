#!/usr/bin/env python3
"""
Test the fixed architecture without requiring actual API keys.
"""

import json
import os

def test_nlp_implementation():
    """Test the NLP implementation function directly."""
    print("Testing NLP implementation...")
    
    try:
        from tools.nlp_tools import _process_natural_language_impl
        
        # Test without API key (should handle gracefully)
        result = _process_natural_language_impl("Get all actors in level")
        
        print("Result:", json.dumps(result, indent=2))
        
        if result.get("error") == "ANTHROPIC_API_KEY environment variable not set":
            print("✅ NLP implementation correctly handles missing API key")
            return True
        else:
            print("❌ Expected API key error")
            return False
            
    except Exception as e:
        print(f"❌ Error testing NLP implementation: {e}")
        return False

def test_http_bridge_import():
    """Test that HTTP bridge can import the fixed function."""
    print("\nTesting HTTP bridge imports...")
    
    try:
        from tools.nlp_tools import _process_natural_language_impl
        print("✅ HTTP bridge can import NLP implementation")
        return True
    except ImportError as e:
        print(f"❌ HTTP bridge import failed: {e}")
        return False

def test_architecture_flow():
    """Test the complete architecture flow simulation."""
    print("\nTesting architecture flow...")
    
    try:
        # Simulate the flow: Frontend -> HTTP Bridge -> NLP Implementation -> Unreal
        from tools.nlp_tools import _process_natural_language_impl
        
        # Simulate user input from frontend
        user_input = "Show me all actors in the level"
        context = "Testing environment"
        
        # Process through NLP (this is what HTTP bridge does)
        result = _process_natural_language_impl(user_input, context)
        
        # Check result structure matches what frontend expects
        expected_keys = ["explanation", "commands", "executionResults"]
        has_all_keys = all(key in result for key in expected_keys)
        
        if has_all_keys:
            print("✅ Architecture flow produces correct response structure")
            return True
        else:
            print(f"❌ Missing expected keys. Got: {list(result.keys())}")
            return False
            
    except Exception as e:
        print(f"❌ Architecture flow test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Testing Fixed Architecture ===\n")
    
    results = []
    
    # Test NLP implementation
    results.append(test_nlp_implementation())
    
    # Test HTTP bridge imports
    results.append(test_http_bridge_import())
    
    # Test architecture flow
    results.append(test_architecture_flow())
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ Fixed architecture is working!")
        print("\nTo use with real API:")
        print("1. Set ANTHROPIC_API_KEY environment variable")
        print("2. Restart HTTP bridge: python http_bridge.py")
        print("3. Frontend will work: http://localhost:3000")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())