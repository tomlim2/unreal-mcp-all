#!/usr/bin/env python3
"""
Check if screenshot file exists for a specific job ID
"""

import sys
from pathlib import Path

# Add the Python directory to the path
python_dir = Path(__file__).parent
sys.path.insert(0, str(python_dir))

from tools.workers import ScreenshotWorker

def check_screenshot_file():
    """Check if screenshot file exists for the job ID"""
    
    job_id = "155e75cd-aaf2-4154-bce2-37f2399e65ac"
    
    # Create screenshot worker
    screenshot_worker = ScreenshotWorker()
    
    # Get file path
    file_path = screenshot_worker.get_screenshot_file_path(job_id)
    
    print(f"Job ID: {job_id}")
    print(f"Expected file path: {file_path}")
    
    if file_path:
        print(f"File exists: {file_path.exists()}")
        if file_path.exists():
            stat = file_path.stat()
            print(f"File size: {stat.st_size} bytes")
            print(f"File type: {file_path.suffix}")
        else:
            # Try to find similar files in the directory
            if file_path.parent.exists():
                print(f"Directory exists, files in directory:")
                for f in file_path.parent.iterdir():
                    if f.is_file():
                        print(f"  {f.name} ({f.stat().st_size} bytes)")
    else:
        print("No file path returned from screenshot worker")

if __name__ == "__main__":
    check_screenshot_file()