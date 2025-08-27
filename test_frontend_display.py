#!/usr/bin/env python3
"""
Test script to simulate webhook data and test frontend display
"""

import requests
import json
import base64

def test_frontend_display():
    """Test the complete flow from webhook to frontend display"""
    
    print("🧪 Testing Frontend Display Flow")
    print("=" * 50)
    
    # Webhook URL
    webhook_url = "https://daf20c2517fd.ngrok-free.app/api/cad/webhook/"
    
    # Use the current session_id
    session_id = "27b14aac-2d91-42c8-935a-b23071fd8184"
    task_id = "task_1755558770"
    
    # Create sample CAD analysis data
    sample_dimension_csv = """Component,Length_mm,Width_mm,Height_mm,Tolerance
Cap_Body,12.5,8.3,4.2,±0.1
Cap_Top,12.7,8.5,1.8,±0.05
Mounting_Hole,2.1,2.1,4.2,±0.02
Thread_Part,6.8,6.8,3.1,±0.1"""
    
    sample_matching_csv = """Component,Match_Score,Confidence,Status
Cap_Body,0.98,High,Matched
Cap_Top,0.95,High,Matched
Mounting_Hole,0.92,Medium,Matched
Thread_Part,0.89,Medium,Partial_Match"""
    
    # Encode as base64
    dimension_b64 = base64.b64encode(sample_dimension_csv.encode('utf-8')).decode('utf-8')
    matching_b64 = base64.b64encode(sample_matching_csv.encode('utf-8')).decode('utf-8')
    
    # Create the correct payload format
    payload = [
        {
            "dimension": dimension_b64,
            "matching": matching_b64,
            "session_id": session_id
        }
    ]
    
    print(f"📤 Step 1: Sending webhook data for session: {session_id}")
    
    # Send to webhook
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("   ✅ Webhook received data successfully!")
            
            # Step 2: Test polling endpoint
            print(f"\n📥 Step 2: Testing polling endpoint for task: {task_id}")
            polling_url = f"https://daf20c2517fd.ngrok-free.app/api/upload/{task_id}/"
            polling_response = requests.get(polling_url)
            
            if polling_response.status_code == 200:
                polling_data = polling_response.json()
                print(f"   - Status: {polling_data.get('status')}")
                print(f"   - Session ID: {polling_data.get('session_id')}")
                
                if polling_data.get('status') == 'completed':
                    print("   ✅ Polling returns completed!")
                    
                    # Step 3: Check the results structure
                    results = polling_data.get('results', [])
                    print(f"   - Results type: {type(results)}")
                    print(f"   - Results length: {len(results) if isinstance(results, list) else 'N/A'}")
                    
                    if isinstance(results, list) and len(results) > 0:
                        result = results[0]
                        print(f"   - First result keys: {list(result.keys())}")
                        print(f"   - Session ID in result: {result.get('session_id')}")
                        
                        # Check if session_id matches
                        if result.get('session_id') == session_id:
                            print("   ✅ Session ID matches!")
                            
                            # Check if dimension and matching data are present
                            if 'dimension' in result and 'matching' in result:
                                print("   ✅ Dimension and matching data present!")
                                
                                # Test decoding
                                try:
                                    dimension_decoded = base64.b64decode(result['dimension']).decode('utf-8')
                                    matching_decoded = base64.b64decode(result['matching']).decode('utf-8')
                                    print("   ✅ Base64 decoding successful!")
                                    print(f"   - Dimension data length: {len(dimension_decoded)} chars")
                                    print(f"   - Matching data length: {len(matching_decoded)} chars")
                                    
                                    print("\n🎉 Frontend should display results successfully!")
                                    
                                except Exception as e:
                                    print(f"   ❌ Base64 decoding failed: {e}")
                            else:
                                print("   ❌ Missing dimension or matching data")
                        else:
                            print("   ❌ Session ID doesn't match")
                    else:
                        print("   ❌ No results array found")
                else:
                    print(f"   ⏳ Still processing: {polling_data.get('status')}")
            else:
                print(f"   ❌ Polling failed: {polling_response.status_code}")
                
        else:
            print(f"   ❌ Webhook failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    test_frontend_display()
