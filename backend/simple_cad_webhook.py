"""
Simple CAD Webhook Handler

A standalone webhook endpoint for CAD analysis results from n8n workflow.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import os
import base64
import csv
from io import StringIO

logger = logging.getLogger(__name__)

def process_base64_data(data):
    """
    Process base64 encoded dimension and matching data from n8n
    Handles the format: [{ "matching": "...", "dimension": "..." }]
    """
    processed = {}
    
    try:
        # Handle the new array format: [{ "matching": "...", "dimension": "..." }]
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict):
                # Process dimension data
                if 'dimension' in first_item and isinstance(first_item['dimension'], str):
                    try:
                        decoded_bytes = base64.b64decode(first_item['dimension'])
                        decoded_string = decoded_bytes.decode('utf-8')
                        # Try to parse as JSON
                        try:
                            dimension_json = json.loads(decoded_string)
                            processed['dimension_json'] = dimension_json
                            logger.info(f"Successfully decoded dimension JSON data")
                        except json.JSONDecodeError:
                            # Fallback to CSV if not JSON
                            processed['dimension_csv'] = decoded_string
                            logger.info(f"Successfully decoded dimension CSV data: {len(decoded_string)} characters")
                    except Exception as e:
                        logger.error(f"Error decoding dimension data: {str(e)}")
                
                # Process matching data
                if 'matching' in first_item and isinstance(first_item['matching'], str):
                    try:
                        decoded_bytes = base64.b64decode(first_item['matching'])
                        decoded_string = decoded_bytes.decode('utf-8')
                        # Try to parse as JSON
                        try:
                            matching_json = json.loads(decoded_string)
                            processed['matching_json'] = matching_json
                            logger.info(f"Successfully decoded matching JSON data")
                        except json.JSONDecodeError:
                            # Fallback to CSV if not JSON
                            processed['matching_csv'] = decoded_string
                            logger.info(f"Successfully decoded matching CSV data: {len(decoded_string)} characters")
                    except Exception as e:
                        logger.error(f"Error decoding matching data: {str(e)}")
        
        # Handle direct fields (fallback for old format)
        elif 'dimension' in data and isinstance(data['dimension'], str):
            try:
                decoded_bytes = base64.b64decode(data['dimension'])
                decoded_string = decoded_bytes.decode('utf-8')
                # Try to parse as JSON
                try:
                    dimension_json = json.loads(decoded_string)
                    processed['dimension_json'] = dimension_json
                    logger.info(f"Successfully decoded direct dimension JSON data")
                except json.JSONDecodeError:
                    processed['dimension_csv'] = decoded_string
                    logger.info(f"Successfully decoded direct dimension data: {len(decoded_string)} characters")
            except Exception as e:
                logger.error(f"Error decoding direct dimension data: {str(e)}")
        
        if 'matching' in data and isinstance(data['matching'], str):
            try:
                decoded_bytes = base64.b64decode(data['matching'])
                decoded_string = decoded_bytes.decode('utf-8')
                # Try to parse as JSON
                try:
                    matching_json = json.loads(decoded_string)
                    processed['matching_json'] = matching_json
                    logger.info(f"Successfully decoded direct matching JSON data")
                except json.JSONDecodeError:
                    processed['matching_csv'] = decoded_string
                    logger.info(f"Successfully decoded direct matching data: {len(decoded_string)} characters")
            except Exception as e:
                logger.error(f"Error decoding direct matching data: {str(e)}")
        
        logger.info(f"Processed base64 data: {list(processed.keys())}")
        return processed
        
    except Exception as e:
        logger.error(f"Error in process_base64_data: {str(e)}")
        return {}

def convert_to_csv(data, data_type):
    """Convert decoded data to CSV format"""
    try:
        # Try to parse as JSON first
        if data.strip().startswith('{') or data.strip().startswith('['):
            json_data = json.loads(data)
            
            # Convert JSON to CSV
            output = StringIO()
            
            if isinstance(json_data, list) and len(json_data) > 0:
                # List of dictionaries
                if isinstance(json_data[0], dict):
                    fieldnames = json_data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(json_data)
                else:
                    # List of simple values
                    writer = csv.writer(output)
                    writer.writerow([data_type.title()])
                    for item in json_data:
                        writer.writerow([item])
            
            elif isinstance(json_data, dict):
                # Single dictionary
                writer = csv.DictWriter(output, fieldnames=json_data.keys())
                writer.writeheader()
                writer.writerow(json_data)
            
            return output.getvalue()
            
        else:
            # If not JSON, treat as plain text and create simple CSV
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([f"{data_type.title()}_Data"])
            
            # Split by lines and create rows
            lines = data.strip().split('\n')
            for line in lines:
                if line.strip():
                    writer.writerow([line.strip()])
            
            return output.getvalue()
            
    except Exception as e:
        logger.error(f"Error converting {data_type} to CSV: {str(e)}")
        # Return simple CSV with error
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([f"{data_type.title()}_Data"])
        writer.writerow([data])
        return output.getvalue()

@csrf_exempt
@require_http_methods(["POST"])
def simple_cad_webhook(request):
    """
    Simple webhook receiver for CAD analysis results from n8n
    
    This endpoint accepts webhook data and logs it without requiring database tables.
    """
    try:
        # Parse the webhook payload
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
        else:
            payload = dict(request.POST)
        
        logger.info(f"Received CAD webhook payload: {payload}")
        print(f"DEBUG: Received CAD webhook payload: {json.dumps(payload, indent=2)}")
        
        # Extract CAD analysis results - handle the new format
        cad_results = {}
        
        # Check if payload itself is the array format (new format with session_id)
        if isinstance(payload, list):
            cad_results = payload
            logger.info(f"Received array format payload with {len(payload)} items")
        # Check if data is in the "answer" field as JSON string
        elif 'answer' in payload:
            try:
                answer_data = json.loads(payload['answer'])
                cad_results = answer_data
                logger.info(f"Received answer field with JSON data")
            except (json.JSONDecodeError, TypeError):
                # If answer is not JSON, store as is
                cad_results = {"raw_analysis": payload['answer']}
                logger.info(f"Received answer field with raw data")
        else:
            # Direct payload
            cad_results = payload
            logger.info(f"Received direct payload format")
        
        # Process base64 data for matching and dimension
        processed_results = process_base64_data(cad_results)
        if isinstance(cad_results, dict):
            cad_results.update(processed_results)
        else:
            # If cad_results is a list, create a new dict with the processed results
            # Store in the format expected by the frontend polling endpoint
            cad_results = {"results": cad_results, **processed_results}
        
        # Extract filename, status, and session_id safely
        if isinstance(payload, dict):
            filename = payload.get('filename', 'Unknown file')
            status = payload.get('status', 'success')
            session_id = payload.get('session_id', None)
        elif isinstance(payload, list) and len(payload) > 0:
            # For array format, extract session_id from first item
            filename = 'Unknown file'
            status = 'success'
            session_id = payload[0].get('session_id', None) if isinstance(payload[0], dict) else None
        else:
            filename = 'Unknown file'
            status = 'success'
            session_id = None
        
        # Log session_id if present
        if session_id:
            logger.info(f"Received webhook with session_id: {session_id}")
        else:
            logger.info("No session_id found in webhook payload")
        
        # Log the analysis results with detailed payload
        logger.info(f"CAD Analysis Results - File: {filename}, Status: {status}")
        logger.info(f"Full payload received: {json.dumps(payload, indent=2)}")
        
        # Store the latest result in a simple file for easy access
        result_data = {
            "filename": filename,
            "timestamp": str(payload.get('timestamp', 'Unknown') if isinstance(payload, dict) else 'Unknown'),
            "status": status,
            "session_id": session_id,  # Include session_id in stored data
            "cad_analysis": cad_results,
            "full_payload": payload
        }
        
        # Write to a simple JSON file for easy access
        results_dir = os.path.join(os.path.dirname(__file__), 'cad_results')
        os.makedirs(results_dir, exist_ok=True)
        
        with open(os.path.join(results_dir, 'latest_result.json'), 'w') as f:
            json.dump(result_data, f, indent=2)
        
        # Return success response
        response_data = {
            'status': 'success',
            'message': 'CAD analysis results received successfully',
            'processed_data': {
                'filename': filename,
                'status': status,
                'results_stored': True
            }
        }
        
        return JsonResponse(response_data, status=200)
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in webhook payload: {str(e)}"
        logger.error(error_msg)
        return JsonResponse({'error': error_msg}, status=400)
    
    except Exception as e:
        error_msg = f"Unexpected error processing webhook: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return JsonResponse({'error': error_msg}, status=500)
