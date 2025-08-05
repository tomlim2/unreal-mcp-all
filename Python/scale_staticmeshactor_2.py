#!/usr/bin/env python3
"""
Scale StaticMeshActor_2 to 10.

This script changes the scale of StaticMeshActor_2 to [10, 10, 10].
"""

import json
import socket
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Unreal Engine connection settings
UNREAL_HOST = "127.0.0.1"
UNREAL_PORT = 55557

def check_connection():
    """Check if we can connect to Unreal Engine."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((UNREAL_HOST, UNREAL_PORT))
        sock.close()
        return True
    except Exception as e:
        logger.error(f"Cannot connect to Unreal Engine: {e}")
        return False

def send_command(command_type, params=None):
    """Send a command to Unreal Engine and get the response."""
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((UNREAL_HOST, UNREAL_PORT))
        
        # Prepare command
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        # Send command
        command_json = json.dumps(command)
        logger.info(f"Sending command: {command_json}")
        sock.sendall(command_json.encode('utf-8'))
        
        # Receive response
        response_data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
            
            # Try to parse JSON to see if we have complete response
            try:
                response = json.loads(response_data.decode('utf-8'))
                break
            except json.JSONDecodeError:
                continue
        
        sock.close()
        
        logger.info(f"Response: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        return None

def find_actor(actor_name):
    """Find a specific actor in the level."""
    logger.info(f"🔍 Searching for actor: {actor_name}")
    
    # Get all actors in level
    response = send_command("get_actors_in_level")
    if not response or "actors" not in response.get("result", {}):
        logger.error("Could not get actors from level")
        return None
    
    actors = response["result"]["actors"]
    
    # Look for the specific actor
    for actor in actors:
        if actor.get("name", "") == actor_name:
            logger.info(f"✅ Found actor: {actor_name}")
            logger.info(f"   Current location: {actor.get('location', [0, 0, 0])}")
            logger.info(f"   Current rotation: {actor.get('rotation', [0, 0, 0])}")
            logger.info(f"   Current scale: {actor.get('scale', [1, 1, 1])}")
            return actor
    
    logger.warning(f"❌ Actor {actor_name} not found in level")
    return None

def scale_actor(actor_name, new_scale):
    """Scale an actor to the specified scale."""
    logger.info(f"📏 Scaling actor {actor_name} to {new_scale}")
    
    # First, get the current actor properties
    actor = find_actor(actor_name)
    if not actor:
        return False
    
    current_location = actor.get("location", [0, 0, 0])
    current_rotation = actor.get("rotation", [0, 0, 0])
    
    # Set the actor transform with new scale
    response = send_command("set_actor_transform", {
        "name": actor_name,
        "location": current_location,
        "rotation": current_rotation,
        "scale": new_scale
    })
    
    if response and response.get("status") == "success":
        logger.info(f"✅ Successfully scaled {actor_name} to {new_scale}!")
        
        # Verify the change by getting the actor properties again
        updated_actor = find_actor(actor_name)
        if updated_actor:
            updated_scale = updated_actor.get("scale", [1, 1, 1])
            logger.info(f"🔍 Verified new scale: {updated_scale}")
        
        return True
    else:
        logger.error(f"❌ Failed to scale actor: {response}")
        return False

def main():
    """Main function to scale StaticMeshActor_2."""
    print("📏 Scaling StaticMeshActor_2 to scale 5")
    print("=" * 50)
    
    # Check connection
    if not check_connection():
        print("❌ Cannot connect to Unreal Engine. Make sure it's running and MCP bridge is active.")
        return False
    
    print("🔌 Connected to Unreal Engine")
    
    # Target actor and new scale
    actor_name = "StaticMeshActor_2"
    new_scale = [5.0, 5.0, 5.0]
    
    # Scale the actor
    success = scale_actor(actor_name, new_scale)
    
    if success:
        print(f"📏 Successfully scaled {actor_name} to {new_scale}!")
        return True
    else:
        print(f"❌ Failed to scale {actor_name}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
