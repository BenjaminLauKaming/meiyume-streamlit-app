#!/usr/bin/env python3
"""
Simple test to verify webhook connection and show correct format
"""

import requests
import json
import base64

# Your webhook URL
WEBHOOK_URL = "https://daf20c2517fd.ngrok-free.app/api/cad/webhook/"

def test_webhook_connection():
    """Test if the webhook is accessible and working"""
    
    print("🧪 Testing webhook connection")
    print("=" * 40)
    print(f"Webhook URL: {WEBHOOK_URL}")
    
    # Test 1: Check if webhook is accessible
    print("\n1. Testing webhook accessibility...")
    try:
        response = requests.get(WEBHOOK_URL, timeout=10)
        print(f"GET response: {response.status_code}")
        if response.status_code in [200, 405]:  # 405 = Method Not Allowed (expected)
            print("✅ Webhook endpoint is accessible!")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Webhook not accessible: {e}")
        return False
    
    # Test 2: Send test data in correct format
    print("\n2. Sending test data in correct format...")
    
    # Create sample CSV data
    dimension_csv = """part_name,feature,value,tolerance,unit,critical
Part A,Length,25.5,±0.1,mm,True
Part A,Width,15.2,±0.05,mm,False"""
    
    matching_csv = """part_a,feature_a,part_b,feature_b,dimension_type,difference_mm,status
Part A,Length,Part B,Length,Length,-4.5,Compatible"""
    
    # Encode as base64
    dimension_base64 = base64.b64encode(dimension_csv.encode('utf-8')).decode('utf-8')
    matching_base64 = base64.b64encode(matching_csv.encode('utf-8')).decode('utf-8')
    
    # Create payload in correct format
    webhook_payload = [
        {
            "matching": matching_base64,
            "dimension": dimension_base64,
            "session_id": "test-session-123"
        }
    ]
    
    print(f"Payload format: Array with {len(webhook_payload)} items")
    print(f"Session ID: {webhook_payload[0]['session_id']}")
    print(f"Dimension data length: {len(webhook_payload[0]['dimension'])} chars")
    print(f"Matching data length: {len(webhook_payload[0]['matching'])} chars")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\nPOST response status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Webhook received data successfully!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Webhook failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending webhook: {e}")
        return False

if __name__ == "__main__":
    success = test_webhook_connection()
    
    if success:
        print("\n🎉 Webhook connection test passed!")
        print("\n📝 Your n8n workflow should send data to:")
        print(f"   {WEBHOOK_URL}")
        print("\n📝 In this format:")
        print("""
[
  {
    "matching": "base64_encoded_matching_csv",
    "dimension": "base64_encoded_dimension_csv", 
    "session_id": "your_session_id"
  }
]
        """)
    else:
        print("\n❌ Webhook connection test failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Check if your ngrok tunnel is running")
        print("2. Verify the webhook URL is correct")
        print("3. Make sure the Django server is running")
        print("4. Check firewall/network settings")
