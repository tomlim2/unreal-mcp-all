#!/usr/bin/env python3
"""
Debug script to test screenshot command flow
"""

import requests
import json
import time

def debug_screenshot_flow():
    """Test the screenshot command from start to finish"""
    
    print("=== Debug Screenshot Flow ===")
    
    # Step 1: Send screenshot request via NLP endpoint
    url = "http://localhost:8080"
    data = {
        "prompt": "take a screenshot",
        "context": "User is working with Unreal Engine project",
        "session_id": "debug_session_123"
    }
    
    print(f"\n1. Sending screenshot request to {url}")
    print(f"Request: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=15)
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse JSON:")
            print(json.dumps(result, indent=2))
            
            # Step 2: Extract job_id from response
            job_id = None
            if result.get('executionResults'):
                for exec_result in result['executionResults']:
                    if exec_result.get('success') and exec_result.get('result', {}).get('result', {}).get('job_id'):
                        job_id = exec_result['result']['result']['job_id']
                        print(f"\n2. ✅ Found job_id: {job_id}")
                        break
            
            if not job_id:
                print(f"\n2. ❌ No job_id found in response")
                return
            
            # Step 3: Poll job status
            print(f"\n3. Polling job status for {job_id}")
            for attempt in range(10):
                print(f"\n   Poll attempt {attempt + 1}/10...")
                
                status_response = requests.get(f"http://localhost:8080/api/job?job_id={job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Status: {json.dumps(status_data, indent=4)}")
                    
                    if status_data.get('success') and status_data.get('status') in ['completed', 'failed']:
                        print(f"   🎉 Job {status_data['status']}!")
                        return
                else:
                    print(f"   ❌ Status check failed: {status_response.status_code}")
                    print(f"   Response: {status_response.text}")
                
                time.sleep(2)
            
            print(f"\n❌ Job did not complete after 10 polling attempts")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_screenshot_flow()