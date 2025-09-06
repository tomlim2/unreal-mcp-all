#!/usr/bin/env python3
"""
HTTP Bridge Starter Module

This module provides a way to start the HTTP bridge from the tools package.
It imports and runs the main HTTP bridge functionality.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path to access http_bridge
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import the main HTTP bridge
from http_bridge import main

if __name__ == "__main__":
    # Run the HTTP bridge main function
    sys.exit(main())