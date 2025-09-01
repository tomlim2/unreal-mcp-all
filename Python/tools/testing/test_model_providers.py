#!/usr/bin/env python3
"""
Test script to verify model provider functionality.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_providers():
    """Test model provider initialization and availability."""
    
    try:
        print("=" * 60)
        print("Testing Model Provider System")
        print("=" * 60)
        
        # Import model providers
        from tools.ai.model_providers import (
            get_provider_factory, 
            get_available_models, 
            get_default_model,
            get_model_provider
        )
        
        print("✅ Model provider imports successful")
        
        # Test factory initialization
        factory = get_provider_factory()
        print(f"✅ Provider factory initialized: {type(factory).__name__}")
        
        # Check available models
        available_models = get_available_models()
        print(f"📋 Available models: {available_models}")
        
        # Check default model
        default_model = get_default_model()
        print(f"🎯 Default model: {default_model}")
        
        # Test model info
        model_info = factory.get_model_info()
        print(f"📊 Model information:")
        for model_name, info in model_info.items():
            available = "✅" if info['available'] == 'True' else "❌"
            is_default = " (DEFAULT)" if info['is_default'] == 'True' else ""
            print(f"  {available} {info['display_name']}{is_default}")
        
        # Test getting providers
        print(f"\n🔍 Testing provider access:")
        for model_name in ['gemini', 'claude']:
            provider = get_model_provider(model_name)
            if provider:
                print(f"  ✅ {model_name}: {provider.get_model_name()}")
            else:
                print(f"  ❌ {model_name}: Not available")
        
        print("\n" + "=" * 60)
        print("✅ Model provider system working correctly!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model_providers()
    if not success:
        sys.exit(1)