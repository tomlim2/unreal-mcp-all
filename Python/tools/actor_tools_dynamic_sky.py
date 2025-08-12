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