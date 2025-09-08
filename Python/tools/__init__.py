"""
Tools module for Unreal MCP server.

This package contains tools organized by functionality:
- unreal/: Tools for Unreal Engine bridge communication
- ai/: Tools for AI/NLP processing  
"""

# Import organized tool modules
from .ai import register_nlp_tools

def register_all_tools(mcp_server):
    """
    Register all tools with the MCP server.
    
    Args:
        mcp_server: The MCP server instance to register tools with
    """
    # Register AI/NLP tools
    register_nlp_tools(mcp_server) 