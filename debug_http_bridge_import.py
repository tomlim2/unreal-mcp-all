#!/usr/bin/env python3
"""
Debug HTTP bridge import and job system initialization
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Python'))

def test_http_bridge_import():
    """Test importing HTTP bridge and see job system status"""
    print("=== HTTP Bridge Import Test ===")
    
    try:
        print("\n1. Importing HTTP bridge...")
        import http_bridge
        
        print("\n2. Getting job system...")
        job_manager, screenshot_worker = http_bridge.get_job_system()
        
        print(f"   job_manager: {job_manager is not None} (id: {id(job_manager) if job_manager else 'None'})")
        print(f"   screenshot_worker: {screenshot_worker is not None} (id: {id(screenshot_worker) if screenshot_worker else 'None'})")
        
        if job_manager:
            print(f"   job_manager type: {type(job_manager)}")
        
        if screenshot_worker:
            print(f"   screenshot_worker type: {type(screenshot_worker)}")
        else:
            print("   screenshot_worker is None - checking why...")
            
            # Check if global variables exist
            print(f"   http_bridge.job_manager: {hasattr(http_bridge, 'job_manager')}")
            print(f"   http_bridge.screenshot_worker: {hasattr(http_bridge, 'screenshot_worker')}")
            
            if hasattr(http_bridge, 'screenshot_worker'):
                print(f"   http_bridge.screenshot_worker value: {http_bridge.screenshot_worker}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_http_bridge_import()