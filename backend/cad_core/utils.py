import requests
import json
import logging
import os
from django.conf import settings
from django.urls import reverse
from django.core.files.storage import default_storage
from requests_toolbelt.multipart.encoder import MultipartEncoder
from .serializers import WebhookPayloadSerializer

logger = logging.getLogger(__name__)

def send_to_n8n_webhook(cad_upload):
    """Send CAD upload file to n8n webhook trigger for processing"""
    
    try:
        # Get the webhook URL - using your new webhook path
        webhook_path = "fe198a5f-79e0-4dc7-82d1-ce7fb65e9c5e"
        n8n_webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', f'http://localhost:5678/webhook/{webhook_path}')
        
        # Prepare the file for upload
        if not cad_upload.file_path:
            logger.error(f"No file path for upload {cad_upload.id}")
            return False
        
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
                        'User-Agent': 'Django-CAD-Analyzer/1.0',
                        'Content-Type': payload.content_type
                    },
                    timeout=120  # Increased timeout for file upload and processing
                )
                
                # Check response
                if response.status_code in [200, 201]:
                    logger.info(f"Successfully sent upload {cad_upload.id} to n8n webhook")
                    
                    # Store webhook response
                    try:
                        if response.headers.get('content-type', '').startswith('application/json'):
                            response_data = response.json()
                            cad_upload.webhook_response = response_data
                        else:
                            cad_upload.webhook_response = {
                                'status': 'submitted', 
                                'response_code': response.status_code,
                                'message': 'File submitted to n8n webhook successfully'
                            }
                        cad_upload.save()
                    except json.JSONDecodeError:
                        logger.info(f"n8n webhook returned non-JSON response: {response.status_code}")
                        cad_upload.webhook_response = {
                            'status': 'submitted', 
                            'response_code': response.status_code
                        }
                        cad_upload.save()
                    
                    return True
                else:
                    logger.error(f"n8n webhook returned status {response.status_code}: {response.text}")
                    return False
                    
        except Exception as file_error:
            logger.error(f"Error reading file for upload {cad_upload.id}: {str(file_error)}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending to n8n webhook: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in send_to_n8n_webhook: {str(e)}")
        return False

def send_to_n8n_form(cad_upload):
    """Send CAD upload data to n8n form for processing - kept for backward compatibility"""
    
    try:
        # For the form-based workflow, we need to submit the file directly to the n8n form
        # Get the form URL from your n8n workflow (replace with your actual form URL)
        n8n_form_url = getattr(settings, 'N8N_FORM_URL', 'http://localhost:5678/form/ffc0c29a-e891-4521-b822-e0d1ac468a19')
        
        # Prepare the file for upload
        if not cad_upload.file_path:
            logger.error(f"No file path for upload {cad_upload.id}")
            return False
        
        # Open and read the file
        try:
            with cad_upload.file_path.open('rb') as file:
                files = {
                    'pdfFile': (cad_upload.original_filename, file, 'application/pdf')
                }
                
                # Submit to n8n form
                response = requests.post(
                    n8n_form_url,
                    files=files,
                    headers={
                        'User-Agent': 'Django-CAD-Analyzer/1.0'
                    },
                    timeout=60  # Increased timeout for file upload
                )
                
                # Check response
                if response.status_code in [200, 201, 302]:  # Form submissions often redirect
                    logger.info(f"Successfully sent upload {cad_upload.id} to n8n form")
                    
                    # Store form response
                    try:
                        if response.headers.get('content-type', '').startswith('application/json'):
                            response_data = response.json()
                            cad_upload.webhook_response = response_data
                        else:
                            cad_upload.webhook_response = {'status': 'submitted', 'response_code': response.status_code}
                        cad_upload.save()
                    except json.JSONDecodeError:
                        logger.info(f"n8n form returned non-JSON response: {response.status_code}")
                    
                    return True
                else:
                    logger.error(f"n8n form returned status {response.status_code}: {response.text}")
                    return False
                    
        except Exception as file_error:
            logger.error(f"Error reading file for upload {cad_upload.id}: {str(file_error)}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending to n8n form: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in send_to_n8n_form: {str(e)}")
        return False

def generate_file_url(cad_upload):
    """Generate a URL for the uploaded file that n8n can access"""
    
    # In production, this would be an absolute URL to the file
    # For development, we'll use the Django media URL
    if cad_upload.file_path:
        # Generate absolute URL
        if settings.DEBUG:
            # Development - use Django dev server
            return f"http://localhost:8000{cad_upload.file_path.url}"
        else:
            # Production - use configured domain
            domain = getattr(settings, 'SITE_DOMAIN', 'https://your-domain.com')
            return f"{domain}{cad_upload.file_path.url}"
    
    return None

def generate_download_urls(cad_upload, request=None):
    """Generate download URLs for analysis results"""
    
    download_urls = {}
    
    for result in cad_upload.results.all():
        result_key = result.result_type
        
        if result.csv_file_path:
            if request:
                download_urls[f"{result_key}_csv"] = request.build_absolute_uri(result.csv_file_path.url)
            else:
                download_urls[f"{result_key}_csv"] = result.csv_file_path.url
        
        if result.report_file_path:
            if request:
                download_urls[f"{result_key}_report"] = request.build_absolute_uri(result.report_file_path.url)
            else:
                download_urls[f"{result_key}_report"] = result.report_file_path.url
    
    return download_urls

