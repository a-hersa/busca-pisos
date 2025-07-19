#!/usr/bin/env python3
"""
Simple API test script for the FastAPI backend
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_user_registration():
    """Test user registration"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"User registration: {response.status_code}")
    if response.status_code == 200:
        print(f"Registered user: {response.json()}")
        return True
    else:
        print(f"Registration failed: {response.text}")
        return False

def test_user_login():
    """Test user login and return token"""
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"User login: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Login successful: {data['user']['username']}")
        return data['access_token']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_protected_endpoint(token):
    """Test protected endpoint with token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Protected endpoint: {response.status_code}")
    if response.status_code == 200:
        print(f"User info: {response.json()}")
        return True
    else:
        print(f"Protected endpoint failed: {response.text}")
        return False

def test_job_creation(token):
    """Test job creation"""
    headers = {"Authorization": f"Bearer {token}"}
    
    job_data = {
        "job_name": "Test Propiedades Crawl",
        "spider_name": "propiedades",
        "start_urls": [
            "https://www.idealista.com/venta-viviendas/mataro-barcelona/con-precio-hasta_120000,de-dos-dormitorios/"
        ],
        "schedule_type": "manual",
        "job_config": {
            "max_pages": 2,
            "delay": 1
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/jobs/", json=job_data, headers=headers)
    print(f"Job creation: {response.status_code}")
    if response.status_code == 200:
        job = response.json()
        print(f"Created job: {job['job_name']} (ID: {job['job_id']})")
        return job['job_id']
    else:
        print(f"Job creation failed: {response.text}")
        return None

def test_job_list(token):
    """Test job listing"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/jobs/", headers=headers)
    print(f"Job listing: {response.status_code}")
    if response.status_code == 200:
        jobs = response.json()
        print(f"Found {len(jobs)} jobs")
        for job in jobs:
            print(f"  - {job['job_name']} ({job['status']})")
        return True
    else:
        print(f"Job listing failed: {response.text}")
        return False

def test_job_execution(token, job_id):
    """Test job execution"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{BASE_URL}/api/jobs/{job_id}/run", headers=headers)
    print(f"Job execution: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Job started: {result}")
        return result.get('task_id')
    else:
        print(f"Job execution failed: {response.text}")
        return None

def test_job_status(token, job_id):
    """Test job status checking"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/status", headers=headers)
    print(f"Job status: {response.status_code}")
    if response.status_code == 200:
        status = response.json()
        print(f"Job status: {json.dumps(status, indent=2, default=str)}")
        return True
    else:
        print(f"Job status failed: {response.text}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing FastAPI Backend\n")
    
    # Test basic health
    if not test_health():
        print("❌ Health check failed")
        return
    
    print("\n" + "="*50)
    print("Testing Authentication")
    print("="*50)
    
    # Test registration (might fail if user exists)
    test_user_registration()
    
    # Test login
    token = test_user_login()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Test protected endpoint
    if not test_protected_endpoint(token):
        print("❌ Token authentication failed")
        return
    
    print("\n" + "="*50)
    print("Testing Job Management")
    print("="*50)
    
    # Test job creation
    job_id = test_job_creation(token)
    if not job_id:
        print("❌ Cannot test jobs without creating one")
        return
    
    # Test job listing
    test_job_list(token)
    
    # Test job status
    test_job_status(token, job_id)
    
    print("\n" + "="*50)
    print("Testing Job Execution")
    print("="*50)
    
    # Note: This will only work if Redis and Celery are running
    task_id = test_job_execution(token, job_id)
    if task_id:
        print(f"✅ Job execution started with task ID: {task_id}")
        
        # Wait a bit and check status again
        print("Waiting 5 seconds to check job progress...")
        time.sleep(5)
        test_job_status(token, job_id)
    else:
        print("⚠️  Job execution failed (Redis/Celery might not be running)")
    
    print("\n🎉 API testing completed!")

if __name__ == "__main__":
    main()