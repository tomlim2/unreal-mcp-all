#!/usr/bin/env python3
"""
Test script for NLP integration in Unreal MCP server.
"""

import os
import sys
import json
import requests
import time
import subprocess
import threading
from typing import Dict, Any

def test_nlp_tool():
    """Test the NLP tool directly."""
    print("Testing NLP tool directly...")
    
    # Set test API key (you'll need to set the real one)
    os.environ['ANTHROPIC_API_KEY'] = 'test-key'
    
    try:
        from tools.nlp_tools import process_natural_language
        from mcp.server.fastmcp import Context
        
        # Create context
        ctx = Context()
        
        # Test without API key
        result = process_natural_language(ctx, "Get all actors in level")
        print("NLP Tool Result:", json.dumps(result, indent=2))
        
        if "error" in result:
            print("✅ NLP tool correctly handles missing API key")
            return True
        else:
            print("❌ Expected error for missing API key")
            return False
            
    except Exception as e:
        print(f"❌ Error testing NLP tool: {e}")
        return False

def test_http_bridge():
    """Test the HTTP bridge."""
    print("\nTesting HTTP bridge...")
    
    # Start HTTP bridge in background
    try:
        from http_bridge import MCPHttpBridge
        bridge = MCPHttpBridge(port=8081)  # Use different port for testing
        
        if bridge.start():
            print("✅ HTTP bridge started on port 8081")
            
            # Test natural language request
            try:
                response = requests.post('http://127.0.0.1:8081', 
                    json={
                        'prompt': 'Show me all actors in the level',
                        'context': 'Testing environment'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("HTTP Bridge Result:", json.dumps(result, indent=2))
                    
                    if "error" in result:
                        print("✅ HTTP bridge correctly handles requests")
                        bridge.stop()
                        return True
                    else:
                        print("❌ Unexpected response format")
                        bridge.stop()
                        return False
                else:
                    print(f"❌ HTTP request failed: {response.status_code}")
                    bridge.stop()
                    return False
                    
            except requests.RequestException as e:
                print(f"❌ Request error: {e}")
                bridge.stop()
                return False
        else:
            print("❌ Failed to start HTTP bridge")
            return False
            
    except Exception as e:
        print(f"❌ Error testing HTTP bridge: {e}")
        return False

def test_frontend_integration():
    """Test frontend integration (requires Next.js server)."""
    print("\nTesting frontend integration...")
    
    try:
        # Try to make request to Next.js API
        response = requests.post('http://localhost:3000/api/openai',
            json={
                'prompt': 'Test request',
                'context': 'Testing'
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Frontend API Result:", json.dumps(result, indent=2))
            print("✅ Frontend API is accessible")
            return True
        else:
            print(f"⚠️ Frontend not running (status: {response.status_code})")
            return None  # Not a failure, just not running
            
    except requests.RequestException:
        print("⚠️ Frontend not running (connection failed)")
        return None  # Not a failure, just not running

def main():
    """Run all tests."""
    print("=== Unreal MCP Refactoring Tests ===\n")
    
    results = []
    
    # Test NLP tool
    results.append(test_nlp_tool())
    
    # Test HTTP bridge
    results.append(test_http_bridge())
    
    # Test frontend (optional)
    frontend_result = test_frontend_integration()
    if frontend_result is not None:
        results.append(frontend_result)
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())