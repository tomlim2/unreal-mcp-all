#!/usr/bin/env python3
"""
Create and move cube2 actor 100 units up in Z direction
"""

import sys
import os
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CreateAndMoveCube2")

def check_connection():
    """Check connection to Unreal Engine."""
    try:
        from unreal_mcp_server import get_unreal_connection
        
        print("🔌 Connecting to Unreal Engine...")
        unreal = get_unreal_connection()
        
        if unreal:
            print("✅ Connected successfully!")
            return unreal
        else:
            print("❌ Failed to connect to Unreal Engine")
            return None
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def send_command(unreal_connection, command: str, params: dict):
    """Send a command to Unreal Engine via the MCP connection."""
    try:
        if not unreal_connection:
            return None
            
        response = unreal_connection.send_command(command, params)
        return response
        
    except Exception as e:
        logger.error(f"Failed to send command: {e}")
        return None

def main():
    print("📦 Creating and moving cube2 actor 100 units up in Z")
    print("=" * 50)
    
    # Connect to Unreal Engine
    unreal = check_connection()
    if not unreal:
        return
    
    # First, check if cube2 already exists
    print("\n🔍 Checking if 'cube2' already exists...")
    get_result = send_command(unreal, "get_actor_properties", {"name": "cube2"})
    
    if not get_result or get_result.get("status") != "success":
        print("📦 cube2 not found, creating it...")
        
        # Create cube2 as a StaticMeshActor
        create_result = send_command(unreal, "create_actor", {
            "name": "cube2",
            "type": "CUBE",
            "location": [0.0, 0.0, 0.0],
            "rotation": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0]
        })
        
        if create_result and create_result.get("status") == "success":
            print("✅ Created cube2 successfully!")
        else:
            error_msg = create_result.get("error", "Unknown error") if create_result else "No response"
            print(f"❌ Failed to create cube2: {error_msg}")
            return
    else:
        print("✅ cube2 already exists")
    
    # Get current position of cube2
    print(f"\n📍 Getting current position of 'cube2'...")
    get_result = send_command(unreal, "get_actor_properties", {"name": "cube2"})
    
    if not get_result or get_result.get("status") != "success":
        print(f"❌ Failed to get properties of 'cube2'")
        return
    
    current_location = get_result["result"]["location"]
    current_x, current_y, current_z = current_location
    
    print(f"📍 Current cube2 position: ({current_x}, {current_y}, {current_z})")
    
    # Calculate new position (move 100 units up in Z)
    new_z = current_z + 100
    new_location = [current_x, current_y, new_z]
    
    print(f"🎯 Moving to new position: ({current_x}, {current_y}, {new_z})")
    
    # Move the actor
    move_result = send_command(unreal, "set_actor_transform", {
        "name": "cube2",
        "location": new_location,
        "rotation": [0.0, 0.0, 0.0],
        "scale": [1.0, 1.0, 1.0]
    })
    
    if move_result and move_result.get("status") == "success":
        print(f"✅ Successfully moved cube2!")
        
        # Verify the move
        verify_result = send_command(unreal, "get_actor_properties", {"name": "cube2"})
        if verify_result and verify_result.get("status") == "success":
            final_location = verify_result["result"]["location"]
            print(f"🔍 Verified position: ({final_location[0]}, {final_location[1]}, {final_location[2]})")
            
            # Check if the position actually changed
            if abs(final_location[2] - new_z) < 1.0:  # Allow for small floating point differences
                print("🎯 CONFIRMED: cube2 has been moved 100 units up in Z!")
            else:
                print(f"⚠️  Position may not have updated as expected")
        else:
            print("⚠️  Could not verify final position")
    else:
        error_msg = move_result.get("error", "Unknown error") if move_result else "No response"
        print(f"❌ Failed to move cube2: {error_msg}")

if __name__ == "__main__":
    main()
