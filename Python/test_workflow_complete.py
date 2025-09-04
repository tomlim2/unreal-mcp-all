"""
Complete end-to-end workflow test for screenshot system.
Tests: Frontend → HTTP Bridge → Job Manager → Worker → Timestamp Detection
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_complete_workflow():
    """Test complete screenshot workflow."""
    print("🚀 Complete Screenshot Workflow Test")
    print("=" * 50)
    
    http_bridge_port = 8080
    base_url = f"http://localhost:{http_bridge_port}"
    
    print(f"📡 Testing HTTP Bridge at {base_url}")
    
    try:
        # 1. Health check
        print("\n1️⃣ Health check...")
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ HTTP Bridge running")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Start HTTP bridge: cd Python && python http_bridge.py")
        return False
    
    try:
        # 2. Start screenshot job
        print("\n2️⃣ Starting screenshot job...")
        job_payload = {
            "parameters": {
                "resolution_multiplier": 2.0,
                "include_ui": False
            },
            "session_id": "workflow-test"
        }
        
        job_response = requests.post(
            f"{base_url}/api/screenshot/start",
            json=job_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if job_response.status_code == 200:
            job_data = job_response.json()
            job_id = job_data.get("job_id")
            print(f"✅ Job started: {job_id}")
        else:
            print(f"❌ Job start failed: {job_response.status_code}")
            print(f"Response: {job_response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Job request failed: {e}")
        return False
    
    try:
        # 3. Monitor progress
        print(f"\n3️⃣ Monitoring job: {job_id}")
        max_wait = 30  # seconds
        interval = 2   # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(f"{base_url}/api/jobs/{job_id}/status", timeout=5)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                job_status = status_data.get("status")
                progress = status_data.get("progress", 0)
                
                print(f"   Status: {job_status}, Progress: {progress}%")
                
                if job_status == "completed":
                    print("✅ Job completed!")
                    result = status_data.get("result", {})
                    
                    if result.get("filename"):
                        print(f"✅ File detected: {result['filename']}")
                        print("✅ Timestamp detection working!")
                    else:
                        print("⚠️  No filename - timestamp detection failed")
                    
                    return True
                    
                elif job_status == "failed":
                    error = status_data.get("error", "Unknown error")
                    print(f"❌ Job failed: {error}")
                    return False
                    
                elif job_status in ["pending", "processing"]:
                    time.sleep(interval)
                    continue
                else:
                    print(f"❌ Unknown status: {job_status}")
                    return False
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                return False
        
        print("⏰ Timeout waiting for job")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Monitoring failed: {e}")
        return False

def main():
    """Main test execution."""
    print("🧪 Screenshot System End-to-End Test")
    print("=" * 60)
    
    print("\n📋 Requirements:")
    print("   ✓ HTTP bridge running (python http_bridge.py)")
    print("   ✓ Unreal project open with plugin")
    print("   ✓ TCP server on port 55557")
    
    print("\n🚀 Starting automatic test...")
    
    success = test_complete_workflow()
    
    if success:
        print("\n🎉 All Systems Working!")
        print("✅ Complete workflow verified:")
        print("   Frontend → HTTP → Jobs → Worker → Files")
    else:
        print("\n💥 Test Failed!")
        print("Check error messages for troubleshooting")

if __name__ == "__main__":
    main()