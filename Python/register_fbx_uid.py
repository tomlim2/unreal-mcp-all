"""
Script to manually register the FBX UID (fbx_001) in the UID manager.
This ensures the UID system properly tracks the manually created FBX entry.
"""

import sys
from pathlib import Path

# Add Python tools to path
sys.path.insert(0, str(Path(__file__).parent))

from core.resources.uid_manager import get_uid_manager

def register_fbx_uid():
    """Register fbx_001 as a manual FBX test UID"""
    uid_manager = get_uid_manager()

    # Add mapping for fbx_001
    uid_manager.add_mapping(
        uid="fbx_001",
        content_type="object3d_fbx",
        filename="R6ForUnreal.fbx",
        parent_uid=None,
        session_id="manual_fbx_test",
        metadata={
            "source": "manual_registration",
            "format": "fbx",
            "user_id": 999999,
            "username": "TestFBXUser",
            "rig_type": "R6",
            "description": "Manually created FBX UID for import testing"
        }
    )

    print("✅ Successfully registered fbx_001")
    print(f"   UID: fbx_001")
    print(f"   Format: FBX")
    print(f"   File: R6ForUnreal.fbx")
    print(f"   User: TestFBXUser (ID: 999999)")

    # Verify registration
    from core.resources.uid_manager import get_uid_mapping
    mapping = get_uid_mapping("fbx_001")

    if mapping:
        print(f"\n✅ Verification: UID mapping found")
        print(f"   Type: {mapping.get('type')}")
        print(f"   Filename: {mapping.get('filename')}")
        print(f"   Metadata: {mapping.get('metadata')}")
    else:
        print("\n❌ Warning: UID mapping not found after registration")

    # Show current counters
    counters = uid_manager.get_current_counters()
    print(f"\n📊 Current UID Counters:")
    print(f"   obj_counter: {counters['obj_counter']}")
    print(f"   fbx_counter: {counters['fbx_counter']}")
    print(f"   img_counter: {counters['img_counter']}")
    print(f"   vid_counter: {counters['vid_counter']}")

if __name__ == "__main__":
    register_fbx_uid()