#!/usr/bin/env python3
"""
Test screenshot worker directly to see if it can find the file
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the Python directory to the path
python_dir = Path(__file__).parent
sys.path.insert(0, str(python_dir))

# Load environment variables
load_dotenv()

from tools.workers import JobManager, ScreenshotWorker

def test_screenshot_worker_direct():
    """Test screenshot worker directly"""
    
    job_id = "155e75cd-aaf2-4154-bce2-37f2399e65ac"
    
    print("Screenshot Worker Direct Test:")
    print("=" * 50)
    print(f"Job ID: {job_id}")
    print(f"Project path: {os.getenv('UNREAL_PROJECT_PATH')}")
    
    try:
        # Create job manager and screenshot worker
        job_manager = JobManager()
        screenshot_worker = ScreenshotWorker(
            job_manager=job_manager,
            unreal_connection=None,  # We don't need connection for file access
            project_path=os.getenv('UNREAL_PROJECT_PATH')
        )
        
        print("Screenshot worker created successfully")
        
        # Test getting file path
        file_path = screenshot_worker.get_screenshot_file_path(job_id)
        print(f"File path from worker: {file_path}")
        
        if file_path:
            print(f"File exists: {file_path.exists()}")
            if file_path.exists():
                stat = file_path.stat()
                print(f"File size: {stat.st_size} bytes")
                
                # Test reading first few bytes
                with open(file_path, 'rb') as f:
                    header = f.read(16)
                    print(f"File header (hex): {header.hex()}")
                    png_header = b'\x89PNG'
                    print(f"Is PNG: {header.startswith(png_header)}")
            else:
                # List files in the screenshots directory to debug
                screenshots_dir = Path(os.getenv('UNREAL_PROJECT_PATH')) / "Saved" / "Screenshots"
                print(f"\nDebugging - Screenshots directory: {screenshots_dir}")
                if screenshots_dir.exists():
                    print("Available screenshot files:")
                    for subdir in screenshots_dir.iterdir():
                        if subdir.is_dir():
                            print(f"  {subdir.name}/")
                            for file in subdir.iterdir():
                                if file.is_file() and file.name.endswith('.png'):
                                    print(f"    {file.name}")
        else:
            print("No file path returned from screenshot worker")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_screenshot_worker_direct()