#!/usr/bin/env python3
"""
Test screenshot command via HTTP bridge
"""

import requests
import json
import time

def test_screenshot_command():
    """Test screenshot command via HTTP bridge"""
    
    # Test the NLP endpoint that should handle "take a screenshot"
    url = "http://localhost:8080"
    
    data = {
        "prompt": "take a screenshot",
        "context": "User is working with Unreal Engine project",
        "session_id": "test_session_123"
    }
    
    print("Testing screenshot command via HTTP bridge...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\nResponse JSON:")
                print(json.dumps(result, indent=2))
                
                # Check if a job was created
                if 'job_id' in result:
                    job_id = result['job_id']
                    print(f"\n✅ Job created with ID: {job_id}")
                    
                    # Test job status endpoint
                    print("\nTesting job status...")
                    status_response = requests.get(f"http://localhost:8080/api/jobs/{job_id}/status")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"Job Status: {json.dumps(status_data, indent=2)}")
                    else:
                        print(f"Job status check failed: {status_response.status_code}")
                else:
                    print("\n❌ No job_id in response")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"Raw response: {response.text[:500]}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_screenshot_command()