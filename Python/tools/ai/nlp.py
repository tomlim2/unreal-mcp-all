"""
MegaMelange Natural Language Processing Module

## Target User & Design Philosophy

**Primary User**: Creative professionals in their 20's (directors, cinematographers, technical artists) 
working with Unreal Engine for film, game development, and virtual production.

**Core Principles**:
- **Intuitive Creative Control**: Natural language commands for complex Unreal Engine operations
- **Professional Workflow Integration**: Support for industry-standard pipelines and tools
- **Real-time Iteration**: Immediate visual feedback for creative decision-making
- **Modular Extensibility**: Easy addition of new creative tools and rendering features
- **Cross-Platform Accessibility**: Web interface, MCP clients, and direct API access

This module translates natural language input from creative professionals into structured
Unreal Engine commands, enabling intuitive control over lighting, camera work, materials,
and scene composition through conversational interfaces.
"""

import logging
import json
import os
import sys
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP, Context
from .nlp_schema_validator import (
    SKY_CONSTRAINTS,
    LIGHT_CONSTRAINTS
)
from .command_handlers import get_command_registry

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

# Import session management
from .session_management import get_session_manager, SessionContext

# Import model providers
from .model_providers import get_model_provider, get_default_model, get_available_models

def _process_natural_language_impl(user_input: str, context: str = None, session_id: str = None, llm_model: str = None) -> Dict[str, Any]:
    try:
        # Get session manager and session context if session_id provided
        session_manager = None
        session_context = None
        if session_id:
            session_manager = get_session_manager()
            session_context = session_manager.get_or_create_session(session_id)
            logger.info(f"Using session context: {session_id}")
        else:
            logger.info("No session ID provided, processing without session context")
        
        # Determine which model to use
        selected_model = llm_model
        logger.info(f"Using model: {selected_model}")
        # Get the model provider
        provider = get_model_provider(selected_model)
        if not provider:
            # Try to fall back to any available model
            available_models = get_available_models()
            if available_models:
                fallback_model = available_models[0]
                provider = get_model_provider(fallback_model)
                selected_model = fallback_model
                logger.warning(f"Model {selected_model} not available, using {fallback_model}")
            else:
                return {
                    "error": f"No AI models available. Configure ANTHROPIC_API_KEY or GOOGLE_API_KEY",
                    "explanation": "Natural language processing unavailable",
                    "commands": [],
                    "executionResults": []
                }
        
        # Build system prompt with session context
        system_prompt = build_system_prompt_with_session(context or "Assume as you are a creative cinematic director", session_context)
        logger.info(f"Processing natural language input with {provider.get_model_name()}: {user_input}")
        
        # Build messages list including conversation history
        messages = []
        
        # Add conversation history as proper messages
        if session_context and session_context.conversation_history:
            recent_messages = session_context.conversation_history[-4:]  # Last 4 messages (2 turns)
            for msg in recent_messages:
                if msg.role in ['user', 'assistant']:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
        
        # Add current user input as the final message
        messages.append({
            "role": "user", 
            "content": f"User request: {user_input}"
        })
        
        # Generate AI response using the selected provider
        ai_response = provider.generate_response(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=1024,
            temperature=0.1
        )
        logger.info(f"AI response from {provider.get_model_name()} for '{user_input}': {ai_response}")
        print(f"DEBUG: AI response from {provider.get_model_name()} for '{user_input}': {ai_response}")

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
                    
                    # Commands are now validated by handler system in execute_command_direct
                    # No need for pre-validation here as handlers manage their own validation
                    
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
        # Prepare final response
        result = {
            "explanation": parsed_response.get("explanation", "Processed your request"),
            "commands": parsed_response.get("commands", []),
            "expectedResult": parsed_response.get("expectedResult", "Commands executed"),
            "executionResults": execution_results
        }
        
        # Update session with this interaction and model preference if session_id provided
        if session_manager and session_context:
            # First add the interaction
            session_manager.add_interaction(session_id, user_input, result)
            logger.debug(f"Updated session {session_id} with interaction")
            
            # Then update preferred model if explicitly provided (after interaction is saved)
            if llm_model:
                current_model = session_context.get_llm_model()
                logger.info(f"Current model: {current_model}, Requested model: {llm_model}")
                
                if llm_model != current_model:
                    try:
                        # Get fresh session context after interaction was added
                        updated_session = session_manager.get_session(session_id)
                        if updated_session:
                            logger.info(f"Updating model from {updated_session.get_llm_model()} to {llm_model}")
                            updated_session.set_llm_model(llm_model)
                            success = session_manager.update_session(updated_session)
                            logger.info(f"Updated preferred model for session {session_id} to {llm_model}, success: {success}")
                            
                            # Verify the update
                            verification_session = session_manager.get_session(session_id)
                            if verification_session:
                                logger.info(f"Verification: model is now {verification_session.get_llm_model()}")
                        else:
                            logger.warning(f"Could not retrieve session {session_id} for model update")
                    except Exception as save_error:
                        logger.error(f"Error saving model preference: {save_error}")
                else:
                    logger.info(f"Model already set to {llm_model}, no update needed")
        
        return result
    except Exception as e:
        logger.error(f"Error in process_natural_language: {e}")
        return {
            "error": str(e),
            "explanation": "An error occurred while processing your request",
            "commands": [],
            "executionResults": []
        }

