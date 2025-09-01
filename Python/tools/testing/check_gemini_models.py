#!/usr/bin/env python3
"""
Check available Gemini models.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_gemini_models():
    try:
        import google.generativeai as genai
        
        # Load environment
        from dotenv import load_dotenv
        dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        load_dotenv(dotenv_path)
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("❌ GOOGLE_API_KEY not found")
            return
            
        genai.configure(api_key=api_key)
        
        print("🔍 Available Gemini models:")
        print("-" * 50)
        
        # List available models
        models = genai.list_models()
        gemini_models = []
        
        for model in models:
            if 'gemini' in model.name.lower():
                # Extract just the model name part
                model_name = model.name.split('/')[-1]
                gemini_models.append(model_name)
                print(f"✅ {model_name}")
                
        print(f"\n📊 Found {len(gemini_models)} Gemini models")
        
        # Test a few specific model names that might exist
        test_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-2.0-flash-exp",
            "gemini-2.5-flash-exp",
            "gemini-pro"
        ]
        
        print(f"\n🧪 Testing specific model names:")
        for model_name in test_models:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"✅ {model_name} - Available")
            except Exception as e:
                print(f"❌ {model_name} - Not available: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_gemini_models()