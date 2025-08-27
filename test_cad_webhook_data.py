#!/usr/bin/env python3
"""
Test script to simulate n8n workflow sending CAD analysis results to the webhook
"""

import requests
import json
import base64
import csv
from io import StringIO

def create_test_cad_data():
    """Create sample CAD analysis data that n8n would send"""
    
    # Sample dimension data
    dimension_data = [
        {"Part Name": "Cap", "Feature": "Diameter", "Value": "25.4", "Tolerance": "±0.1", "Unit": "mm", "Critical": "True"},
        {"Part Name": "Cap", "Feature": "Height", "Value": "15.2", "Tolerance": "±0.05", "Unit": "mm", "Critical": "True"},
        {"Part Name": "Cap", "Feature": "Wall Thickness", "Value": "2.1", "Tolerance": "±0.2", "Unit": "mm", "Critical": "False"},
        {"Part Name": "Base", "Feature": "Diameter", "Value": "25.6", "Tolerance": "±0.1", "Unit": "mm", "Critical": "True"},
        {"Part Name": "Base", "Feature": "Height", "Value": "12.8", "Tolerance": "±0.05", "Unit": "mm", "Critical": "True"},
        {"Part Name": "Base", "Feature": "Thread Pitch", "Value": "1.5", "Tolerance": "±0.1", "Unit": "mm", "Critical": "True"}
    ]
    
    # Sample matching data
    matching_data = [
        {"Component": "Cap - Diameter", "Matched_Part": "Base - Diameter", "Confidence": "0.95", "Match_Type": "Diameter", "Status": "Compatible"},
        {"Component": "Cap - Height", "Matched_Part": "Base - Height", "Confidence": "0.92", "Match_Type": "Height", "Status": "Compatible"},
        {"Component": "Cap - Wall Thickness", "Matched_Part": "Base - Wall Thickness", "Confidence": "0.78", "Match_Type": "Thickness", "Status": "Marginal"}
    ]
    
    # Convert to CSV strings
    dimension_csv = StringIO()
    dimension_writer = csv.DictWriter(dimension_csv, fieldnames=dimension_data[0].keys())
    dimension_writer.writeheader()
    dimension_writer.writerows(dimension_data)
    dimension_csv_str = dimension_csv.getvalue()
    
    matching_csv = StringIO()
    matching_writer = csv.DictWriter(matching_csv, fieldnames=matching_data[0].keys())
    matching_writer.writeheader()
    matching_writer.writerows(matching_data)
    matching_csv_str = matching_csv.getvalue()
    
    # Encode as base64
    dimension_base64 = base64.b64encode(dimension_csv_str.encode('utf-8')).decode('utf-8')
    matching_base64 = base64.b64encode(matching_csv_str.encode('utf-8')).decode('utf-8')
    
    # Create the payload that n8n should send (exact format from n8n)
    webhook_payload = [
        {
            "dimension": dimension_base64,
            "matching": matching_base64,
            "session_id": "27b14aac-2d91-42c8-935a-b23071fd8184"  # Use the actual session_id from the task
        }
    ]
    
    return webhook_payload

def send_test_data():
    """Send test data to the webhook"""
    
    webhook_url = "http://localhost:8000/api/cad/webhook/"
    test_data = create_test_cad_data()
    
    print("Sending test CAD analysis data to webhook...")
    print(f"Webhook URL: {webhook_url}")
    print(f"Session ID: {test_data[0]['session_id']}")
    print(f"Data format: {list(test_data[0].keys())}")
    
    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Test data sent successfully!")
            print("Now check the frontend to see if the data appears.")
        else:
            print(f"❌ Failed to send test data: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error sending test data: {e}")

if __name__ == "__main__":
    send_test_data()
