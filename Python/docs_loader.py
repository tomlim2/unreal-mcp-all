"""
Documentation loader for Unreal MCP best practices.
"""

import os
from pathlib import Path

def load_best_practices() -> str:
    """Load the best practices documentation from markdown file."""
    try:
        # Get the directory where this module is located
        current_dir = Path(__file__).parent
        docs_file = current_dir / "docs" / "unreal_mcp_best_practices.md"
        
        # Read the markdown file
        with open(docs_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    except FileNotFoundError:
        return """
        # Unreal MCP Best Practices
        
        Documentation file not found. Please ensure unreal_mcp_best_practices.md exists in the docs/ directory.
        
        ## Basic Usage
        - Use get_actors_in_level() to list all actors
        - Use set_time_of_day(HHMM_format, sky_name) for time control
        - Always use HHMM format (1600) not decimal (16.0) for time values
        """
    
    except Exception as e:
        return f"""
        # Unreal MCP Best Practices
        
        Error loading documentation: {str(e)}
        
        ## Basic Usage
        - Use get_actors_in_level() to list all actors
        - Use set_time_of_day(HHMM_format, sky_name) for time control
        - Always use HHMM format (1600) not decimal (16.0) for time values
        """
