#!/usr/bin/env python3
"""
Test script to verify the complete screenshot job system is working.
"""

import time
import json
from tools.ai.nlp import process_natural_language

def test_screenshot_job():
    """Test the complete screenshot job workflow."""
    print("🧪 Testing Screenshot Job System")
    print("=" * 50)
    
    # Test session ID
    test_session_id = "test_session_screenshot_" + str(int(time.time()))
    print(f"📋 Using test session ID: {test_session_id}")
    
    # Test natural language input
    user_input = "Take a high resolution screenshot"
    context = "Testing screenshot job system"
    
    print(f"🗣️  User input: {user_input}")
    print(f"📝 Context: {context}")
    print()
    
    try:
        # Process the natural language request
        print("🔄 Processing natural language request...")
        result = process_natural_language(
            user_input=user_input,
            context=context,
            session_id=test_session_id
        )
        
        print("✅ NLP Processing completed!")
        print(f"📊 Result keys: {list(result.keys())}")
        print()
        
        # Check if we got commands
        if 'commands' in result and result['commands']:
            print(f"🎯 Generated {len(result['commands'])} commands:")
            for i, cmd in enumerate(result['commands'], 1):
                print(f"   {i}. {cmd.get('type', 'unknown')} - {cmd.get('params', {})}")
        
        # Check execution results
        if 'executionResults' in result and result['executionResults']:
            print(f"⚡ Execution results:")
            for i, exec_result in enumerate(result['executionResults'], 1):
                success = exec_result.get('success', False)
                status = "✅ SUCCESS" if success else "❌ FAILED"
                command = exec_result.get('command', 'unknown')
                print(f"   {i}. {command}: {status}")
                
                if success and 'result' in exec_result:
                    job_result = exec_result['result']
                    if isinstance(job_result, dict) and 'result' in job_result:
                        inner_result = job_result['result']
                        if isinstance(inner_result, dict) and 'job_id' in inner_result:
                            job_id = inner_result['job_id']
                            print(f"      🆔 Job ID: {job_id}")
                            print(f"      📁 Download URL would be: /api/screenshot/download/{job_id}")
        
        print()
        print("📋 Full Result:")
        print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_job_system_availability():
    """Test if the job system components are available."""
    print("\n🔧 Testing Job System Components")
    print("=" * 50)
    
    try:
        # Test local job system initialization
        from tools.ai.nlp import _get_or_create_job_system
        job_manager, screenshot_worker = _get_or_create_job_system()
        
        print(f"📊 Job Manager: {'✅ Available' if job_manager else '❌ Not Available'}")
        print(f"📸 Screenshot Worker: {'✅ Available' if screenshot_worker else '❌ Not Available'}")
        
        if job_manager and screenshot_worker:
            print("🎉 Local job system successfully initialized!")
        else:
            print("⚠️  Job system initialization failed")
            
    except Exception as e:
        print(f"❌ Job system test failed: {e}")
        import traceback
        traceback.print_exc()

def test_http_bridge_job_system():
    """Test if HTTP bridge job system is available."""
    print("\n🌐 Testing HTTP Bridge Job System")
    print("=" * 50)
    
    try:
        import http_bridge
        job_manager, screenshot_worker = http_bridge.get_job_system()
        
        print(f"📊 HTTP Bridge Job Manager: {'✅ Available' if job_manager else '❌ Not Available'}")
        print(f"📸 HTTP Bridge Screenshot Worker: {'✅ Available' if screenshot_worker else '❌ Not Available'}")
        
        if job_manager and screenshot_worker:
            print("🎉 HTTP bridge job system is running!")
        else:
            print("ℹ️  HTTP bridge job system not running (expected if bridge not started)")
            
    except Exception as e:
        print(f"ℹ️  HTTP bridge not available: {e}")

if __name__ == "__main__":
    print("🚀 Starting Screenshot Job System Tests")
    print("=" * 60)
    
    # Test 1: Job system components
    test_job_system_availability()
    
    # Test 2: HTTP bridge availability  
    test_http_bridge_job_system()
    
    # Test 3: End-to-end screenshot workflow
    result = test_screenshot_job()
    
    if result:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")
    
    print("=" * 60)