#!/usr/bin/env python3
"""
Debug script to check if UID information is properly included in system prompts.
"""

import os
import sys
from pathlib import Path

# Add the tools directory to Python path
tools_dir = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_dir))

def test_uid_in_system_prompt():
    """Debug UID inclusion in system prompts."""
    print("=" * 60)
    print("UID IN SYSTEM PROMPT DEBUG")
    print("=" * 60)

    try:
        from ai.nlp import build_system_prompt_with_session
        from ai.session_management import SessionContext
        from datetime import datetime
        print("✅ Modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import modules: {e}")
        return False

    # Create session with conversation history
    session = SessionContext(
        session_id="debug-session",
        session_name="Debug Session",
        llm_model="gemini-2",
        created_at=datetime.now(),
        last_accessed=datetime.now()
    )

    # Add conversation with UID
    ai_response = {
        "explanation": "Screenshot taken successfully",
        "commands": [{"type": "take_screenshot"}],
        "executionResults": [
            {
                "command": "take_screenshot",
                "success": True,
                "result": {
                    "uids": {"image": "img_999"},
                    "image": {"url": "/screenshots/TestImage.png"},
                    "filename": "TestImage.png"
                }
            }
        ]
    }

    session.add_interaction("Take a test screenshot", ai_response)

    print(f"\n🔍 Testing session methods:")

    # Test latest image UID
    latest_uid = session.get_latest_image_uid()
    print(f"   Latest UID: {latest_uid}")

    # Test latest image path
    latest_path = session.get_latest_image_path()
    print(f"   Latest path: {latest_path}")

    # Test conversation summary
    conversation_summary = session.get_conversation_summary()
    print(f"   Conversation summary:")
    print(f"      {conversation_summary}")

    print(f"\n🔍 Building system prompt:")
    context = "User wants to test the system"
    system_prompt = build_system_prompt_with_session(context, session)

    # Check if UID is in prompt
    print(f"\n   📋 UID presence check:")
    if latest_uid and latest_uid in system_prompt:
        print(f"   ✅ Latest UID {latest_uid} found in system prompt")
    else:
        print(f"   ❌ Latest UID {latest_uid} NOT found in system prompt")

    if latest_path and latest_path in system_prompt:
        print(f"   ✅ Latest path {latest_path} found in system prompt")
    else:
        print(f"   ❌ Latest path {latest_path} NOT found in system prompt")

    # Show the relevant section
    print(f"\n   📋 Latest image section in system prompt:")
    lines = system_prompt.split('\n')
    found_latest_section = False

    for i, line in enumerate(lines):
        if "Latest image:" in line:
            print(f"      {line}")
            found_latest_section = True
            # Show next line for context
            if i + 1 < len(lines):
                print(f"      {lines[i + 1]}")
            break

    if not found_latest_section:
        print(f"      ❌ 'Latest image:' section not found in system prompt")

    # Show conversation history section
    print(f"\n   📋 Scene/History section in system prompt:")
    for i, line in enumerate(lines):
        if "Scene:" in line:
            print(f"      {line}")
            break
        elif "conversation" in line.lower() or "history" in line.lower():
            print(f"      {line}")

    return True

if __name__ == "__main__":
    test_uid_in_system_prompt()