#!/usr/bin/env python3
"""
Quick connection test for the smart screenshot implementation.
"""

import json
import socket

def test_tcp_connection():
    """Test basic TCP connection to Unreal Engine"""
    print("Testing TCP connection to Unreal Engine...")
    
    try:
        # Try to connect to Unreal Engine
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        result = sock.connect_ex(('127.0.0.1', 55557))
        
        if result == 0:
            print("✅ TCP connection successful")
            
            # Try sending a simple ping command
            ping_command = {"type": "ping", "params": {}}
            command_json = json.dumps(ping_command)
            
            sock.sendall(command_json.encode('utf-8'))
            
            # Try to receive response
            response_data = sock.recv(4096)
            response = json.loads(response_data.decode('utf-8'))
            
            sock.close()
            
            if response.get('message') == 'pong':
                print("✅ Ping test successful")
                return True
            else:
                print(f"❌ Unexpected ping response: {response}")
                return False
                
        else:
            print("❌ TCP connection failed - Unreal Engine may not be running")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        if 'sock' in locals():
            sock.close()
        return False

def test_screenshot_command_routing():
    """Test that screenshot command gets routed correctly"""
    print("\nTesting screenshot command routing...")
    
    try:
        from unreal_mcp_server import get_unreal_connection
        
        connection = get_unreal_connection()
        if not connection:
            print("❌ Could not get Unreal connection")
            return False
            
        # Test with resolution 1.0 (should use synchronous path)
        test_command = {"type": "take_highresshot", "params": {"resolution_multiplier": 1.0}}
        
        print("🧪 Testing synchronous path (1.0x resolution)...")
        response = connection.send_command("take_highresshot", {"resolution_multiplier": 1.0})
        
        if response:
            print(f"✅ Got response: {response.get('message', 'No message')}")
            if 'width' in response and 'height' in response:
                print("✅ Synchronous path confirmed (includes viewport dimensions)")
            return True
        else:
            print("❌ No response from screenshot command")
            return False
            
    except Exception as e:
        print(f"❌ Screenshot routing test failed: {e}")
        return False

def main():
    """Run basic connectivity tests"""
    print("🧪 Quick Connection and Routing Tests")
    print("=" * 50)
    
    tests = [
        test_tcp_connection,
        test_screenshot_command_routing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All connectivity tests passed!")
        print("💡 Ready to test full screenshot implementation")
    else:
        print("⚠️  Basic connectivity issues detected")
        print("💡 Make sure Unreal Engine project is open with MCP plugin loaded")

if __name__ == "__main__":
    main()