#!/usr/bin/env python3
"""
Quick test for gemini-2 model.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gemini2():
    try:
        from tools.ai.nlp import process_natural_language
        
        print("Testing gemini-2.5-flash model...")
        
        result = process_natural_language(
            user_input="Create a bright red light",
            context="Testing new model",
            session_id=None,
            llm_model="gemini-2"
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
    test_gemini2()