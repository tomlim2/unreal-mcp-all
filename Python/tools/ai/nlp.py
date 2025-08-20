"""
Natural Language Processing Tools for Unreal MCP.

This module provides tools for processing natural language commands and translating them
to appropriate Unreal Engine operations.
"""

import logging
import json
import os
import sys
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP, Context

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
    """
    Implementation of natural language processing (non-decorated version).
    
    Args:
        user_input: The natural language command from the user
        context: Optional context about the current Unreal Engine state
        
    Returns:
        Dict containing explanation, executed commands, and results
    """
    try:
        # Check if Anthropic SDK is available
        if not ANTHROPIC_AVAILABLE:
            return {
                "error": "Anthropic SDK not installed. Run: pip install anthropic",
                "explanation": "Natural language processing unavailable", 
                "commands": [],
                "executionResults": []
            }
        
        # Get API key from environment (now loaded from .env file)
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
        system_prompt = build_system_prompt(context or "User is working with Unreal Engine project")
        
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
        logger.info(f"AI response: {ai_response}")
        
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
        
        # Execute commands using direct connection
        execution_results = []
        if parsed_response.get("commands") and isinstance(parsed_response["commands"], list):
            for command in parsed_response["commands"]:
                try:
                    result = execute_command_direct(command)
                    execution_results.append({
                        "command": command.get("type", "unknown"),
                        "success": True,
                        "result": result
                    })
                    logger.info(f"Successfully executed command: {command.get('type')}")
                except Exception as e:
                    execution_results.append({
                        "command": command.get("type", "unknown"),
                        "success": False,
                        "error": str(e)
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
    """Register natural language processing tools with the MCP server."""
    
    @mcp.tool()
    def process_natural_language(ctx: Context, user_input: str, context: str = None) -> Dict[str, Any]:
        """
        Process natural language input and execute appropriate Unreal Engine commands.
        
        Args:
            user_input: The natural language command from the user
            context: Optional context about the current Unreal Engine state
            
        Returns:
            Dict containing explanation, executed commands, and results
        """
        return _process_natural_language_impl(user_input, context)

def build_system_prompt(context: str) -> str:
    """Build the system prompt for the AI with available commands."""
    return f"""You are an AI assistant that translates natural language requests into Unreal Engine commands via MCP protocol.

Available Unreal MCP commands:
- get_ultra_dynamic_sky: Get Ultra Dynamic Sky actor info and current time of day
- get_time_of_day: Get current time from Ultra Dynamic Sky
- set_time_of_day: Set time in HHMM format (0000-2359), params: {{time_of_day: number, sky_name?: string}}
- set_color_temperature: Set lighting color temperature in Kelvin (1500-15000), params: {{color_temperature: number}}
- get_actors_in_level: List all actors in level
- create_actor: Create new actor, params: {{name: string, type: string, location?: [x,y,z], rotation?: [x,y,z], scale?: [x,y,z]}}
- delete_actor: Delete actor by name, params: {{name: string}}
- set_actor_transform: Move/rotate/scale actor, params: {{name: string, location?: [x,y,z], rotation?: [x,y,z], scale?: [x,y,z]}}
- get_actor_properties: Get actor properties, params: {{name: string}}

IMPORTANT - Time Format Conversion Rules:
When user requests time changes, convert natural language to HHMM format:
- "sunrise" or "6 AM" → time_of_day: 600
- "sunset" or "6 PM" → time_of_day: 1800
- "1 PM" → time_of_day: 1300
- "23:30" → time_of_day: 2330
- "12:30 AM" → time_of_day: 30
- "noon" → time_of_day: 1200
- "midnight" → time_of_day: 0

IMPORTANT - Color Temperature Conversion Rules:
When user requests color/lighting changes (NOT time-related), use color temperature commands:
- "make it warm" or "warm light" → set_color_temperature with description: "warm"
- "make it cold" or "cold light" → set_color_temperature with description: "cold" 
- "warmer" or "more warm" → set_color_temperature with description: "warmer"
- "cooler" or "more cool" → set_color_temperature with description: "cooler"
- "sunset lighting" → set_color_temperature with description: "sunset"
- "daylight" → set_color_temperature with description: "daylight"
- Specific Kelvin values → set_color_temperature with color_temperature: number

DISAMBIGUATION: 
- If user mentions "cold evening" or "cold morning" → use set_time_of_day for time of day
- If user mentions "cold light" or "make it cold" → use set_color_temperature for lighting color

Context: {context}

Return a JSON response with:
{{
  "explanation": "What you understood from the request",
  "commands": [
    {{
      "type": "command_name",
      "params": {{...}}
    }}
  ],
  "expectedResult": "What the user should expect to see"
}}"""

def execute_command_direct(command: Dict[str, Any]) -> Any:
    """Execute a command directly using Unreal connection (for HTTP bridge)."""
    command_type = command.get("type")
    params = command.get("params", {})
    
    logger.info(f"Executing command: {command_type} with params: {params}")
    
    # Import tools to get access to connection
    from unreal_mcp_server import get_unreal_connection
    
    # Get connection
    unreal = get_unreal_connection()
    if not unreal:
        raise Exception("Could not connect to Unreal Engine")
    
    # Execute the command normally (set_color_temperature now handles both numeric and description inputs)
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
            
            
    else:
        raise Exception(f"Unknown command type: {command_type}")