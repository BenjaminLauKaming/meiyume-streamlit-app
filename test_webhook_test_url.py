#!/usr/bin/env python3
"""
Test script to try the webhook-test URL
"""

import requests
import json
import base64
import uuid

def test_webhook_test_url():
    """Test the webhook-test URL"""
    
    print("🧪 Testing Webhook-Test URL")
    print("=" * 50)
    
    # Test webhook URL
    webhook_url = "https://meiyume.app.n8n.cloud/webhook-test/3f700683-6240-4e87-8fc3-dcbeb96ea69c"
    
    # Generate test data
    session_id = str(uuid.uuid4())
    test_filename = "test_drawing.pdf"
    
    # Create a dummy PDF content (just for testing)
    dummy_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
    
    # Prepare webhook payload with simplified format
    webhook_payload = {
        "data": base64.b64encode(dummy_pdf_content).decode('utf-8'),
        "session_id": session_id
    }
    
    print(f"📤 Sending test data to webhook-test:")
    print(f"   URL: {webhook_url}")
    print(f"   Session ID: {session_id}")
    print(f"   Filename: {test_filename}")
    print(f"   File size: {len(dummy_pdf_content)} bytes")
    print(f"   Payload keys: {list(webhook_payload.keys())}")
    print(f"   Payload structure:")
    print(f"     - data: base64_encoded_file_content")
    print(f"     - session_id: {session_id}")
    
    try:
        # Send webhook request
        response = requests.post(
            webhook_url,
            json=webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n📥 Webhook-Test Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ Webhook-test request successful!")
            print("\n🎯 n8n Workflow Should Receive:")
            print(f"   - data: base64 encoded PDF content")
            print(f"   - session_id: {session_id}")
            print("\n📝 In your n8n workflow, you can access:")
            print(f"   - File content: {{ $json.data }} (base64)")
            print(f"   - Session ID: {{ $json.session_id }}")
            print("\n🔧 Next Steps:")
            print("1. Decode the base64 data in n8n")
            print("2. Process the PDF file")
            print("3. Send results back to:")
            print("   https://daf20c2517fd.ngrok-free.app/api/cad/webhook/")
            print("4. Format the response as:")
            print("   [")
            print("     {")
            print('       "dimension": "base64_encoded_csv",')
            print('       "matching": "base64_encoded_csv",')
            print(f'       "session_id": "{session_id}"')
            print("     }")
            print("   ]")
        else:
            print("❌ Webhook-test request failed!")
            print("   Check your n8n workflow configuration")
            
    except Exception as e:
        print(f"❌ Error sending webhook-test: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if the webhook-test URL is correct")
        print("2. Verify your n8n workflow is active")
        print("3. Check network connectivity")

if __name__ == "__main__":
    test_webhook_test_url()
