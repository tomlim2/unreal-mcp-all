#!/usr/bin/env python3
"""
Debug job creation and trace what happens
"""

import requests
import json
import time

def debug_job_creation():
    """Create a job and immediately check if it exists"""
    
    print("=== Debug Job Creation Trace ===")
    
    # First check existing jobs
    print("\n1. Checking existing jobs before creating new one...")
    response = requests.get("http://localhost:8080/debug-jobs")
    if response.status_code == 200:
        data = response.json()
        print(f"   Existing jobs: {data['total_jobs']}")
        for job in data.get('jobs', []):
            print(f"     - {job['job_id']}: {job['status']} ({job['progress']}%)")
    else:
        print(f"   Failed to get jobs: {response.status_code}")
    
    # Create screenshot job
    print("\n2. Creating screenshot job...")
    create_data = {
        "prompt": "take a screenshot",
        "context": "User is working with Unreal Engine project",
        "session_id": "debug_session_456"
    }
    
    response = requests.post("http://localhost:8080", json=create_data)
    if response.status_code != 200:
        print(f"Failed to create job: {response.status_code}")
        return
    
    result = response.json()
    print(f"Response received")
    
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
    
    print(f"   Job created with ID: {job_id}")
    
    # Immediately check if job exists in job_manager
    print(f"\n3. Immediately checking if job exists in job_manager...")
    response = requests.get("http://localhost:8080/debug-jobs")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total jobs in manager: {data['total_jobs']}")
        
        job_found = False
        for job in data.get('jobs', []):
            print(f"     - {job['job_id']}: {job['status']} ({job['progress']}%)")
            if job['job_id'] == job_id:
                job_found = True
                print(f"   ✅ Our job found: {job['status']} at {job['progress']}%")
        
        if not job_found:
            print(f"   ❌ Our job {job_id} not found in job manager")
    else:
        print(f"   Failed to get jobs after creation: {response.status_code}")
    
    # Try to get job status directly
    print(f"\n4. Checking job status directly...")
    response = requests.get(f"http://localhost:8080/api/job?job_id={job_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Direct status check: {json.dumps(data, indent=4)}")
    else:
        print(f"   Direct status check failed: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    debug_job_creation()