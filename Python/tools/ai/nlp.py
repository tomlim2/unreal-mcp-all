import logging
import json
import os
import sys
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP, Context
from ..utils.temperature_utils import map_temperature_description
from .nlp_schema_validator import (
    validate_command, 
    normalize_light_parameters, 
    normalize_sky_parameters,
    ValidatedCommand,
    SKY_CONSTRAINTS,
    LIGHT_CONSTRAINTS
)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from the Python directory
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(dotenv_path)
    print(f"✅ Loaded .env file from: {dotenv_path}")
except ImportError:
    print("⚠️ python-dotenv not installed, .env file will not be loaded")
except Exception as e:
    print(f"⚠️ Failed to load .env file: {e}")

# Try to import anthropic at module level to debug the issue
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
    print(f"✅ Anthropic SDK imported successfully in {__name__}")
except ImportError as e:
    ANTHROPIC_AVAILABLE = False
    print(f"❌ Failed to import Anthropic SDK in {__name__}: {e}")
    print(f"Python path: {sys.path[:3]}")

# Get logger
logger = logging.getLogger("UnrealMCP")

def _process_natural_language_impl(user_input: str, context: str = None) -> Dict[str, Any]:
    try:
        if not ANTHROPIC_AVAILABLE:
            return {
                "error": "Anthropic SDK not installed. Run: pip install anthropic",
                "explanation": "Natural language processing unavailable", 
                "commands": [],
                "executionResults": []
            }
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key or api_key == 'your-api-key-here':
            return {
                "error": "ANTHROPIC_API_KEY environment variable not set",
                "explanation": "Please configure your Anthropic API key",
                "commands": [],
                "executionResults": []
            }
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        # Build system prompt with available tools
        system_prompt = build_system_prompt(context or "Assume as you are a creative cinematic director")
        logger.info(f"Processing natural language input: {user_input}")
        # Get AI response
        response = client.messages.create(
            model='claude-3-haiku-20240307',
            max_tokens=1024,
            temperature=0.1,
            messages=[
                {"role": "user", "content": f"{system_prompt}\n\nUser request: {user_input}"}
            ]
        )
        ai_response = response.content[0].text
        logger.info(f"AI response for '{user_input}': {ai_response}")
        print(f"DEBUG: AI response for '{user_input}': {ai_response}")
        
        # Parse AI response
        try:
            parsed_response = json.loads(ai_response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            # If AI didn't return valid JSON, create a structured response
            parsed_response = {
                "explanation": ai_response,
                "commands": [],
                "expectedResult": "Please rephrase your request more specifically."
            }
        # Execute commands using direct connection with schema validation
        execution_results = []
        if parsed_response.get("commands") and isinstance(parsed_response["commands"], list):
            for command in parsed_response["commands"]:
                try:
                    logger.info(f"Executing command from NLP: {command}")
                    print(f"DEBUG: Executing command from NLP: {command}")
                    
                    # Pre-validate command before execution
                    validated_cmd = validate_command(command)
                    if not validated_cmd.is_valid:
                        raise Exception(f"Schema validation failed: {'; '.join(validated_cmd.validation_errors)}")
                    
                    result = execute_command_direct(command)
                    execution_results.append({
                        "command": command.get("type", "unknown"),
                        "success": True,
                        "result": result,
                        "validation": "passed"
                    })
                    logger.info(f"Successfully executed validated command: {command.get('type')}")
                except Exception as e:
                    execution_results.append({
                        "command": command.get("type", "unknown"),
                        "success": False,
                        "error": str(e),
                        "validation": "failed" if "validation failed" in str(e).lower() else "passed"
                    })
                    logger.error(f"Failed to execute command {command.get('type')}: {e}")
        return {
            "explanation": parsed_response.get("explanation", "Processed your request"),
            "commands": parsed_response.get("commands", []),
            "expectedResult": parsed_response.get("expectedResult", "Commands executed"),
            "executionResults": execution_results
        }
    except Exception as e:
        logger.error(f"Error in process_natural_language: {e}")
        return {
            "error": str(e),
            "explanation": "An error occurred while processing your request",
            "commands": [],
            "executionResults": []
        }

def register_nlp_tools(mcp: FastMCP):
    @mcp.tool()
    def process_natural_language(ctx: Context, user_input: str, context: str = None) -> Dict[str, Any]:
        return _process_natural_language_impl(user_input, context)

def build_system_prompt(context: str) -> str:
    import time
    import random
    timestamp = int(time.time() * 1000)
    random_suffix = random.randint(1000, 9999)
    
    return f"""You are a creative cinematic director's AI assistant translating natural language to Unreal Engine commands.

## SCHEMA-VALIDATED COMMANDS
- Time/Sky: get_ultra_dynamic_sky, set_time_of_day, set_color_temperature
- Actors: get_actors_in_level, create_actor, delete_actor, set_actor_transform, get_actor_properties  
- Cesium: set_cesium_latitude_longitude, get_cesium_properties
- MM Lights: create_mm_control_light, get_mm_control_lights, update_mm_control_light, delete_mm_control_light

## PARAMETER VALIDATION RULES
**Sky Commands:**
- time_of_day: Range 0-{SKY_CONSTRAINTS['TIME_RANGE']['max']} (HHMM format)
- color_temperature: Range {SKY_CONSTRAINTS['COLOR_TEMP_RANGE']['min']}-{SKY_CONSTRAINTS['COLOR_TEMP_RANGE']['max']} Kelvin OR string descriptions
- sky_name: String (default: "{SKY_CONSTRAINTS['DEFAULT_SKY_NAME']}")

**Light Commands:**
- light_name: Required non-empty string for create/update/delete
- location: {{"x": number, "y": number, "z": number}} (default: {LIGHT_CONSTRAINTS['DEFAULT_LOCATION']})
- intensity: Non-negative number (default: {LIGHT_CONSTRAINTS['DEFAULT_INTENSITY']})
- color: {{"r": 0-255, "g": 0-255, "b": 0-255}} (default: {LIGHT_CONSTRAINTS['DEFAULT_COLOR']})

## RANDOM UNIQUENESS
For random elements use timestamp+suffix for unique IDs:
- Light names: "mm_light_{timestamp}_{random_suffix}"
- Wide ranges: Location(-2000,2000), Intensity(500-15000), Colors(0-255 full spectrum)
- Avoid clustering: Use diverse values across entire ranges
- Current: timestamp={timestamp}, suffix={random_suffix}

## CONVERSIONS
**Time:** sunrise→600, sunset→1800, noon→1200, midnight→0
**ColorTemp:** warm→3200K, cool→6500K, warmer→"warmer", cooler→"cooler"
**Colors:** red→{{"r":255,"g":0,"b":0}}, white→{{"r":255,"g":255,"b":255}}, random→use full RGB spectrum
**Cities:** SF(37.7749,-122.4194), NYC(40.7128,-74.0060), Tokyo(35.6804,139.6917)

## VALIDATION RULES
- "cold morning"→time_of_day | "cold light"→color_temperature
- "cooler" ALWAYS = color_temperature (never time)
- All parameters must match schema validation rules
- Return ONLY valid JSON with literal numbers (no Math.random, no code)

Context: {context}

JSON FORMAT:
{{
  "explanation": "Brief description",
  "commands": [{{"type": "command_name", "params": {{...}}}}],
  "expectedResult": "What happens"
}}"""

def execute_command_direct(command: Dict[str, Any]) -> Any:
    """Execute a command directly using Unreal connection (for HTTP bridge) with schema validation."""
    # Validate command using schema
    validated_cmd = validate_command(command)
    
    if not validated_cmd.is_valid:
        raise Exception(f"Command validation failed: {'; '.join(validated_cmd.validation_errors)}")
    
    command_type = validated_cmd.type
    params = validated_cmd.params.copy()
    
    logger.info(f"execute_command_direct: Processing validated {command_type} with params: {params}")
    print(f"DEBUG: execute_command_direct called with validated {command_type}, params: {params}")
    
    # Import tools to get access to connection
    from unreal_mcp_server import get_unreal_connection
    
    # Get connection
    unreal = get_unreal_connection()
    if not unreal:
        raise Exception("Could not connect to Unreal Engine")
    
    # Normalize and validate sky commands
    if command_type in ["set_time_of_day", "set_color_temperature", "get_ultra_dynamic_sky"]:
        params = normalize_sky_parameters(params)
        print(f"DEBUG: {command_type} - normalized params: {params}")
    
    # Handle color temperature string descriptions
    if command_type == "set_color_temperature" and "color_temperature" in params:
        color_temp = params["color_temperature"]
        
        if isinstance(color_temp, str):
            print(f"DEBUG: Processing color temperature description: {color_temp}")
            # Get current temperature for relative adjustments
            current_response = unreal.send_command("get_ultra_dynamic_sky", {})
            current_temp = 6500.0
            if current_response and "result" in current_response and "color_temperature" in current_response["result"]:
                current_temp = float(current_response["result"]["color_temperature"])
            elif current_response and "color_temperature" in current_response:
                current_temp = float(current_response["color_temperature"])
            
            # Use shared temperature mapping function
            try:
                final_temp = map_temperature_description(color_temp, current_temp)
                params["color_temperature"] = final_temp
                print(f"DEBUG: Converted '{color_temp}' to {final_temp}K (from current {current_temp}K)")
            except ValueError as e:
                raise Exception(str(e))
    
    # Normalize and validate light commands
    if command_type in ["create_mm_control_light", "update_mm_control_light"]:
        # Only normalize if we have optional parameters to set defaults for
        if command_type == "create_mm_control_light":
            params = normalize_light_parameters(params)
        print(f"DEBUG: {command_type} - normalized params: {params}")
    
    response = unreal.send_command(command_type, params)
        
    if response and response.get("status") == "error":
        raise Exception(response.get("error", "Unknown Unreal error"))
    
    return response

def execute_command_via_mcp(ctx: Context, command: Dict[str, Any]) -> Any:
    """Execute a command using MCP's tool system."""
    command_type = command.get("type")
    params = command.get("params", {})
    
    logger.info(f"Executing command: {command_type} with params: {params}")
    
    # Import tools to get access to functions
    from unreal_mcp_server import get_unreal_connection
    
    # Get connection
    unreal = get_unreal_connection()
    if not unreal:
        raise Exception("Could not connect to Unreal Engine")
    
    # Execute the appropriate command
    if command_type == "get_actors_in_level":
        response = unreal.send_command("get_actors_in_level", {})
        if response and "result" in response and "actors" in response["result"]:
            return response["result"]["actors"]
        elif response and "actors" in response:
            return response["actors"]
        else:
            return []
            
    elif command_type == "set_time_of_day":
        time_of_day = params.get("time_of_day")
        sky_name = params.get("sky_name")
        if time_of_day is not None:
            response = unreal.send_command("set_time_of_day", {
                "time_of_day": time_of_day,
                "sky_name": sky_name
            })
            return response
        else:
            raise Exception("time_of_day parameter is required")
            
    elif command_type == "get_time_of_day":
        response = unreal.send_command("get_time_of_day", {})
        return response
        
    elif command_type == "create_actor":
        name = params.get("name")
        actor_type = params.get("type")
        if name and actor_type:
            response = unreal.send_command("create_actor", {
                "name": name,
                "type": actor_type,
                "location": params.get("location"),
                "rotation": params.get("rotation"),
                "scale": params.get("scale")
            })
            return response
        else:
            raise Exception("name and type parameters are required")
            
    elif command_type == "delete_actor":
        name = params.get("name")
        if name:
            response = unreal.send_command("delete_actor", {"name": name})
            return response
        else:
            raise Exception("name parameter is required")
            
    elif command_type == "set_actor_transform":
        name = params.get("name")
        if name:
            response = unreal.send_command("set_actor_transform", {
                "name": name,
                "location": params.get("location"),
                "rotation": params.get("rotation"),
                "scale": params.get("scale")
            })
            return response
        else:
            raise Exception("name parameter is required")
            
    elif command_type == "get_actor_properties":
        name = params.get("name")
        if name:
            response = unreal.send_command("get_actor_properties", {"name": name})
            return response
        else:
            raise Exception("name parameter is required")
            
    elif command_type == "set_color_temperature":
        color_temperature = params.get("color_temperature")
        if color_temperature is not None:
            response = unreal.send_command("set_color_temperature", {
                "color_temperature": color_temperature
            })
            return response
        else:
            raise Exception("color_temperature parameter is required")
            
    elif command_type == "set_cesium_latitude_longitude":
        latitude = params.get("latitude")
        longitude = params.get("longitude") 
        
        if latitude is not None and longitude is not None:
            response = unreal.send_command("set_cesium_latitude_longitude", {
                "latitude": latitude,
                "longitude": longitude
            })
            return response
        else:
            raise Exception("latitude and longitude parameters are required")
            
    elif command_type == "get_cesium_properties":
        response = unreal.send_command("get_cesium_properties", {})
        return response
    
    elif command_type == "create_mm_control_light":
        light_name = params.get("light_name")
        if not light_name:
            raise Exception("light_name parameter is required")
        
        command_params = {"light_name": light_name}
        
        if "location" in params:
            command_params["location"] = params["location"]
        if "intensity" in params:
            command_params["intensity"] = params["intensity"]
        if "color" in params:
            command_params["color"] = params["color"]
            
        response = unreal.send_command("create_mm_control_light", command_params)
        return response
    
    elif command_type == "get_mm_control_lights":
        response = unreal.send_command("get_mm_control_lights", {})
        return response
    
    elif command_type == "update_mm_control_light":
        light_name = params.get("light_name")
        if not light_name:
            raise Exception("light_name parameter is required")
        
        command_params = {"light_name": light_name}
        
        if "location" in params:
            command_params["location"] = params["location"]
        if "intensity" in params:
            command_params["intensity"] = params["intensity"]
        if "color" in params:
            command_params["color"] = params["color"]
            
        response = unreal.send_command("update_mm_control_light", command_params)
        return response
    
    elif command_type == "delete_mm_control_light":
        light_name = params.get("light_name")
        if not light_name:
            raise Exception("light_name parameter is required")
            
        response = unreal.send_command("delete_mm_control_light", {"light_name": light_name})
        return response
            
    else:
        raise Exception(f"Unknown command type: {command_type}")