#!/usr/bin/env python3
"""
Debug which job_manager instances are being used
"""

import requests
import json

def test_job_manager_instances():
    """Test if different job_manager instances are being used"""
    
    print("=== Debug Job Manager Instances ===")
    
    # Create a screenshot job to trigger the async handler
    print("\n1. Creating screenshot job to trigger debug output...")
    create_data = {
        "prompt": "take a screenshot",
        "context": "User is working with Unreal Engine project", 
        "session_id": "debug_manager_test"
    }
    
    response = requests.post("http://localhost:8080", json=create_data)
    if response.status_code == 200:
        result = response.json()
        print("Response received - check server logs for debug output")
        
        # Extract job_id
        job_id = None
        if result.get('executionResults'):
            for exec_result in result['executionResults']:
                if exec_result.get('success') and exec_result.get('result', {}).get('result', {}).get('job_id'):
                    job_id = exec_result['result']['result']['job_id']
                    break
        
        if job_id:
            print(f"Job ID extracted: {job_id}")
        else:
            print("No job_id found")
    else:
        print(f"Request failed: {response.status_code}")

if __name__ == "__main__":
    test_job_manager_instances()