def register_nlp_tools(mcp: FastMCP):
    # No NLP tools to register - use process_natural_language() function directly
    pass

# Main function for external use with session support
def process_natural_language(user_input: str, context: str = None, session_id: str = None, llm_model: str = None) -> Dict[str, Any]:
    """Process natural language input and return structured commands with optional session support."""
    try:
        return _process_natural_language_impl(user_input, context, session_id, llm_model)
    except Exception as e:
        logger.error(f"Error in process_natural_language: {e}")
        return {
            "error": str(e),
            "explanation": "An error occurred while processing your request",
            "commands": [],
            "executionResults": []
        }

def build_system_prompt_with_session(context: str, session_context: SessionContext = None) -> str:
    """Build system prompt with session context information."""
    import time
    import random
    timestamp = int(time.time() * 1000)
    random_suffix = random.randint(1000, 9999)
    
    # Get supported commands from registry
    registry = get_command_registry()
    supported_commands = registry.get_supported_commands()
    
    base_prompt = f"""You are an AI assistant for creative professionals in their 20's (directors, cinematographers, technical artists) working with Unreal Engine for film, game development, and virtual production.

Your role is to provide intuitive creative control by translating natural language requests into precise Unreal Engine commands that support professional workflows and enable real-time creative iteration.

## SUPPORTED COMMANDS
**Scene Environment:**
- Ultra Dynamic Sky: get_ultra_dynamic_sky, set_time_of_day, set_color_temperature
- Ultra Dynamic Weather: get_ultra_dynamic_weather, set_current_weather_to_rain
- Geospatial: set_cesium_latitude_longitude, get_cesium_properties

**Scene Objects & Lighting:**
- Actors: get_actors_in_level, create_actor, delete_actor, set_actor_transform, get_actor_properties  
- Cinematic Lighting: create_mm_control_light, get_mm_control_lights, update_mm_control_light, delete_mm_control_light

**Rendering & Capture:**
- Screenshots: take_highresshot (execute screenshot command)

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

**Cesium Commands:**
- latitude: Number between -90 and 90 degrees
- longitude: Number between -180 and 180 degrees

**Actor Commands:**
- name: Required non-empty string for most operations
- type: Required for create_actor (e.g., "StaticMeshActor", "PointLight")
- location/rotation/scale: Optional Vector3 objects {{"x": number, "y": number, "z": number}}

**Screenshot Commands:**
- take_highresshot: Execute screenshot command
  - resolution_multiplier: Optional float 1.0-8.0 (default: 1.0)
  - include_ui: Optional boolean (default: false)
  - Returns: success confirmation

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
- All parameters validated by specialized handlers
- Return ONLY valid JSON with literal numbers (no Math.random, no code)
- Commands are processed by modular handler system for consistency"""

    if session_context:
        # Add scene state
        scene_summary = session_context.get_scene_summary()
        if scene_summary and scene_summary != "No scene state tracked yet.":
            base_prompt += f"\n\n## CURRENT SCENE STATE\n{scene_summary}"
            base_prompt += "\n- Use this information to make informed decisions about lighting, positioning, and scene modifications"
            base_prompt += "\n- Reference existing elements when relevant (e.g., 'move the red light', 'adjust the current sky time')"
    
    base_prompt += f"\n\nContext: {context}\n\nJSON FORMAT:\n{{\n  \"explanation\": \"Brief description\",\n  \"commands\": [{{\"type\": \"command_name\", \"params\": {{...}}}}],\n  \"expectedResult\": \"What happens\"\n}}"
    
    return base_prompt


def execute_command_direct(command: Dict[str, Any]) -> Any:
    """Execute a command directly using Unreal connection with new handler system."""
    logger.info(f"execute_command_direct: Processing {command.get('type')} with params: {command.get('params', {})}")
    print(f"DEBUG: execute_command_direct called with {command.get('type')}, params: {command.get('params', {})}")
    
    # Import tools to get access to connection
    from unreal_mcp_server import get_unreal_connection
    
    # Get connection
    unreal = get_unreal_connection()
    if not unreal:
        raise Exception("Could not connect to Unreal Engine")
    
    # Use command registry for unified execution
    registry = get_command_registry()
    result = registry.execute_command(command, unreal)
    
    # Screenshot commands now use synchronous execution - no special handling needed
    # The C++ HandleTakeHighResShot now calls HandleImmediateScreenshot which waits for completion
    
    return result

def execute_command_via_mcp(ctx: Context, command: Dict[str, Any]) -> Any:
    """Execute a command using MCP's tool system (legacy compatibility wrapper)."""
    logger.info(f"execute_command_via_mcp (legacy): {command.get('type')} with params: {command.get('params', {})}")
    
    # Use the same unified execution path as direct commands
    return execute_command_direct(command)