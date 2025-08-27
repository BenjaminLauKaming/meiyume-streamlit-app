"""
Simple endpoint to get the latest CAD results
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import os
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def get_latest_cad_result(request):
    """
    Get the latest CAD analysis result
    """
    try:
        results_file = os.path.join(os.path.dirname(__file__), 'cad_results', 'latest_result.json')
        
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                result_data = json.load(f)
            
            return JsonResponse({
                'status': 'success',
                'data': result_data
            })
        else:
            return JsonResponse({
                'status': 'no_data',
                'message': 'No CAD results available yet'
            })
            
    except Exception as e:
        logger.error(f"Error retrieving CAD results: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
