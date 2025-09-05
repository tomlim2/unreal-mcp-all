#!/usr/bin/env python3
"""
Test screenshot with immediate and continuous polling
"""

import requests
import json
import time
import threading

def test_screenshot_with_continuous_polling():
    """Create screenshot and immediately start polling"""
    print("=== Screenshot Timing Test ===")
    
    # Step 1: Create screenshot job
    url = "http://localhost:8080"
    data = {
        "prompt": "take a screenshot",
        "context": "User is working with Unreal Engine project",
        "session_id": "timing_test_session"
    }
    
    print(f"\n1. Creating screenshot job...")
    
    response = requests.post(url, json=data)
    if response.status_code != 200:
        print(f"Failed to create job: {response.status_code}")
        return
    
    result = response.json()
    
    # Extract job_id
    job_id = None
    if result.get('executionResults'):
        for exec_result in result['executionResults']:
            if exec_result.get('success') and exec_result.get('result', {}).get('result', {}).get('job_id'):
                job_id = exec_result['result']['result']['job_id']
                break
    
    if not job_id:
        print("No job_id found in response")
        return
    
    print(f"Job created: {job_id}")
    
    # Step 2: Immediately start continuous polling
    print(f"\n2. Starting continuous polling...")
    
    def poll_job_status():
        for attempt in range(20):  # Poll for 20 attempts
            try:
                response = requests.get(f"http://localhost:8080/api/job?job_id={job_id}")
                timestamp = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        status = data.get('status', 'unknown')
                        progress = data.get('progress', 0)
                        print(f"   Poll {attempt+1}: {status} ({progress}%) at {timestamp:.3f}")
                        
                        if status in ['completed', 'failed']:
                            if status == 'completed':
                                result = data.get('result')
                                if result:
                                    print(f"   ✅ Screenshot: {result.get('filename')}")
                                    print(f"   📄 File path: {result.get('filepath')}")
                                    print(f"   🔗 Download URL: {result.get('download_url')}")
                                else:
                                    print(f"   ✅ Completed but no result data")
                            else:
                                error = data.get('error', 'Unknown error')
                                print(f"   ❌ Failed: {error}")
                            break
                    else:
                        print(f"   Poll {attempt+1}: Error - {data.get('error', 'Unknown')}")
                else:
                    print(f"   Poll {attempt+1}: HTTP {response.status_code}")
                    if response.status_code == 200:
                        print(f"      Response: {response.text[:200]}")
                
                time.sleep(0.5)  # Poll every 500ms
                
            except Exception as e:
                print(f"   Poll {attempt+1}: Exception - {e}")
                time.sleep(0.5)
        
        print(f"   Polling completed after 20 attempts")
    
    # Start polling in a separate thread
    poll_thread = threading.Thread(target=poll_job_status)
    poll_thread.daemon = True
    poll_thread.start()
    
    # Wait for polling to complete
    poll_thread.join()
    
    print(f"\n3. Final check of active jobs...")
    response = requests.get("http://localhost:8080/debug-jobs")
    if response.status_code == 200:
        data = response.json()
        print(f"   Active jobs: {data['total_jobs']}")
        for job in data.get('jobs', []):
            print(f"     - {job['job_id']}: {job['status']} ({job['progress']}%)")
    
if __name__ == "__main__":
    test_screenshot_with_continuous_polling()