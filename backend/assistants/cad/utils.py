"""
Utilities for CAD assistant
"""

import requests
import logging
from django.conf import settings
from requests_toolbelt import MultipartEncoder

logger = logging.getLogger(__name__)

def send_to_n8n_webhook(cad_upload):
    """
    Send CAD upload to n8n webhook for processing
    
    Args:
        cad_upload: CADUpload instance to process
    """
    
    # Get n8n webhook URL from settings
    n8n_webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', '')
    if not n8n_webhook_url:
        raise ValueError("N8N_WEBHOOK_URL not configured in settings")
    
    # Open and read the file
    try:
        with cad_upload.file_path.open('rb') as file:
            # Use MultipartEncoder to correctly set Content-Type and Content-Length
            payload = MultipartEncoder(
                fields={
                    'pdfFile': (cad_upload.original_filename, file, 'application/pdf'),
                    'upload_id': str(cad_upload.id),
                    'original_filename': cad_upload.original_filename,
                    'project_name': cad_upload.project_name or '',
                    'drawing_number': cad_upload.drawing_number or '',
                    'revision': cad_upload.revision or '',
                    'user_id': str(cad_upload.user.id),
                    'webhook_secret': getattr(settings, 'N8N_WEBHOOK_SECRET', '')
                }
            )
            
            # Send to n8n webhook
            response = requests.post(
                n8n_webhook_url,
                data=payload,
                headers={
                    'User-Agent': 'Meiyume-AI-Assistant/1.0',
                    'Content-Type': payload.content_type
                },
                timeout=120  # Increased timeout for file upload and processing
            )
            
            response.raise_for_status()
            
            logger.info(f"Successfully sent CAD upload {cad_upload.id} to n8n")
            return response.json()
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send CAD upload {cad_upload.id} to n8n: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending CAD upload {cad_upload.id} to n8n: {str(e)}")
        raise 