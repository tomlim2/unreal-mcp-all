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

    @mcp.tool()
    def force_sky_update(ctx: Context, sky_name: str = "Ultra_Dynamic_Sky_C_0") -> Dict[str, Any]:
        """Force Ultra Dynamic Sky to update its visual state.
        
        This function attempts to trigger the sky's internal update mechanisms
        without changing the time of day value.
        
        Args:
            ctx: The MCP context
            sky_name: Name of the Ultra Dynamic Sky actor (default: Ultra_Dynamic_Sky_C_0)
            
        Returns:
            Dict containing the result of the operation
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            
            # Get current time of day first
            current_response = unreal.send_command("get_time_of_day", {"sky_name": sky_name})
            
            if not current_response or current_response.get("status") != "success":
                return {"success": False, "error": "Failed to get current time of day"}
            
            current_time = current_response.get("result", {}).get("time_of_day", 1200)
            
            # Set the same time to trigger update functions
            update_response = unreal.send_command("set_time_of_day", {
                "sky_name": sky_name, 
                "time_of_day": current_time
            })
            
            if not update_response:
                return {"success": False, "error": "No response from Unreal Engine"}
            
            return {
                "success": True,
                "message": f"Forced sky update with current time: {current_time}",
                "update_response": update_response
            }
            
        except Exception as e:
            logger.error(f"Error forcing sky update: {e}")
            return {"success": False, "error": str(e)}

    logger.info("Actor tools registered successfully") 