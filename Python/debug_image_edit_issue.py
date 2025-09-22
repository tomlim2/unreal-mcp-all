#!/usr/bin/env python3
"""
Debug script for image editing issue with img_079.
"""

import os
import sys
from pathlib import Path

# Add the tools directory to Python path
tools_dir = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_dir))

def debug_image_edit_issue():
    """Debug the image editing issue with img_079."""
    print("=" * 60)
    print("IMAGE EDIT DEBUG")
    print("=" * 60)

    try:
        from ai.uid_manager import get_uid_mapping
        from ai.command_handlers.nano_banana.image_edit import NanoBananaImageEditHandler
        print("✅ Successfully imported modules")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False

    # Check UID mapping for img_079
    print("🔍 Checking UID mapping for img_079:")
    mapping = get_uid_mapping("img_079")

    if mapping:
        print(f"   ✅ UID found:")
        print(f"   - Filename: {mapping.get('filename')}")
        print(f"   - File path: {mapping.get('metadata', {}).get('file_path')}")
        print(f"   - Created: {mapping.get('created_at')}")
        print(f"   - Session: {mapping.get('session_id')}")

        file_path = mapping.get('metadata', {}).get('file_path')
        if file_path:
            exists = os.path.exists(file_path)
            print(f"   - File exists: {exists}")
            if not exists:
                print(f"   ❌ File not found at: {file_path}")
            else:
                print(f"   ✅ File found at: {file_path}")
        else:
            print(f"   ❌ No file_path in metadata")
    else:
        print(f"   ❌ UID img_079 not found in mapping table")

    # Test image resolution
    print(f"\n🔍 Testing image path resolution:")
    handler = NanoBananaImageEditHandler()

    test_cases = [
        "img_079",  # UID
        "ScreenShot00075.png",  # Filename (should fail with our strict policy)
    ]

    for test_input in test_cases:
        print(f"   Testing: {test_input}")
        try:
            resolved_path = handler._resolve_image_path(test_input)
            if resolved_path:
                print(f"   ✅ Resolved to: {resolved_path}")
                print(f"   File exists: {os.path.exists(resolved_path)}")
            else:
                print(f"   ❌ Failed to resolve")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

    # Check what the AI command actually sent
    print(f"\n🔍 Analyzing the command that failed:")
    failed_command = {
        "type": "transform_image_style",
        "params": {
            "image_url": "ScreenShot00075.png",  # This is wrong - should be img_079
            "style_prompt": "a person in a yellow raincoat jumping and playing in a puddle",
            "session_id": "7048e9d1-3dc7-484e-bde0-c72505a3266a",
            "image_uid": "img_079",  # This is correct
            "image_path": "ScreenShot00075.png"  # This is wrong
        }
    }

    print(f"   Command params:")
    for key, value in failed_command["params"].items():
        print(f"   - {key}: {value}")

    print(f"\n📝 Problem Analysis:")
    print(f"   The AI command has inconsistent parameters:")
    print(f"   - image_url: 'ScreenShot00075.png' (filename - WRONG)")
    print(f"   - image_uid: 'img_079' (UID - CORRECT)")
    print(f"   - image_path: 'ScreenShot00075.png' (filename - WRONG)")
    print(f"   ")
    print(f"   The image_url should be 'img_079', not the filename!")

    return True

if __name__ == "__main__":
    debug_image_edit_issue()