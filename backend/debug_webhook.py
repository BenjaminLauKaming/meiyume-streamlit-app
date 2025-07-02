#!/usr/bin/env python3
"""
Debug script to test what data is sent to n8n webhook
"""

import requests
import os
import json
import sys

def debug_webhook_data():
    """Send test data to webhook and see what n8n receives"""
    
    # n8n webhook URL
    webhook_url = "http://localhost:5678/webhook/fe198a5f-79e0-4dc7-82d1-ce7fb65e9c5e"
    
    # Check if test file exists
    test_file_path = "../test_upload.txt"
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        print("Creating a simple test file...")
        with open(test_file_path, 'w') as f:
            f.write("This is a test file for debugging webhook data\n")
    
    print(f"🔄 Testing webhook data structure")
    print(f"📄 Using test file: {test_file_path}")
    
    try:
        # Prepare the file for upload
        with open(test_file_path, 'rb') as file:
            files = {
                'pdfFile': ('test_upload.txt', file, 'text/plain')
            }
            
            # Additional data to send with the file
            data = {
                'upload_id': 'debug-test-123',
                'original_filename': 'test_upload.txt',
                'project_name': 'Debug Test Project',
                'drawing_number': 'DWG-001',
                'revision': 'Rev A',
                'user_id': 'debug-user',
                'webhook_secret': 'debug-secret'
            }
            
            print("📤 Sending debug request to n8n webhook...")
            print(f"📋 File data: {files}")
            print(f"📋 Form data: {json.dumps(data, indent=2)}")
            print("-" * 50)
            
            # Send the request
            response = requests.post(
                webhook_url,
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            print(f"📄 Response Content: {response.text}")
            
            if response.status_code == 200:
                print("✅ Webhook received the request successfully!")
                return True
            else:
                print(f"❌ Webhook returned error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error sending to webhook: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 n8n Webhook Data Debug Script")
    print("=" * 50)
    
    success = debug_webhook_data()
    
    print("=" * 50)
    if success:
        print("✅ Debug test completed!")
        print("💡 Check your n8n execution log to see what data structure was received")
        print("💡 In n8n, go to Executions tab to see the webhook data")
    else:
        print("❌ Debug test failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 