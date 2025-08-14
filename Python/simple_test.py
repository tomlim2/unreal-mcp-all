#!/usr/bin/env python3
"""
Simple test to verify the refactored architecture works.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import anthropic
        print("✅ Anthropic SDK imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Anthropic SDK: {e}")
        return False
    
    try:
        import tools.nlp_tools
        print("✅ NLP tools module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import NLP tools: {e}")
        return False
    
    try:
        import http_bridge
        print("✅ HTTP bridge module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import HTTP bridge: {e}")
        return False
    
    return True

def test_environment():
    """Test environment configuration."""
    print("\nTesting environment...")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print("✅ ANTHROPIC_API_KEY is set")
        return True
    else:
        print("⚠️ ANTHROPIC_API_KEY not set (required for production)")
        return None  # Not a failure, just a warning

def main():
    """Run tests."""
    print("=== Simple Refactoring Test ===\n")
    
    results = []
    
    # Test imports
    results.append(test_imports())
    
    # Test environment (optional)
    env_result = test_environment()
    if env_result is not None:
        results.append(env_result)
    
    # Summary
    print("\n=== Summary ===")
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ Basic setup is working!")
        print("\nNext steps:")
        print("1. Set ANTHROPIC_API_KEY environment variable")
        print("2. Start HTTP bridge: python http_bridge.py")
        print("3. Start frontend: cd ../Frontend && npm run dev")
        return 0
    else:
        print("❌ Some issues detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())