"""
Actor Tools for Unreal MCP.

This module provides tools for creating, manipulating, and inspecting actors in Unreal Engine.
"""

import logging
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP, Context

# Get logger
logger = logging.getLogger("UnrealMCP")

def register_actor_tools(mcp: FastMCP):
    """Register actor tools with the MCP server."""
    
    @mcp.tool()
    def get_actors_in_level(ctx: Context) -> List[Dict[str, Any]]:
        """Get a list of all actors in the current level."""
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            response = unreal.send_command("get_actors_in_level", {})
            
            if not response:
                logger.warning("No response from Unreal Engine")
                return []
                
            # Log the complete response for debugging
            logger.info(f"Complete response from Unreal: {response}")
            
            # Check response format
            if "result" in response and "actors" in response["result"]:
                actors = response["result"]["actors"]
                logger.info(f"Found {len(actors)} actors in level")
                return actors
            elif "actors" in response:
                actors = response["actors"]
                logger.info(f"Found {len(actors)} actors in level")
                return actors
                
            logger.warning(f"Unexpected response format: {response}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting actors: {e}")
            return []

    @mcp.tool()
    def find_actors_by_name(ctx: Context, pattern: str) -> List[str]:
        """Find actors by name pattern."""
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            response = unreal.send_command("find_actors_by_name", {
                "pattern": pattern
            })
            
            if not response:
                return []
                
            return response.get("actors", [])
            
        except Exception as e:
            logger.error(f"Error finding actors: {e}")
            return []
    
    @mcp.tool()
    def create_actor(
        ctx: Context,
        name: str,
        type: str,
        location: List[float] = [0.0, 0.0, 0.0],
        rotation: List[float] = [0.0, 0.0, 0.0],
        scale: List[float] = [1.0, 1.0, 1.0]
    ) -> Dict[str, Any]:
        """Create a new actor in the current level.
        
        Args:
            ctx: The MCP context
            name: The name to give the new actor (must be unique)
            type: The type of actor to create (e.g. StaticMeshActor, PointLight)
            location: The [x, y, z] world location to spawn at
            rotation: The [pitch, yaw, roll] rotation in degrees
            scale: The [x, y, z] scale to apply
            
        Returns:
            Dict containing the created actor's properties
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            
            # Ensure all parameters are properly formatted
            params = {
                "name": name,
                "type": type.upper(),  # Make sure type is uppercase
                "location": location,
                "rotation": rotation,
                "scale": scale
            }
            
            # Validate location, rotation, and scale formats
            for param_name in ["location", "rotation", "scale"]:
                param_value = params[param_name]
                if not isinstance(param_value, list) or len(param_value) != 3:
                    logger.error(f"Invalid {param_name} format: {param_value}. Must be a list of 3 float values.")
                    return {"success": False, "message": f"Invalid {param_name} format. Must be a list of 3 float values."}
                # Ensure all values are float
                params[param_name] = [float(val) for val in param_value]
            
            logger.info(f"Creating actor '{name}' of type '{type}' with params: {params}")
            response = unreal.send_command("create_actor", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            # Log the complete response for debugging
            logger.info(f"Actor creation response: {response}")
            
            # Handle error responses correctly
            if response.get("status") == "error":
                error_message = response.get("error", "Unknown error")
                logger.error(f"Error creating actor: {error_message}")
                return {"success": False, "message": error_message}
            
            return response
            
        except Exception as e:
            error_msg = f"Error creating actor: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @mcp.tool()
    def delete_actor(ctx: Context, name: str) -> Dict[str, Any]:
        """Delete an actor by name."""
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            response = unreal.send_command("delete_actor", {
                "name": name
            })
            return response or {}
            
        except Exception as e:
            logger.error(f"Error deleting actor: {e}")
            return {}
    
    @mcp.tool()
    def set_actor_transform(
        ctx: Context,
        name: str,
        location: List[float] = None,
        rotation: List[float] = None,
        scale: List[float] = None
    ) -> Dict[str, Any]:
        """Set the transform of an actor."""
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            params = {"name": name}
            if location is not None:
                params["location"] = location
            if rotation is not None:
                params["rotation"] = rotation
            if scale is not None:
                params["scale"] = scale
                
            response = unreal.send_command("set_actor_transform", params)
            return response or {}
            
        except Exception as e:
            logger.error(f"Error setting transform: {e}")
            return {}
    
    @mcp.tool()
    def get_actor_properties(ctx: Context, name: str) -> Dict[str, Any]:
        """Get all properties of an actor."""
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            response = unreal.send_command("get_actor_properties", {
                "name": name
            })
            return response or {}
            
        except Exception as e:
            logger.error(f"Error getting properties: {e}")
            return {}


    # === DYNAMIC SKY TOOLS ===
    
    @mcp.tool()
    def get_time_of_day(ctx: Context, sky_name: str = "Ultra_Dynamic_Sky_C_0") -> Dict[str, Any]:
        """Get the time of day from Ultra Dynamic Sky.
        
        Args:
            ctx: The MCP context
            sky_name: Name of the Ultra Dynamic Sky actor (default: Ultra_Dynamic_Sky_C_0)
            
        Returns:
            Dict containing the time of day value
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            response = unreal.send_command("get_time_of_day", {"sky_name": sky_name})
            
            if not response:
                logger.warning("No response from Unreal Engine")
                return {"success": False, "error": "No response from Unreal Engine"}
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting time of day: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def set_time_of_day(ctx: Context, time_of_day: float, sky_name: str = "Ultra_Dynamic_Sky_C_0") -> Dict[str, Any]:
        """Set the time of day in Ultra Dynamic Sky.
        
        Args:
            ctx: The MCP context
            time_of_day: Time of day value (0-24 hours)
            sky_name: Name of the Ultra Dynamic Sky actor (default: Ultra_Dynamic_Sky_C_0)
            
        Returns:
            Dict containing the result of the operation
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            # Validate time_of_day range - supports both decimal hours (0-24) and HHMM format (0-2400)
            if time_of_day < 0 or time_of_day > 2400:
                return {"success": False, "error": "Time of day must be between 0 and 2400 (HHMM format) or 0-24 (decimal hours)"}
            
            unreal = get_unreal_connection()
            response = unreal.send_command("set_time_of_day", {"sky_name": sky_name, "time_of_day": time_of_day})
            
            if not response:
                logger.warning("No response from Unreal Engine")
                return {"success": False, "error": "No response from Unreal Engine"}
            
            return response
            
        except Exception as e:
            logger.error(f"Error setting time of day: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_ultra_dynamic_sky(ctx: Context) -> Dict[str, Any]:
        """Get Ultra Dynamic Sky actor information and current time of day.
        
        This function retrieves the Ultra Dynamic Sky actor and its time of day value
        using the direct get_ultra_dynamic_sky command.
        
        Args:
            ctx: The MCP context
            
        Returns:
            Dict containing the sky actor name and time of day value
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            response = unreal.send_command("get_ultra_dynamic_sky", {})
            
            if not response:
                logger.warning("No response from Unreal Engine")
                return {"success": False, "error": "No response from Unreal Engine"}
            
            # Log the response for debugging
            logger.info(f"get_ultra_dynamic_sky response: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting ultra dynamic sky: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def set_color_temperature(ctx: Context, color_temperature: float = None, description: str = None) -> Dict[str, Any]:
        """Set or adjust the color temperature in Ultra Dynamic Sky.
        
        Args:
            ctx: The MCP context
            color_temperature: Exact color temperature value in Kelvin (1500-15000)
            description: Natural language description (e.g., "warm", "cold", "warmer", "cooler", "very warm", "sunset", "daylight")
            
        Returns:
            Dict containing the result of the operation
            
        Examples:
            set_color_temperature(color_temperature=3200)  # Set to 3200K
            set_color_temperature(description="warm")      # Set to warm lighting
            set_color_temperature(description="warmer")    # Make current lighting warmer
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            # Must provide either color_temperature or description
            if color_temperature is None and description is None:
                return {"success": False, "error": "Must provide either color_temperature (numeric) or description (text)"}
            
            if color_temperature is not None and description is not None:
                return {"success": False, "error": "Provide either color_temperature OR description, not both"}
            
            unreal = get_unreal_connection()
            final_temp = None
            interpretation_info = None
            
            if color_temperature is not None:
                # Direct numeric temperature
                if color_temperature < 1500 or color_temperature > 15000:
                    return {"success": False, "error": "Color temperature must be between 1500 and 15000 Kelvin"}
                final_temp = color_temperature
                
            else:
                # Natural language description - need to get current temperature first
                current_response = unreal.send_command("get_ultra_dynamic_sky", {})
                current_temp = 6500.0
                if current_response and "color_temperature" in current_response:
                    current_temp = float(current_response["color_temperature"])
                
                # Parse natural language description
                desc_lower = description.lower().strip()
                
                # Determine new temperature based on description
                # Note: Lower Kelvin = warmer (more red/orange), Higher Kelvin = cooler (more blue/white)
                if "very warm" in desc_lower or "extremely warm" in desc_lower:
                    final_temp = 2700.0  # Very warm candle light
                elif "warm" in desc_lower and ("more" in desc_lower or "er" in desc_lower):
                    final_temp = max(1500.0, current_temp - 1000.0)  # Make warmer
                elif "warm" in desc_lower:
                    final_temp = 3200.0  # Standard warm white
                elif "very cold" in desc_lower or "extremely cold" in desc_lower:
                    final_temp = 10000.0  # Very cold blue
                elif "cold" in desc_lower and ("more" in desc_lower or "er" in desc_lower):
                    final_temp = min(15000.0, current_temp + 1000.0)  # Make cooler
                elif "cold" in desc_lower or "cool" in desc_lower:
                    final_temp = 8000.0  # Standard cool white
                elif "daylight" in desc_lower or "neutral" in desc_lower:
                    final_temp = 6500.0  # Standard daylight
                elif "sunset" in desc_lower or "golden" in desc_lower:
                    final_temp = 2200.0  # Sunset/golden hour
                elif "noon" in desc_lower or "bright" in desc_lower:
                    final_temp = 5600.0  # Noon daylight
                else:
                    return {"success": False, "error": f"Could not interpret color description: '{description}'. Try 'warm', 'cold', 'warmer', 'cooler', 'daylight', 'sunset', etc."}
                
                # Create interpretation info
                interpretation_info = {
                    "description": description,
                    "previous_temp": current_temp,
                    "new_temp": final_temp,
                    "change": "warmer" if final_temp < current_temp else "cooler" if final_temp > current_temp else "unchanged"
                }
            
            # Set the temperature
            response = unreal.send_command("set_color_temperature", {"color_temperature": final_temp})
            
            if not response:
                logger.warning("No response from Unreal Engine")
                return {"success": False, "error": "No response from Unreal Engine"}
            
            # Add interpretation info to response if using natural language
            if interpretation_info and isinstance(response, dict):
                response["interpretation"] = interpretation_info
            
            return response
            
        except Exception as e:
            logger.error(f"Error setting color temperature: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def debug_sky_properties(ctx: Context, sky_name: str = "Ultra_Dynamic_Sky_C_0") -> Dict[str, Any]:
        """Debug function to list all properties of Ultra Dynamic Sky actor.
        
        Args:
            ctx: The MCP context
            sky_name: Name of the Ultra Dynamic Sky actor (default: Ultra_Dynamic_Sky_C_0)
            
        Returns:
            Dict containing all properties and their types
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            response = unreal.send_command("get_actor_properties", {"name": sky_name})
            
            if not response:
                logger.warning("No response from Unreal Engine")
                return {"success": False, "error": "No response from Unreal Engine"}
            
            # Also try to get time of day to see what error we get
            time_response = unreal.send_command("get_time_of_day", {"sky_name": sky_name})
            
            return {
                "actor_properties": response,
                "time_of_day_attempt": time_response,
                "sky_name": sky_name
            }
            
        except Exception as e:
            logger.error(f"Error debugging sky properties: {e}")
            return {"success": False, "error": str(e)}

    logger.info("Actor tools registered successfully") 