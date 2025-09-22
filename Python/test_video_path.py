#!/usr/bin/env python3
"""
Test video file path resolution.
"""

import os
from pathlib import Path

# Set project path
os.environ['UNREAL_PROJECT_PATH'] = 'E:\\CINEVStudio\\CINEVStudio'

def test_video_path():
    # Simulate the path resolution logic from HTTP bridge
    path = '/api/video/gentle_zoom_in_VEO_1758517786.mp4'
    path_parts = path.split('/')

    print(f"Original path: {path}")
    print(f"Path parts: {path_parts}")
    print(f"Length: {len(path_parts)}")

    if len(path_parts) == 4 and path_parts[1] == 'api':
        endpoint_type = path_parts[2]
        filename = path_parts[3]

        print(f"Endpoint type: {endpoint_type}")
        print(f"Filename: {filename}")

        if endpoint_type in ['video-file', 'video']:
            print("✅ Video endpoint detected")

            project_path = os.getenv('UNREAL_PROJECT_PATH')
            print(f"Project path: {project_path}")

            video_dir = Path(project_path) / "Saved" / "Videos" / "generated"
            file_path = video_dir / filename

            print(f"Video directory: {video_dir}")
            print(f"Full file path: {file_path}")
            print(f"File exists: {file_path.exists()}")

            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"File size: {file_size} bytes")

                if filename.lower().endswith('.mp4'):
                    print("✅ Valid MP4 file")
                else:
                    print("❌ Not an MP4 file")
            else:
                print("❌ File does not exist")
        else:
            print("❌ Not a video endpoint")
    else:
        print("❌ Invalid path structure")

if __name__ == '__main__':
    test_video_path()