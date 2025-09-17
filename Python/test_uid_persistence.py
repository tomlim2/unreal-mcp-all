#!/usr/bin/env python3
"""
Test script to verify UID persistence across server restarts.

This script simulates server restart scenarios and verifies that
UIDs continue sequentially without collisions.
"""

import os
import sys
from pathlib import Path

# Add the Python directory to path
python_dir = Path(__file__).parent
sys.path.insert(0, str(python_dir))

from tools.ai.uid_manager import get_uid_manager, generate_image_uid

def test_uid_persistence():
    """Test UID persistence across multiple instances."""
    print("🧪 Testing UID Persistence System")
    print("=" * 50)
    
    # Clean up any existing state for clean test
    uid_state_file = python_dir / "uid_state.json"
    if uid_state_file.exists():
        print(f"🗑️  Removing existing state file: {uid_state_file}")
        uid_state_file.unlink()
    
    # Test 1: Initial UID generation
    print("\n📝 Test 1: Initial UID generation")
    uid1 = generate_image_uid()
    uid2 = generate_image_uid()
    uid3 = generate_image_uid()
    
    print(f"Generated UIDs: {uid1}, {uid2}, {uid3}")
    assert uid1 == "img_001", f"Expected img_001, got {uid1}"
    assert uid2 == "img_002", f"Expected img_002, got {uid2}"
    assert uid3 == "img_003", f"Expected img_003, got {uid3}"
    print("✅ Initial generation: PASSED")
    
    # Check that state file was created
    assert uid_state_file.exists(), "State file should exist after UID generation"
    print(f"✅ State file created: {uid_state_file}")
    
    # Test 2: Simulate server restart (create new manager instance)
    print("\n🔄 Test 2: Simulating server restart")
    
    # Force creation of new manager instance by clearing global state
    import tools.ai.uid_manager as uid_module
    uid_module._global_uid_manager = None
    
    # Generate new UIDs after "restart"
    uid4 = generate_image_uid()
    uid5 = generate_image_uid()
    
    print(f"UIDs after restart: {uid4}, {uid5}")
    assert uid4 == "img_004", f"Expected img_004, got {uid4}"
    assert uid5 == "img_005", f"Expected img_005, got {uid5}"
    print("✅ Restart continuity: PASSED")
    
    # Test 3: Verify state file content
    print("\n📋 Test 3: State file verification")
    import json
    
    with open(uid_state_file, 'r') as f:
        state_data = json.load(f)
    
    print(f"State file content: {state_data}")
    assert state_data['current_counter'] == 5, f"Expected counter 5, got {state_data['current_counter']}"
    assert 'last_updated' in state_data, "State should include last_updated timestamp"
    print("✅ State file verification: PASSED")
    
    # Test 4: Multiple restarts
    print("\n🔄🔄 Test 4: Multiple restart cycles")
    
    for restart_num in range(1, 4):
        # Clear global state to simulate restart
        uid_module._global_uid_manager = None
        
        # Generate UID after restart
        uid = generate_image_uid()
        expected_uid = f"img_{5 + restart_num:03d}"
        
        print(f"Restart #{restart_num}: Generated {uid}, expected {expected_uid}")
        assert uid == expected_uid, f"Restart #{restart_num}: Expected {expected_uid}, got {uid}"
    
    print("✅ Multiple restarts: PASSED")
    
    # Test 5: Final counter check
    print("\n🏁 Test 5: Final state verification")
    manager = get_uid_manager()
    final_counter = manager.get_current_counter()
    
    print(f"Final counter value: {final_counter}")
    assert final_counter == 8, f"Expected final counter 8, got {final_counter}"
    print("✅ Final state: PASSED")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ UID persistence system working correctly")
    print("✅ No UID collisions across restarts")
    print("✅ Sequential numbering maintained")
    print("✅ State file properly maintained")
    
    # Show final state file for reference
    print(f"\n📁 Final state file ({uid_state_file}):")
    with open(uid_state_file, 'r') as f:
        state_content = f.read()
    print(state_content)

if __name__ == "__main__":
    try:
        test_uid_persistence()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)