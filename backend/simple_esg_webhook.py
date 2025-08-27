"""
Simple ESG Webhook Handler

A standalone webhook endpoint that doesn't require database setup.
This can be used until the full Django backend is properly configured.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def simple_esg_webhook(request):
    """
    Simple webhook receiver for ESG analysis results from n8n
    
    This endpoint accepts webhook data and logs it without requiring database tables.
    """
    try:
        # Parse the webhook payload
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
        else:
            payload = dict(request.POST)
        
        logger.info(f"Received ESG webhook payload: {payload}")
        
        # Extract key information - handle nested JSON format from n8n
        document_language = 'Unknown'
        total_volume_litres = 'Not found'
        
        # Check if data is in the "answer" field as JSON string
        if 'answer' in payload:
            try:
                answer_data = json.loads(payload['answer'])
                document_language = answer_data.get('identified_language', 'Unknown')
                total_volume_litres = answer_data.get('total_litres', 'Not found')
            except (json.JSONDecodeError, TypeError):
                # If answer is not JSON, try direct access
                pass
        
        # Fallback to direct access
        if document_language == 'Unknown':
            document_language = payload.get('document_language') or payload.get('identified_language', 'Unknown')
        if total_volume_litres == 'Not found':
            total_volume_litres = payload.get('total_volume_litres') or payload.get('total_litres', 'Not found')
            
        status = payload.get('status', 'success')
        filename = payload.get('filename', 'Unknown file')
        
        # Log the analysis results with detailed payload
        logger.info(f"ESG Analysis Results - File: {filename}, Language: {document_language}, Volume: {total_volume_litres}, Status: {status}")
        logger.info(f"Full payload received: {json.dumps(payload, indent=2)}")
        
        # Store the latest result in a simple file for easy access
        # Handle volume formatting properly
        if isinstance(total_volume_litres, str) and "L" in str(total_volume_litres):
            volume_display = str(total_volume_litres)  # Already has L
        elif total_volume_litres and str(total_volume_litres) != "0":
            volume_display = str(total_volume_litres) + " L"
        else:
            volume_display = "Not found"
            
        result_data = {
            "identified_language": document_language,
            "total_litres": volume_display,
            "filename": filename,
            "timestamp": str(payload.get('timestamp', 'Unknown')),
            "full_payload": payload
        }
        
        # Write to a simple JSON file for easy access
        import os
        results_dir = os.path.join(os.path.dirname(__file__), 'esg_results')
        os.makedirs(results_dir, exist_ok=True)
        
        with open(os.path.join(results_dir, 'latest_result.json'), 'w') as f:
            json.dump(result_data, f, indent=2)
        
        # Return success response
        response_data = {
            'status': 'success',
            'message': 'ESG analysis results received successfully',
            'processed_data': {
                'document_language': document_language,
                'total_volume_litres': total_volume_litres,
                'filename': filename,
                'status': status
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
