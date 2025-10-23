"""
Simple Compliance Webhook Handler

A standalone webhook endpoint that saves latest Compliance (MSDS) results.
Mirrors the simple ESG/CAD handlers for quick integration without DB models.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import os


logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def simple_compliance_webhook(request):
    """Receive compliance results from n8n and store the latest result."""
    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
        else:
            payload = dict(request.POST)

        logger.info(f"Received Compliance webhook payload: {payload}")

        # Try to extract key fields, allowing for n8n formats
        filename = payload.get('filename', 'Unknown file') if isinstance(payload, dict) else 'Unknown file'
        status = payload.get('status', 'success') if isinstance(payload, dict) else 'success'
        product_name = payload.get('product_name') if isinstance(payload, dict) else None
        supplier_name = payload.get('supplier_name') if isinstance(payload, dict) else None

        # If n8n placed structured data inside an 'answer' field, try parsing it
        structured = {}
        if isinstance(payload, dict) and 'answer' in payload:
            try:
                structured = json.loads(payload['answer']) if isinstance(payload['answer'], str) else payload['answer']
            except (json.JSONDecodeError, TypeError):
                structured = {"raw_answer": payload['answer']}

        result_data = {
            "filename": filename,
            "status": status,
            "product_name": product_name,
            "supplier_name": supplier_name,
            "full_payload": payload,
            "structured": structured,
        }

        # Persist latest result to file
        results_dir = os.path.join(os.path.dirname(__file__), 'compliance_results')
        os.makedirs(results_dir, exist_ok=True)
        with open(os.path.join(results_dir, 'latest_result.json'), 'w') as f:
            json.dump(result_data, f, indent=2)

        response_data = {
            'status': 'success',
            'message': 'Compliance results received successfully',
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








