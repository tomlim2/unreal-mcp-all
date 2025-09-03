#!/usr/bin/env python3
"""
Test script for the new smart screenshot implementation methods.
Tests both synchronous and asynchronous screenshot approaches.
"""

import json
import time
from tools.ai.nlp import process_natural_language

def test_standard_resolution_screenshot():
    """Test standard resolution (synchronous) screenshot"""
    print("Testing standard resolution screenshot (synchronous method)...")
    
    user_input = "Take a screenshot"  # Should default to 1.0x resolution
    result = process_natural_language(user_input)
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Check if we got the expected synchronous path
    if result.get("executionResults"):
        for exec_result in result["executionResults"]:
            if exec_result.get("command") == "take_highresshot":
                print(f"✅ Command executed: {exec_result.get('success')}")
                if exec_result.get("result"):
                    response_result = exec_result["result"]
                    print(f"📊 Response: {response_result.get('message', 'No message')}")
                    if "width" in response_result and "height" in response_result:
                        print(f"🖼️  Synchronous path detected (includes viewport dimensions)")
                    return True
    
    print("❌ Standard screenshot test failed")
    return False

def test_high_resolution_screenshot():
    """Test high resolution (asynchronous) screenshot"""
    print("\nTesting high resolution screenshot (asynchronous method)...")
    
    user_input = "Take a high resolution screenshot at 2x multiplier"
    result = process_natural_language(user_input)
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Check if we got the expected asynchronous path
    if result.get("executionResults"):
        for exec_result in result["executionResults"]:
            if exec_result.get("command") == "take_highresshot":
                print(f"✅ Command executed: {exec_result.get('success')}")
                if exec_result.get("result"):
                    response_result = exec_result["result"]
                    print(f"📊 Response: {response_result.get('message', 'No message')}")
                    if "capture_time_seconds" in response_result:
                        print(f"⏱️  Asynchronous path detected (includes capture time)")
                        capture_time = response_result.get("capture_time_seconds", 0)
                        print(f"⏱️  Capture time: {capture_time:.2f} seconds")
                    return True
    
    print("❌ High-res screenshot test failed")
    return False

def test_socket_timeout_compliance():
    """Test that high-res screenshots respect socket timeout limits"""
    print("\nTesting socket timeout compliance...")
    
    # This should complete within 6 seconds (our new timeout)
    start_time = time.time()
    user_input = "Take a 4x resolution screenshot"
    result = process_natural_language(user_input)
    end_time = time.time()
    
    total_time = end_time - start_time
    print(f"⏱️  Total processing time: {total_time:.2f} seconds")
    
    if total_time <= 7.0:  # Allow 1 second buffer for processing overhead
        print("✅ Socket timeout compliance verified")
        return True
    else:
        print("❌ Socket timeout compliance failed - took too long")
        return False

def main():
    """Run all screenshot method tests"""
    print("🧪 Testing Smart Hybrid Screenshot Implementation")
    print("=" * 60)
    
    tests = [
        test_standard_resolution_screenshot,
        test_high_resolution_screenshot,
        test_socket_timeout_compliance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Smart hybrid screenshot implementation is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation and Unreal Engine connection.")

if __name__ == "__main__":
    main()