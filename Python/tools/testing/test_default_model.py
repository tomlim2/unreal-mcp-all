#!/usr/bin/env python3
"""
Test that default model is now gemini-2.5-flash.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_default_model():
    try:
        from tools.ai.nlp import process_natural_language
        
        print("Testing DEFAULT model (should be gemini-2.5-flash)...")
        
        result = process_natural_language(
            user_input="Set the time to noon",
            context="Testing default model",
            session_id=None,
            llm_model=None  # Use default
        )
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Success: {result.get('explanation', 'No explanation')}")
            print(f"📝 Commands: {len(result.get('commands', []))} generated")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_default_model()