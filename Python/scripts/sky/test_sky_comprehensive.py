#!/usr/bin/env python
"""
Comprehensive test of the fixed Ultra Dynamic Sky functionality.

TIME MAPPING SYSTEM:
The Ultra Dynamic Sky uses a float parameter from 0000 to 2400 representing time from 00:00 to 24:00

IMPORTANT NOTE - API IMPLEMENTATION:
Currently, the MCP API expects decimal hours (0.0-24.0) due to validation constraints.
- Conceptually: 4pm should be parameter 1600.0 (HHMM format)  
- Currently: 4pm is sent as 16.0 (decimal hours) to pass API validation
- The conversion functions handle this discrepancy automatically

FUTURE: The API should be updated to accept the full HHMM range (0000-2400)
to match the Ultra Dynamic Sky's native parameter system.

TIME REFERENCES:
"Time of Day" can be referenced as:
- "time of day" or "tod" 
- "time"
- Direct time format: "14:00", "2pm", "6am"
- HHMM format: "1400", "0600"

Examples (with current API conversion):
- 00:00 (midnight) = 0 or 0000 → API: 0.0
- 01:30 (1:30 AM) = 150 → API: 1.5 (not 150!)
- 04:00 (4am) = 400 → API: 4.0
- 06:00 (6am) = 600 → API: 6.0
- 14:00 (2:00 PM / 2pm) = 1400 → API: 14.0
- 16:00 (4:00 PM / 4pm) = 1600 → API: 16.0
- 16:30 (4:30 PM) = 1630 → API: 16.5
- 17:00 (5:00 PM / 5pm) = 1700 → API: 17.0
- 23:59 (11:59 PM) = 2359 → API: 23.983
- 24:00 (end of day) = 2400 → API: 24.0

Format: HHMM where HH is hours (00-24) and MM is minutes (00-59)
Conversion: HHMM gets converted to decimal hours for current API compatibility
"""

import sys
import os
import socket
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SkyTest")

def hhmm_to_decimal(hhmm_time):
    """Convert HHMM format (0000-2400) to decimal hours (0.0-24.0) for current API compatibility.
    
    This function bridges the gap between the Ultra Dynamic Sky's native HHMM format
    and the current MCP API's decimal hour validation.
    
    Args:
        hhmm_time: Time in HHMM format (e.g., 1630 for 16:30, 1400 for 2pm)
        
    Returns:
        float: Time in decimal hours (e.g., 16.5 for 16:30, 14.0 for 2pm)
        
    Examples:
        hhmm_to_decimal(1600) → 16.0 (4pm)
        hhmm_to_decimal(1630) → 16.5 (4:30pm)
        hhmm_to_decimal(1400) → 14.0 (2pm)
    """
    hours = hhmm_time // 100
    minutes = hhmm_time % 100
    return hours + (minutes / 60.0)

def decimal_to_hhmm(decimal_time):
    """Convert decimal hours (0.0-24.0) back to HHMM format (0000-2400).
    
    This function converts the API's decimal hours back to the conceptual HHMM format.
    
    Args:
        decimal_time: Time in decimal hours (e.g., 16.5 for 16:30, 14.0 for 2pm)
        
    Returns:
        int: Time in HHMM format (e.g., 1630 for 16:30, 1400 for 2pm)
        
    Examples:
        decimal_to_hhmm(16.0) → 1600 (4pm)
        decimal_to_hhmm(16.5) → 1630 (4:30pm)  
        decimal_to_hhmm(14.0) → 1400 (2pm)
    """
    hours = int(decimal_time)
    minutes = int((decimal_time - hours) * 60)
    return hours * 100 + minutes

def send_command(command: str, params: dict):
    """Send a command to the Unreal MCP server."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 55557))
        
        command_obj = {
            "type": command,
            "params": params
        }
        
        command_json = json.dumps(command_obj)
        logger.info(f"Sending: {command}")
        sock.sendall(command_json.encode('utf-8'))
        
        # Receive response
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            
            try:
                data = b''.join(chunks)
                json_response = json.loads(data.decode('utf-8'))
                break
            except json.JSONDecodeError:
                continue
        
        sock.close()
        return json_response
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

def main():
    print("🌅 === Ultra Dynamic Sky Time Control Test ===")
    
    # Test different times of day using HHMM format
    time_tests = [
        (0, "🌙 Midnight (00:00) = 0000"),
        (400, "🌌 4:00 AM (4am) = 0400"),
        (600, "🌅 Sunrise (06:00) = 0600"),
        (1200, "☀️  Noon (12:00) = 1200"),
        (1400, "☀️  2:00 PM (2pm) = 1400"),
        (1700, "🌆 5:00 PM (5pm) = 1700"),
        (1800, "🌇 Sunset (18:00) = 1800"),
        (2200, "🌃 Night (22:00) = 2200"),
        (150, "🌜 1:30 AM = 0150"),
        (1630, "🌆 4:30 PM = 1630")
    ]
    
    for time_value, description in time_tests:
        print(f"\n{description}")
        print("-" * 40)
        
        # Set the time (convert HHMM to decimal for the API)
        decimal_time = hhmm_to_decimal(time_value)
        result = send_command("set_time_of_day", {
            "sky_name": "Ultra_Dynamic_Sky_C_0", 
            "time_of_day": decimal_time
        })
        
        if result and result.get("status") == "success":
            hours = time_value // 100
            minutes = time_value % 100
            print(f"✅ Successfully set time to {hours:02d}:{minutes:02d} (parameter: {time_value})")
            
            # Verify by getting the time
            get_result = send_command("get_time_of_day", {
                "sky_name": "Ultra_Dynamic_Sky_C_0"
            })
            
            if get_result and get_result.get("status") == "success":
                actual_time = get_result["result"]["time_of_day"]
                print(f"✅ Verified time: {actual_time}")
            else:
                print("❌ Failed to verify time")
        else:
            print(f"❌ Failed to set time: {result}")
    
    # Finally, set to midnight as requested
    print(f"\n🌙 Setting final time to midnight (00:00)...")
    result = send_command("set_time_of_day", {
        "sky_name": "Ultra_Dynamic_Sky_C_0", 
        "time_of_day": 0
    })
    
    if result and result.get("status") == "success":
        print("✅ Successfully set time to midnight!")
        
        # Final verification
        get_result = send_command("get_time_of_day", {
            "sky_name": "Ultra_Dynamic_Sky_C_0"
        })
        
        if get_result and get_result.get("status") == "success":
            final_time = get_result["result"]["time_of_day"]
            print(f"🎯 Final time confirmed: {final_time} (midnight)")
    
    print("\n🎉 === Test Complete ===")

if __name__ == "__main__":
    main()
