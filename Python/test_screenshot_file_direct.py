#!/usr/bin/env python3
"""
Test screenshot file access directly
"""

import sys
import os
from pathlib import Path

# Add the Python directory to the path
python_dir = Path(__file__).parent
sys.path.insert(0, str(python_dir))

def test_screenshot_file_direct():
    """Test direct access to screenshot file"""
    
    job_id = "155e75cd-aaf2-4154-bce2-37f2399e65ac"
    expected_file = Path("E:\\CINEVStudio\\CINEVStudio\\Saved\\Screenshots\\WindowsEditor\\HighresScreenshot00023.png")
    
    print("Direct File Test:")
    print("=" * 50)
    print(f"Job ID: {job_id}")
    print(f"Expected file: {expected_file}")
    print(f"File exists: {expected_file.exists()}")
    
    if expected_file.exists():
        stat = expected_file.stat()
        print(f"File size: {stat.st_size} bytes")
        print(f"File type: {expected_file.suffix}")
    
    # Test with environment variable
    project_path = os.getenv('UNREAL_PROJECT_PATH')
    print(f"\nProject path from env: {project_path}")
    
    if project_path:
        screenshots_dir = Path(project_path) / "Saved" / "Screenshots"
        print(f"Screenshots directory: {screenshots_dir}")
        print(f"Screenshots dir exists: {screenshots_dir.exists()}")
        
        if screenshots_dir.exists():
            print("\nFiles in screenshots directory:")
            for subdir in screenshots_dir.iterdir():
                if subdir.is_dir():
                    print(f"  Subdirectory: {subdir.name}")
                    for file in subdir.iterdir():
                        if file.is_file() and file.name.endswith('.png'):
                            print(f"    {file.name} ({file.stat().st_size} bytes)")
    
    # Test creating a direct file URL
    print(f"\nDirect file URL would be: file://{expected_file}")

if __name__ == "__main__":
    test_screenshot_file_direct()