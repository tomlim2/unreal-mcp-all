#!/usr/bin/env python3
"""
Test script to verify model switching in NLP processing.
"""

import sys
import os
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_switching():
    """Test NLP processing with different models."""
    
    try:
        print("=" * 60)
        print("Testing Model Switching in NLP Processing")
        print("=" * 60)
        
        # Import NLP processing
        from tools.ai.nlp import process_natural_language
        from tools.ai.model_providers import get_available_models
        
        print("✅ NLP imports successful")
        
        # Test input
        test_input = "Set the time to sunrise (6 AM)"
        test_context = "User is working with Unreal Engine project"
        
        available_models = get_available_models()
        print(f"📋 Available models for testing: {available_models}")
        
        # Test with each available model
        for model_name in available_models:
            print(f"\n🔍 Testing with {model_name.upper()} model:")
            print("-" * 40)
            
            try:
                # Process with specific model
                result = process_natural_language(
                    user_input=test_input,
                    context=test_context,
                    session_id=None,  # No session for testing
                    model=model_name
                )
                
                # Check result
                if result.get('error'):
                    print(f"  ❌ Error: {result['error']}")
                else:
                    print(f"  ✅ Success: {result.get('explanation', 'No explanation')}")
                    print(f"  📝 Commands: {len(result.get('commands', []))} generated")
                    if result.get('commands'):
                        for i, cmd in enumerate(result['commands'][:2]):  # Show first 2
                            print(f"    {i+1}. {cmd.get('type', 'unknown')}")
                
            except Exception as e:
                print(f"  ❌ Model {model_name} failed: {e}")
        
        # Test default model (no model specified)
        print(f"\n🎯 Testing with DEFAULT model:")
        print("-" * 40)
        
        try:
            result = process_natural_language(
                user_input=test_input,
                context=test_context,
                session_id=None,
                model=None  # Use default
            )
            
            if result.get('error'):
                print(f"  ❌ Error: {result['error']}")
            else:
                print(f"  ✅ Success: {result.get('explanation', 'No explanation')}")
                print(f"  📝 Commands: {len(result.get('commands', []))} generated")
        
        except Exception as e:
            print(f"  ❌ Default model failed: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Model switching test completed!")
        print("⚠️  Note: Command execution skipped (no Unreal connection)")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model_switching()
    if not success:
        sys.exit(1)