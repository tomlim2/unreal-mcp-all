"""JSON formatter for CLI output"""
import json
from typing import Any


def format_as_json(data: Any, indent: int = 2) -> str:
    """
    Format data as JSON.

    Args:
        data: Data to format
        indent: Indentation level

    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent)
