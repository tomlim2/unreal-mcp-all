#!/usr/bin/env python3
"""
Ultra Dynamic Sky Test Script

Test script for the new Time of Day functionality in Unreal MCP.
"""

import json
import socket
import time

def send_command(command_type, params=None):
    """Send a command to Unreal Engine and return the response."""
    HOST = "127.0.0.1"
    PORT = 55558
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((HOST, PORT))
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        sock.sendall(json.dumps(command).encode('utf-8'))
        response = sock.recv(8192)  # Increased buffer size for property lists
        result = json.loads(response.decode('utf-8'))
        sock.close()
        
        return result
        
    except Exception as e:
        print(f"Command '{command_type}' failed with error: {e}")
        return None

def test_unreal_connection():
    """Test connection to Unreal Engine."""
    
    print("=== Ultra Dynamic Sky Debug Test ===\n")
    
    # First, check if Ultra Dynamic Sky actor exists
    print("1. Checking for Ultra Dynamic Sky actor...")
    actors_result = send_command("find_actors_by_name", {"pattern": "Ultra_Dynamic_Sky"})
    
    if actors_result:
        print(f"Found actors: {actors_result}")
    else:
        print("No Ultra Dynamic Sky actors found or connection failed")
        return
    
    # Debug actor properties
    print("\n2. Getting all properties of Ultra Dynamic Sky actor...")
    properties_result = send_command("get_actor_properties", {"name": "Ultra_Dynamic_Sky_C_0"})
    
    if properties_result:
        print("Actor properties response:")
        print(json.dumps(properties_result, indent=2))
    else:
        print("Failed to get actor properties")
    
    # Test get_time_of_day with improved error handling
    print("\n3. Testing get_time_of_day...")
    time_result = send_command("get_time_of_day", {})
    
    if time_result:
        print("Get time of day response:")
        print(json.dumps(time_result, indent=2))
        
        if time_result.get("status") == "success":
            current_time = time_result.get("result", {}).get("time_of_day")
            print(f"Current time of day: {current_time}")
        else:
            print(f"Error: {time_result.get('error', 'Unknown error')}")
    else:
        print("Failed to get time of day")
    
    # Test set_time_of_day
    print("\n4. Testing set_time_of_day...")
    set_result = send_command("set_time_of_day", {"time_of_day": 1230})
    
    if set_result:
        print("Set time of day response:")
        print(json.dumps(set_result, indent=2))
        
        if set_result.get("status") == "success":
            result_data = set_result.get("result", {})
            print(f"Successfully set time to 12:30")
            print(f"Update functions called: {result_data.get('update_functions_called', False)}")
            print(f"Property name used: {result_data.get('property_name', 'Unknown')}")
            print(f"Property type: {result_data.get('property_type', 'Unknown')}")
            
            # Wait a moment for the update to process
            print("Waiting 2 seconds for sky update to process...")
            time.sleep(2)
            
            # Verify the change
            print("\n5. Verifying the time change...")
            verify_result = send_command("get_time_of_day", {})
            
            if verify_result and verify_result.get("status") == "success":
                new_time = verify_result.get("result", {}).get("time_of_day")
                print(f"Verified time of day: {new_time}")
            else:
                print("Failed to verify time change")
                
            # Test force sky update
            print("\n6. Testing force sky update...")
            force_result = send_command("force_sky_update", {})
            
            if force_result:
                print("Force sky update response:")
                print(json.dumps(force_result, indent=2))
            else:
                print("Failed to force sky update")
                
        else:
            print(f"Failed to set time: {set_result.get('error', 'Unknown error')}")
    else:
        print("Failed to set time of day")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_unreal_connection()
