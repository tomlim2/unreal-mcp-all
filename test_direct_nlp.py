#!/usr/bin/env python3
"""
Test NLP processing directly to see debug output
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Python'))

def test_direct_nlp():
    """Test NLP processing directly"""
    print("=== Direct NLP Test ===")
    
    # Import and test NLP processing
    try:
        from tools.ai.nlp import process_natural_language
        
        print("\n1. Testing direct NLP call with screenshot command...")
        
        user_input = "take a screenshot"
        context = "User is working with Unreal Engine project"
        session_id = "direct_test_session"
        
        result = process_natural_language(user_input, context, session_id)
        
        print(f"\n2. NLP Result:")
        print(f"   Type: {type(result)}")
        print(f"   Keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            execution_results = result.get('executionResults', [])
            print(f"   Execution Results Count: {len(execution_results)}")
            
            for i, exec_result in enumerate(execution_results):
                print(f"   Result {i}: {exec_result}")
                
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_direct_nlp()