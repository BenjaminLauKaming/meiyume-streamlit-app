#!/usr/bin/env python3
"""
Test Docker container communication
"""

import requests
import os

def test_docker_connection():
    """Test connection between Docker containers"""
    
    print("🔧 Testing Docker Container Communication")
    print("=" * 50)
    
    # Test different URLs
    urls_to_test = [
        ("Django via localhost", "http://localhost:8000/api/health/"),
        ("Django via docker service", "http://django:8000/api/health/"),
        ("Django via container IP", "http://172.17.0.1:8000/api/health/"),
    ]
    
    for name, url in urls_to_test:
        print(f"\n📡 Testing {name}: {url}")
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                print(f"📄 Response: {response.text[:100]}...")
            else:
                print(f"📄 Response: {response.text}")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected Error: {str(e)}")
    
    # Test CAD upload endpoint
    print(f"\n📤 Testing CAD upload endpoint...")
    try:
        # Create a simple test file
        test_content = b"test file content"
        
        files = {"file": ("test.txt", test_content, "text/plain")}
        data = {"project_name": "Test", "drawing_number": "TEST-001", "revision": "A"}
        
        response = requests.post(
            "http://django:8000/api/cad/uploads/",
            files=files,
            data=data,
            timeout=10
        )
        
        print(f"📡 Upload Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Upload successful!")
            result = response.json()
            print(f"📄 Response: {result}")
        else:
            print(f"❌ Upload failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Upload Error: {str(e)}")

if __name__ == "__main__":
    test_docker_connection()
