#!/usr/bin/env python3
"""
Simple test script to verify Unreal TCP connection
"""
import socket
import json
import sys

def test_unreal_connection():
    """Test connection to Unreal Engine TCP server"""
    try:
        print("Testing connection to Unreal Engine...")
        
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Connect
        sock.connect(('127.0.0.1', 55557))
        print("✓ Connected successfully")
        
        # Send test command
        test_command = {"type": "get_actors_in_level", "params": {}}
        command_json = json.dumps(test_command)
        print(f"Sending: {command_json}")
        
        sock.sendall(command_json.encode('utf-8'))
        
        # Receive response
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
            try:
                # Try to parse as complete JSON
                response = json.loads(response_data.decode('utf-8'))
                print(f"✓ Received response: {response}")
                sock.close()
                return True
            except json.JSONDecodeError:
                # Not complete yet, continue reading
                continue
        
        print("✗ No valid response received")
        sock.close()
        return False
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_unreal_connection()
    sys.exit(0 if success else 1)