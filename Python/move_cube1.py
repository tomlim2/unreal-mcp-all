#!/usr/bin/env python3
"""
Move cube1 actor 200 units up in Z direction
"""

import sys
import os
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MoveCube1")

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
    print("📦 Moving cube2 actor 100 units up in Z")
    print("=" * 40)
    
    # Connect to Unreal Engine
    unreal = check_connection()
    if not unreal:
        return
    
    # First, look for cube actors in the level
    print("\n🔍 Looking for cube actors...")
    actors_result = send_command(unreal, "get_actors_in_level", {})
    
    if not actors_result or actors_result.get("status") != "success":
        print("❌ Failed to get actors from level")
        return
    
    actors = actors_result.get("result", {}).get("actors", [])
    cube_actors = []
    
    for actor in actors:
        if isinstance(actor, dict):
            name = actor.get("name", "")
            if "cube" in name.lower():
                cube_actors.append(name)
    
    if not cube_actors:
        print("❌ No cube actors found in the level")
        return
    
    print(f"🧊 Found cube actors: {', '.join(cube_actors)}")
    
    # Try to find cube2 first, then TestCube_002, otherwise use available cubes
    target_actor = None
    if "cube2" in cube_actors:
        target_actor = "cube2"
    elif "TestCube_002" in cube_actors:
        target_actor = "TestCube_002"
        print(f"💡 'cube2' not found, using '{target_actor}' instead")
    elif cube_actors:
        target_actor = cube_actors[1] if len(cube_actors) > 1 else cube_actors[0]
        print(f"💡 'cube2' not found, using '{target_actor}' instead")
    
    if not target_actor:
        print("❌ No suitable cube actor found")
        return
    
    # Get current position of the target actor
    print(f"\n📍 Getting current position of '{target_actor}'...")
    get_result = send_command(unreal, "get_actor_properties", {"name": target_actor})
    
    if not get_result or get_result.get("status") != "success":
        print(f"❌ Failed to get properties of '{target_actor}'")
        return
    
    current_location = get_result["result"]["location"]
    current_x, current_y, current_z = current_location
    
    print(f"📍 Current {target_actor} position: ({current_x}, {current_y}, {current_z})")
    
    # Calculate new position (move 100 units up in Z)
    new_z = current_z + 100
    new_location = [current_x, current_y, new_z]
    
    print(f"🎯 Moving to new position: ({current_x}, {current_y}, {new_z})")
    
    # Move the actor
    move_result = send_command(unreal, "set_actor_transform", {
        "name": target_actor,
        "location": new_location
    })
    
    if move_result and move_result.get("status") == "success":
        print(f"✅ Successfully moved {target_actor}!")
        
        # Verify the move
        verify_result = send_command(unreal, "get_actor_properties", {"name": target_actor})
        if verify_result and verify_result.get("status") == "success":
            final_location = verify_result["result"]["location"]
            print(f"🔍 Verified position: ({final_location[0]}, {final_location[1]}, {final_location[2]})")
        else:
            print("⚠️  Could not verify final position")
    else:
        error_msg = move_result.get("error", "Unknown error") if move_result else "No response"
        print(f"❌ Failed to move {target_actor}: {error_msg}")

if __name__ == "__main__":
    main()
