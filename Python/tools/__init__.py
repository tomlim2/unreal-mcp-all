"""
Tools module for Unreal MCP server.

This package contains tools organized by functionality:
- unreal/: Tools for Unreal Engine bridge communication
- ai/: Tools for AI/NLP processing  
- testing/: Tools for development and testing
"""

# Import organized tool modules
from .unreal import (
    register_actor_tools, 
    register_blueprint_tools,
    register_blueprint_node_tools,
    register_editor_tools
)
from .ai import register_nlp_tools
from .testing import register_test_tools

def register_all_tools(mcp_server):
    """
    Register all tools with the MCP server.
    
    Args:
        mcp_server: The MCP server instance to register tools with
    """
    # Register Unreal Engine bridge tools
    register_actor_tools(mcp_server)
    register_blueprint_tools(mcp_server) 
    register_blueprint_node_tools(mcp_server)
    register_editor_tools(mcp_server)
    
    # Register AI/NLP tools
    register_nlp_tools(mcp_server)
    
    # Register testing tools
    register_test_tools(mcp_server) 