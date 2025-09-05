#!/usr/bin/env python3
"""
Test environment variable loading
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def test_env_loading():
    """Test if environment variables are loaded correctly"""
    
    print("Environment Variable Test:")
    print("=" * 50)
    
    # Check current working directory
    print(f"Current directory: {os.getcwd()}")
    
    # Check if .env file exists
    env_file = Path(".env")
    print(f".env file exists: {env_file.exists()}")
    if env_file.exists():
        print(f".env file path: {env_file.absolute()}")
        print("\nContents of .env file:")
        with open(env_file) as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip().startswith('#'):
                    print(f"  {line_num}: {line.strip()}")
    
    # Test loading .env
    print("\nLoading .env file...")
    loaded = load_dotenv()
    print(f"load_dotenv() returned: {loaded}")
    
    # Check environment variables
    print(f"\nUNREAL_PROJECT_PATH: {os.getenv('UNREAL_PROJECT_PATH')}")
    print(f"ANTHROPIC_API_KEY: {'***' if os.getenv('ANTHROPIC_API_KEY') else None}")
    print(f"SUPABASE_URL: {'***' if os.getenv('SUPABASE_URL') else None}")

if __name__ == "__main__":
    test_env_loading()