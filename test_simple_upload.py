#!/usr/bin/env python3
"""
Simple test script to demonstrate the CAD upload and result retrieval flow
"""

import requests
import json
import time

def test_simple_upload():
    """Test the complete upload and result retrieval flow"""
    
    print("🚀 Testing Simple CAD Upload Flow")
    print("=" * 50)
    
    # Step 1: Upload a file
    print("📤 Step 1: Uploading file...")
    
    with open("README.md", "rb") as f:
        files = {"file": ("test_cad.pdf", f.read(), "application/pdf")}
        
        response = requests.post(
            "http://localhost:8000/api/upload/",
            files=files,
            timeout=30
        )
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return
    
    upload_data = response.json()
    task_id = upload_data.get("id")
    
    print(f"✅ Upload successful! Task ID: {task_id}")
    print(f"📁 Filename: {upload_data.get('filename')}")
    print(f"📊 Status: {upload_data.get('status')}")
    
    # Step 2: Poll for results
    print("\n⏳ Step 2: Waiting for results...")
    
    max_attempts = 10
    for attempt in range(max_attempts):
        time.sleep(2)
        
        try:
            result_response = requests.get(
                f"http://localhost:8000/api/upload/{task_id}/",
                timeout=10
            )
            
            if result_response.status_code == 200:
                result_data = result_response.json()
                status = result_data.get("status")
                
                print(f"📊 Attempt {attempt + 1}: Status = {status}")
                
                if status == "completed":
                    print("✅ Analysis completed!")
                    
                    # Display results summary
                    results = result_data.get("results", [])
                    print(f"\n📈 Results Summary:")
                    print(f"   • Total result types: {len(results)}")
                    
                    for result in results:
                        result_type = result.get("result_type")
                        raw_data = result.get("raw_data", {})
                        
                        if result_type == "dimensions":
                            parts = raw_data.get("parts", [])
                            total_dimensions = sum(len(part.get("dimensions", [])) for part in parts)
                            print(f"   • Dimensions: {len(parts)} parts, {total_dimensions} dimensions")
                        
                        elif result_type == "matching":
                            matches = raw_data.get("matches", [])
                            print(f"   • Matching: {len(matches)} component matches")
                    
                    # Show sample data
                    print(f"\n📋 Sample Data:")
                    for result in results:
                        result_type = result.get("result_type")
                        raw_data = result.get("raw_data", {})
                        
                        if result_type == "dimensions" and raw_data.get("parts"):
                            first_part = raw_data["parts"][0]
                            print(f"   • First part: {first_part['name']} ({len(first_part['dimensions'])} dimensions)")
                            if first_part['dimensions']:
                                first_dim = first_part['dimensions'][0]
                                print(f"     - {first_dim['name']}: {first_dim['value']} {first_dim['unit']} ±{first_dim['tolerance']}")
                        
                        elif result_type == "matching" and raw_data.get("matches"):
                            first_match = raw_data["matches"][0]
                            print(f"   • First match: {first_match['Component']} → {first_match['Matched_Part']} ({first_match['Confidence']} confidence)")
                    
                    return result_data
                    
                elif status == "failed":
                    print("❌ Analysis failed")
                    return None
                    
        except requests.RequestException as e:
            print(f"⚠️  Request error: {e}")
            continue
    
    print("❌ Timeout waiting for results")
    return None

if __name__ == "__main__":
    result = test_simple_upload()
    
    if result:
        print(f"\n🎉 Test completed successfully!")
        print(f"📊 Access the full results at: http://localhost:8501")
    else:
        print(f"\n❌ Test failed!")



