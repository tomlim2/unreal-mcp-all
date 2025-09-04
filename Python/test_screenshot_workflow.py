#!/usr/bin/env python3
"""
Test script for timestamp-based screenshot workflow.
This verifies the complete job management system works end-to-end.
"""

import time
import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScreenshotWorkflowTest:
    """Test the complete screenshot workflow with timestamp-based detection."""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        
    def test_complete_workflow(self):
        """Test the complete screenshot job workflow."""
        logger.info("🚀 Starting screenshot workflow test...")
        
        try:
            # Step 1: Create screenshot job
            logger.info("📸 Step 1: Creating screenshot job...")
            job_response = self.create_screenshot_job()
            
            if not job_response or not job_response.get('success'):
                logger.error("❌ Failed to create screenshot job")
                return False
                
            job_id = job_response.get('job_id')
            logger.info(f"✅ Screenshot job created: {job_id}")
            
            # Step 2: Monitor job progress
            logger.info("⏳ Step 2: Monitoring job progress...")
            final_status = self.monitor_job_progress(job_id)
            
            if final_status == 'completed':
                logger.info("✅ Screenshot job completed successfully!")
                
                # Step 3: Get final result
                result = self.get_job_result(job_id)
                if result:
                    logger.info(f"📄 File info: {result.get('filename', 'Unknown')} "
                              f"({result.get('file_size', 0)} bytes)")
                    logger.info(f"🔗 Download URL: {result.get('download_url', 'None')}")
                
                # Step 4: Test file download
                self.test_file_download(job_id)
                
                return True
                
            elif final_status == 'failed':
                logger.error("❌ Screenshot job failed")
                return False
            else:
                logger.warning(f"⚠️ Unexpected final status: {final_status}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test workflow failed with exception: {e}")
            return False
    
    def create_screenshot_job(self) -> dict:
        """Create a new screenshot job."""
        try:
            url = f"{self.base_url}/api/screenshot/start"
            data = {
                'parameters': {
                    'resolution_multiplier': 2,
                    'filename_override': None
                },
                'session_id': 'test-session-12345'
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return None
    
    def monitor_job_progress(self, job_id: str, timeout_seconds=60) -> str:
        """Monitor job progress until completion or failure."""
        start_time = time.time()
        last_status = None
        
        while (time.time() - start_time) < timeout_seconds:
            try:
                status_info = self.get_job_status(job_id)
                
                if not status_info:
                    logger.warning("Could not get job status")
                    time.sleep(2)
                    continue
                
                current_status = status_info.get('status', 'unknown')
                
                if current_status != last_status:
                    logger.info(f"📊 Status: {current_status}")
                    last_status = current_status
                
                # Show progress if available
                progress = status_info.get('progress', 0)
                if progress and progress > 0:
                    logger.info(f"📈 Progress: {progress:.1f}%")
                
                # Check if job is complete
                if current_status in ['completed', 'failed', 'cancelled']:
                    return current_status
                
                time.sleep(1)  # Poll every second
                
            except Exception as e:
                logger.error(f"Error monitoring job: {e}")
                time.sleep(2)
        
        logger.error("⏰ Job monitoring timeout")
        return 'timeout'
    
    def get_job_status(self, job_id: str) -> dict:
        """Get current job status."""
        try:
            url = f"{self.base_url}/api/screenshot/status/{job_id}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Status check HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return None
    
    def get_job_result(self, job_id: str) -> dict:
        """Get job result details."""
        try:
            url = f"{self.base_url}/api/screenshot/result/{job_id}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Result check HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting job result: {e}")
            return None
    
    def test_file_download(self, job_id: str):
        """Test that the file can be downloaded."""
        try:
            url = f"{self.base_url}/api/screenshot/download/{job_id}"
            response = requests.head(url, timeout=5)  # Just check headers
            
            if response.status_code == 200:
                content_length = response.headers.get('content-length', 'unknown')
                content_type = response.headers.get('content-type', 'unknown')
                logger.info(f"📥 File downloadable: {content_length} bytes, type: {content_type}")
                return True
            else:
                logger.warning(f"Download check HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing download: {e}")
            return False
    
    def test_job_cancellation(self):
        """Test job cancellation functionality."""
        logger.info("🛑 Testing job cancellation...")
        
        try:
            # Create a job
            job_response = self.create_screenshot_job()
            if not job_response or not job_response.get('success'):
                logger.error("Failed to create job for cancellation test")
                return False
            
            job_id = job_response.get('job_id')
            logger.info(f"Created job for cancellation test: {job_id}")
            
            # Try to cancel it quickly
            time.sleep(0.5)  # Give it a moment to start
            
            url = f"{self.base_url}/api/screenshot/cancel/{job_id}"
            response = requests.post(url, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("✅ Job cancellation successful")
                    return True
                else:
                    logger.warning(f"Job cancellation returned success=false: {result}")
                    return False
            else:
                logger.error(f"Cancellation HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing cancellation: {e}")
            return False

def main():
    """Run the complete test suite."""
    print("🧪 Screenshot Workflow Test Suite")
    print("==================================")
    
    tester = ScreenshotWorkflowTest()
    
    # Test 1: Complete workflow
    print("\n🔄 Test 1: Complete Screenshot Workflow")
    success1 = tester.test_complete_workflow()
    
    # Test 2: Job cancellation
    print("\n🔄 Test 2: Job Cancellation")
    success2 = tester.test_job_cancellation()
    
    # Summary
    print("\n📊 Test Results:")
    print(f"  Complete Workflow: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"  Job Cancellation:  {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! The timestamp-based screenshot system is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    exit(main())