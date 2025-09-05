#!/usr/bin/env python3
"""
Test the screenshot endpoint directly
"""

import sys
from pathlib import Path
import requests
import json

def test_screenshot_endpoint():
    """Test the screenshot endpoint"""
    
    job_id = "155e75cd-aaf2-4154-bce2-37f2399e65ac"
    
    # Test direct HTTP bridge endpoint
    print("Testing HTTP Bridge Endpoint:")
    print("=" * 50)
    try:
        response = requests.get(f"http://localhost:8080/api/screenshot/download/{job_id}")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
        else:
            print(f"Content type: {response.headers.get('content-type')}")
            print(f"Content length: {len(response.content)} bytes")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nTesting Next.js Proxy Endpoint:")
    print("=" * 50)
    try:
        response = requests.get(f"http://localhost:3000/api/screenshot/{job_id}")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response (raw): {response.text}")
        else:
            print(f"Content type: {response.headers.get('content-type')}")
            print(f"Content length: {len(response.content)} bytes")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_screenshot_endpoint()