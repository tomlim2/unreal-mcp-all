"""
Tools module for Unreal MCP server.

This package contains tools for interacting with Unreal Engine.
"""

from . import actor_tools
from . import actor_tools_dynamic_sky

# Export modules
__all__ = ['actor_tools', 'actor_tools_dynamic_sky']

def register_all_tools(mcp_server):
    """
    Register all tools with the MCP server.
    
    Args:
        mcp_server: The MCP server instance to register tools with
    """
    # Register actor tools
    actor_tools.register_actor_tools(mcp_server)
    actor_tools_dynamic_sky.register_actor_tools(mcp_server)
    
    # Register other tool modules as they are added
    # register_material_tools(mcp_server)
    # register_blueprint_tools(mcp_server)
    # etc. 