def create_csv_from_results(analysis_result):
    """Create CSV file from analysis results"""
    import csv
    import tempfile
    from django.core.files.base import ContentFile
    
    try:
        # Extract data from results
        data = analysis_result.processed_data or analysis_result.raw_data
        
        if not data or not isinstance(data, (list, dict)):
            logger.warning(f"No valid data to create CSV for result {analysis_result.id}")
            return None
        
        # Create CSV content
        csv_content = []
        
        if isinstance(data, dict):
            # Convert dict to list of key-value pairs
            if analysis_result.result_type == 'dimensions':
                csv_content = create_dimensions_csv(data)
            elif analysis_result.result_type == 'tolerances':
                csv_content = create_tolerances_csv(data)
            elif analysis_result.result_type == 'relationships':
                csv_content = create_relationships_csv(data)
            else:
                # Generic key-value CSV
                csv_content = [['Key', 'Value']]
                for key, value in data.items():
                    csv_content.append([str(key), str(value)])
        
        elif isinstance(data, list):
            # List of items
            if data and isinstance(data[0], dict):
                # List of dictionaries - use keys as headers
                headers = list(data[0].keys())
                csv_content = [headers]
                for item in data:
                    row = [str(item.get(header, '')) for header in headers]
                    csv_content.append(row)
            else:
                # Simple list
                csv_content = [['Value']]
                for item in data:
                    csv_content.append([str(item)])
        
        # Convert to CSV string
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_content)
        csv_string = output.getvalue()
        
        # Save as file
        filename = f"{analysis_result.result_type}_results_{analysis_result.upload.id}.csv"
        analysis_result.csv_file_path.save(
            filename,
            ContentFile(csv_string.encode('utf-8')),
            save=True
        )
        
        logger.info(f"Created CSV file for result {analysis_result.id}")
        return analysis_result.csv_file_path.url
        
    except Exception as e:
        logger.error(f"Error creating CSV for result {analysis_result.id}: {str(e)}")
        return None

def create_dimensions_csv(data):
    """Create CSV structure for dimensions data"""
    csv_content = [['Component', 'Dimension Type', 'Value', 'Unit', 'Tolerance', 'Confidence']]
    
    if 'dimensions' in data:
        for dimension in data['dimensions']:
            csv_content.append([
                dimension.get('component', ''),
                dimension.get('type', ''),
                dimension.get('value', ''),
                dimension.get('unit', ''),
                dimension.get('tolerance', ''),
                dimension.get('confidence', '')
            ])
    
    return csv_content

def create_tolerances_csv(data):
    """Create CSV structure for tolerances data"""
    csv_content = [['Component', 'Tolerance Type', 'Value', 'Upper Limit', 'Lower Limit', 'Grade']]
    
    if 'tolerances' in data:
        for tolerance in data['tolerances']:
            csv_content.append([
                tolerance.get('component', ''),
                tolerance.get('type', ''),
                tolerance.get('value', ''),
                tolerance.get('upper_limit', ''),
                tolerance.get('lower_limit', ''),
                tolerance.get('grade', '')
            ])
    
    return csv_content

def create_relationships_csv(data):
    """Create CSV structure for relationships data"""
    csv_content = [['Part A', 'Part B', 'Relationship Type', 'Connection', 'Notes']]
    
    if 'relationships' in data:
        for relationship in data['relationships']:
            csv_content.append([
                relationship.get('part_a', ''),
                relationship.get('part_b', ''),
                relationship.get('type', ''),
                relationship.get('connection', ''),
                relationship.get('notes', '')
            ])
    
    return csv_content

def cleanup_old_files():
    """Cleanup old uploaded files and results (called by periodic task)"""
    from django.utils import timezone
    from datetime import timedelta
    
    # Delete files older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    
    old_uploads = CADUpload.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed']
    )
    
    deleted_count = 0
    for upload in old_uploads:
        try:
            # Delete file
            if upload.file_path:
                default_storage.delete(upload.file_path.name)
            
            # Delete result files
            for result in upload.results.all():
                if result.csv_file_path:
                    default_storage.delete(result.csv_file_path.name)
                if result.report_file_path:
                    default_storage.delete(result.report_file_path.name)
            
            # Delete database record
            upload.delete()
            deleted_count += 1
            
        except Exception as e:
            logger.error(f"Error deleting old upload {upload.id}: {str(e)}")
    
    logger.info(f"Cleaned up {deleted_count} old uploads")
    return deleted_count

def validate_file_type(file):
    """Validate uploaded file type and content"""
    import magic
    
    # Check file extension
    if not file.name.lower().endswith('.pdf'):
        return False, "Only PDF files are allowed"
    
    # Check file size
    if file.size > 10 * 1024 * 1024:  # 10MB
        return False, "File size cannot exceed 10MB"
    
    # Check MIME type using python-magic
    try:
        file_content = file.read(2048)  # Read first 2KB
        file.seek(0)  # Reset file pointer
        
        mime_type = magic.from_buffer(file_content, mime=True)
        if mime_type != 'application/pdf':
            return False, f"Invalid file type: {mime_type}. Only PDF files are allowed."
        
    except Exception as e:
        logger.warning(f"Could not validate file MIME type: {str(e)}")
        # Continue without MIME validation if python-magic is not available
    
    return True, "File is valid" 