#!/usr/bin/env python3
"""
Test script to verify frontend can access CAD analysis data
"""

import requests
import json
import time

def test_frontend_data_access():
    """Test if the frontend can access the CAD analysis data"""
    
    # Test the API endpoint that the frontend polls
    api_url = "http://localhost:8000/api/upload/task_1755558770/"
    
    print("Testing frontend data access...")
    print(f"API URL: {api_url}")
    
    try:
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint accessible")
            print(f"Status: {data.get('status')}")
            print(f"Session ID: {data.get('session_id')}")
            
            if data.get('status') == 'completed':
                results = data.get('results', [])
                print(f"✅ Found {len(results)} result(s)")
                
                for i, result in enumerate(results):
                    print(f"\n--- Result {i+1} ---")
                    print(f"Session ID: {result.get('session_id')}")
                    print(f"Filename: {result.get('filename')}")
                    print(f"Status: {result.get('status')}")
                    print(f"Has dimension data: {'dimension' in result}")
                    print(f"Has matching data: {'matching' in result}")
                    
                    if 'dimension' in result:
                        print("✅ Dimension data available")
                    if 'matching' in result:
                        print("✅ Matching data available")
                
                print("\n🎉 Frontend should now be able to display the data!")
                print("Open http://localhost:8501 in your browser and navigate to CAD Analysis")
                
            else:
                print(f"❌ Status is not 'completed': {data.get('status')}")
                
        else:
            print(f"❌ API endpoint error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django backend")
        print("Make sure Django is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_streamlit_access():
    """Test if Streamlit frontend is accessible"""
    
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit frontend is accessible at http://localhost:8501")
        else:
            print(f"⚠️ Streamlit frontend returned status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Streamlit frontend not accessible")
        print("Make sure Streamlit is running on localhost:8501")
    except Exception as e:
        print(f"❌ Error testing Streamlit: {e}")

if __name__ == "__main__":
    print("=== Frontend Data Access Test ===\n")
    
    test_frontend_data_access()
    print("\n" + "="*50 + "\n")
    test_streamlit_access()
    
    print("\n=== Test Complete ===")
    print("If all tests pass, the frontend should display the CAD analysis data.")
    print("Navigate to: http://localhost:8501 → CAD Analysis")
