#!/usr/bin/env python3
"""
Set time to 11pm in Unreal Engine level.

This script sets the time of day to 11pm (23:00) using the Ultra Dynamic Sky system.
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

def find_sky_actor():
    """Find Ultra Dynamic Sky actor in the level."""
    logger.info("🔍 Searching for Ultra Dynamic Sky actor...")
    
    # Get all actors in level
    response = send_command("get_actors_in_level")
    if not response or "actors" not in response.get("result", {}):
        logger.error("Could not get actors from level")
        return None
    
    actors = response["result"]["actors"]
    
    # Look for Ultra Dynamic Sky actors
    sky_actors = []
    for actor in actors:
        actor_name = actor.get("name", "")
        actor_class = actor.get("class", "")
        if "Ultra_Dynamic_Sky" in actor_name or "Ultra_Dynamic_Sky" in actor_class:
            sky_actors.append(actor_name)
    
    if sky_actors:
        logger.info(f"✅ Found sky actor(s): {sky_actors}")
        return sky_actors[0]  # Return the first one
    else:
        logger.warning("❌ No Ultra Dynamic Sky actor found in level")
        return None

def create_sky_actor():
    """Create an Ultra Dynamic Sky actor."""
    logger.info("🌌 Creating Ultra Dynamic Sky actor...")
    
    # Try to create a sky actor with proper parameters
    response = send_command("create_actor", {
        "name": "Ultra_Dynamic_Sky_C_0",
        "type": "ULTRA_DYNAMIC_SKY",
        "location": [0, 0, 0],
        "rotation": [0, 0, 0],
        "scale": [1, 1, 1]
    })
    
    if response and response.get("status") == "success":
        actor_name = response.get("result", {}).get("name", "Ultra_Dynamic_Sky_C_0")
        logger.info(f"✅ Created sky actor: {actor_name}")
        return actor_name
    else:
        logger.error(f"❌ Failed to create sky actor: {response}")
        
        # Try alternative type names
        alternative_types = ["BP_Ultra_Dynamic_Sky", "UltraDynamicSky", "SKY"]
        for alt_type in alternative_types:
            logger.info(f"🔄 Trying alternative type: {alt_type}")
            response = send_command("create_actor", {
                "name": f"Ultra_Dynamic_Sky_{alt_type}",
                "type": alt_type,
                "location": [0, 0, 0],
                "rotation": [0, 0, 0],
                "scale": [1, 1, 1]
            })
            
            if response and response.get("status") == "success":
                actor_name = response.get("result", {}).get("name", f"Ultra_Dynamic_Sky_{alt_type}")
                logger.info(f"✅ Created sky actor with type {alt_type}: {actor_name}")
                return actor_name
        
        logger.error("❌ Could not create sky actor with any type")
        return None

def set_time_to_11pm(sky_name):
    """Set the time to 11pm (23:00) using the sky actor."""
    logger.info(f"🕚 Setting time to 11pm for sky actor: {sky_name}")
    
    # Set time to 11pm (2300 in HHMM format, or 23.0 in decimal hours)
    response = send_command("set_time_of_day", {
        "sky_name": sky_name,
        "time_of_day": 23.0  # 11pm in decimal hours
    })
    
    if response and response.get("status") == "success":
        logger.info("✅ Successfully set time to 11pm!")
        return True
    else:
        logger.error(f"❌ Failed to set time: {response}")
        
        # Try alternative format (HHMM)
        logger.info("🔄 Trying alternative time format (2300)...")
        response = send_command("set_time_of_day", {
            "sky_name": sky_name,
            "time_of_day": 2300  # 11pm in HHMM format
        })
        
        if response and response.get("status") == "success":
            logger.info("✅ Successfully set time to 11pm using HHMM format!")
            return True
        else:
            logger.error(f"❌ Failed to set time with both formats: {response}")
            return False

def main():
    """Main function to set time to 11pm."""
    print("🌙 Setting time to 11pm in Unreal Engine level")
    print("=" * 50)
    
    # Check connection
    if not check_connection():
        print("❌ Cannot connect to Unreal Engine. Make sure it's running and MCP bridge is active.")
        return False
    
    print("🔌 Connected to Unreal Engine")
    
    # Find or create sky actor
    sky_name = find_sky_actor()
    
    if not sky_name:
        sky_name = create_sky_actor()
        
    if not sky_name:
        print("❌ Could not find or create sky actor")
        return False
    
    # Set time to 11pm
    success = set_time_to_11pm(sky_name)
    
    if success:
        print("🌙 Time successfully set to 11pm!")
        return True
    else:
        print("❌ Failed to set time to 11pm")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
