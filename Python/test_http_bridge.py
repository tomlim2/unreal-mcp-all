#!/usr/bin/env python3
"""
Test script to debug the HTTP bridge Anthropic import issue.
"""

import sys
import os

def test_http_bridge_simulation():
    """Simulate what the HTTP bridge does when handling a request."""
    print("=== HTTP Bridge Simulation Test ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:5]}")
    
    print("\n--- Testing imports ---")
    
    # Test importing nlp_tools (this is what HTTP bridge does)
    try:
        print("Importing tools.nlp_tools...")
        from tools.nlp_tools import _process_natural_language_impl, ANTHROPIC_AVAILABLE
        print(f"✅ Import successful. ANTHROPIC_AVAILABLE = {ANTHROPIC_AVAILABLE}")
        
        # Test calling the function (this is what HTTP bridge does)
        print("\nTesting _process_natural_language_impl...")
        result = _process_natural_language_impl("test command")
        
        if "error" in result and "not installed" in result["error"]:
            print("❌ Function returned SDK not installed error")
            print(f"Error: {result['error']}")
        elif "error" in result and "not set" in result["error"]:
            print("✅ Function returned API key not set error (expected)")
        else:
            print("✅ Function executed successfully")
            
    except Exception as e:
        print(f"❌ Import or execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_http_bridge_simulation()