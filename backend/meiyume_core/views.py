"""
Views for meiyume_core app - shared functionality across all assistants
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json
import requests
import base64
import os
from io import BytesIO, StringIO
import csv

from .models import UserPreferences, ProcessingLog
from .serializers import UserPreferencesSerializer
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from rest_framework.request import Request

class FileUploadView(generics.CreateAPIView):
    """Handle file uploads and send to n8n workflow"""
    
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = []  # Temporarily disable authentication for testing
    
    def create(self, request, *args, **kwargs):
        """Handle file upload and send to n8n workflow"""
        try:
            # Get uploaded file
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return Response(
                    {'error': 'No file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get session_id from form data
            session_id = request.data.get('session_id')
            if not session_id:
                return Response(
                    {'error': 'No session_id provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert file to base64
            file_content = uploaded_file.read()
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Send to n8n workflow via webhook
            n8n_webhook_url = "https://meiyume.app.n8n.cloud/webhook/3f700683-6240-4e87-8fc3-dcbeb96ea69c"
            
            # Reset file pointer to beginning and read content once
            uploaded_file.seek(0)
            file_content = uploaded_file.read()
            
            # Prepare webhook payload
            webhook_payload = {
                "data": base64.b64encode(file_content).decode('utf-8'),
                "session_id": session_id
            }
            
            # Debug: Log what we're sending
            print(f"DEBUG: Sending to n8n webhook - URL: {n8n_webhook_url}")
            print(f"DEBUG: Payload keys: {list(webhook_payload.keys())}")
            print(f"DEBUG: File content length: {len(file_content)} bytes")
            print(f"DEBUG: Session ID: {session_id}")
            print(f"DEBUG: File name: {uploaded_file.name}")
            
            response = requests.post(
                n8n_webhook_url,
                json=webhook_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            # Debug: Log response
            print(f"DEBUG: n8n response status: {response.status_code}")
            print(f"DEBUG: n8n response: {response.text[:200]}...")
            
            if response.status_code == 200:
                # Create a simple response with task ID
                task_id = f"task_{int(timezone.now().timestamp())}"
                
                # Store session_id mapping for tracking
                session_mapping = {
                    'task_id': task_id,
                    'session_id': session_id,
                    'filename': uploaded_file.name,
                    'uploaded_at': timezone.now().isoformat(),
                    'status': 'uploaded'
                }
                
                # Save session mapping to file
                import os
                sessions_dir = os.path.join(os.path.dirname(__file__), '..', 'sessions')
                os.makedirs(sessions_dir, exist_ok=True)
                
                session_file = os.path.join(sessions_dir, f"{task_id}.json")
                with open(session_file, 'w') as f:
                    json.dump(session_mapping, f, indent=2)
                
                return Response({
                    'id': task_id,
                    'status': 'uploaded',
                    'message': 'File uploaded and sent to n8n workflow',
                    'filename': uploaded_file.name,
                    'task_id': task_id,
                    'session_id': session_id
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': f'n8n workflow error: {response.status_code}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FileResultView(generics.RetrieveAPIView):
    """Get processing results for a file"""
    
    permission_classes = []  # Temporarily disable authentication for testing
    
    def _group_dimensions_by_part(self, dimension_data):
        """Group dimension data by part name"""
        parts = {}
        
        for row in dimension_data:
            part_name = row.get('Part Name', 'Unknown')
            if part_name not in parts:
                parts[part_name] = {
                    'name': part_name,
                    'dimensions': []
                }
            
            parts[part_name]['dimensions'].append({
                'name': row.get('Feature', ''),
                'value': row.get('Value', ''),
                'tolerance': row.get('Tolerance', ''),
                'unit': row.get('Unit', ''),
                'critical': row.get('Critical', 'False').lower() == 'true'
            })
        
        return list(parts.values())
    
    def retrieve(self, request, *args, **kwargs):
        """Get results for a specific task"""
        task_id = kwargs.get('pk')
        
        try:
            # Check if we have results from the n8n workflow
            results_file = os.path.join(os.path.dirname(__file__), '..', 'cad_results', 'latest_result.json')
            
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    result_data = json.load(f)
                
                # Check if we have actual results (not just a placeholder)
                if result_data.get('status') == 'uploaded' or not result_data.get('cad_analysis'):
                    # No real results yet, return processing status
                    return Response({
                        'id': task_id,
                        'status': 'uploaded',
                        'message': 'File uploaded, waiting for n8n processing'
                    })
                
                # Extract the results from the n8n response
                cad_analysis = result_data.get('cad_analysis', {})
                
                # Format results for the frontend
                formatted_results = []
                
                # First: honor raw base64 payload if present (frontend expects base64 list)
                # Try to get expected session_id from stored mapping once
                expected_session_id = None
                try:
                    sessions_dir = os.path.join(os.path.dirname(__file__), '..', 'sessions')
                    session_file = os.path.join(sessions_dir, f"{task_id}.json")
                    if os.path.exists(session_file):
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)
                            expected_session_id = session_data.get('session_id')
                except Exception as e:
                    print(f"Error reading session mapping: {e}")

                if isinstance(cad_analysis, dict) and (
                    isinstance(cad_analysis.get('dimension'), str) or isinstance(cad_analysis.get('matching'), str)
                ):
                    result_item = {
                        'dimension': cad_analysis.get('dimension'),
                        'matching': cad_analysis.get('matching'),
                        'session_id': result_data.get('session_id') or cad_analysis.get('session_id') or expected_session_id
                    }
                    if expected_session_id and result_item.get('session_id') != expected_session_id:
                        return Response({
                            'id': task_id,
                            'status': 'processing',
                            'session_id': expected_session_id,
                            'message': 'Results received, waiting for this session_id'
                        })
                    return Response({
                        'id': task_id,
                        'status': 'completed',
                        'session_id': expected_session_id,
                        'results': [result_item]
                    })

                # Check if we have JSON data from the webhook
                if 'dimension_json' in cad_analysis:
                    try:
                        dimension_data = cad_analysis['dimension_json']
                        formatted_results.append({
                            "result_type": "dimensions",
                            "raw_data": dimension_data
                        })
                    except Exception as e:
                        print(f"Error processing dimension JSON data: {e}")
                
                if 'matching_json' in cad_analysis:
                    try:
                        matching_data = cad_analysis['matching_json']
                        formatted_results.append({
                            "result_type": "matching",
                            "raw_data": matching_data
                        })
                    except Exception as e:
                        print(f"Error processing matching JSON data: {e}")
                
                # Fallback: Check if we have CSV data from the webhook
                if 'dimension_csv' in cad_analysis:
                    try:
                        # Parse CSV data
                        dimension_data = []
                        csv_reader = csv.DictReader(StringIO(cad_analysis['dimension_csv']))
                        for row in csv_reader:
                            dimension_data.append(row)
                        
                        formatted_results.append({
                            "result_type": "dimensions",
                            "raw_data": {
                                "parts": self._group_dimensions_by_part(dimension_data)
                            }
                        })
                    except Exception as e:
                        print(f"Error parsing dimension CSV data: {e}")
                
                if 'matching_csv' in cad_analysis:
                    try:
                        # Parse CSV data
                        matching_data = []
                        csv_reader = csv.DictReader(StringIO(cad_analysis['matching_csv']))
                        for row in csv_reader:
                            matching_data.append(row)
                        
                        formatted_results.append({
                            "result_type": "matching",
                            "raw_data": {
                                "matches": matching_data
                            }
                        })
                    except Exception as e:
                        print(f"Error parsing matching CSV data: {e}")
                
                # Check if we have results array with base64 data (new format with session_id)
                if 'results' in cad_analysis and isinstance(cad_analysis['results'], list):
                    # Try to get session_id from stored mapping
                    expected_session_id = None
                    try:
                        sessions_dir = os.path.join(os.path.dirname(__file__), '..', 'sessions')
                        session_file = os.path.join(sessions_dir, f"{task_id}.json")
                        if os.path.exists(session_file):
                            with open(session_file, 'r') as f:
                                session_data = json.load(f)
                                expected_session_id = session_data.get('session_id')
                    except Exception as e:
                        print(f"Error reading session mapping: {e}")

                    results_list = cad_analysis['results']
                    matched_results = results_list
                    if expected_session_id:
                        matched_results = [
                            r for r in results_list
                            if isinstance(r, dict) and (
                                r.get('session_id') == expected_session_id or
                                r.get('sessionId') == expected_session_id
                            )
                        ]
                        if not matched_results:
                            return Response({
                                'id': task_id,
                                'status': 'processing',
                                'session_id': expected_session_id,
                                'message': 'Results received, waiting for this session_id'
                            })

                    return Response({
                        'id': task_id,
                        'status': 'completed',
                        'session_id': expected_session_id,
                        'results': matched_results
                    })
                
                # Check if we have the new webhook format with session_id in the results array
                if isinstance(cad_analysis, list) and len(cad_analysis) > 0:
                    # Try to get session_id from stored mapping
                    expected_session_id = None
                    try:
                        sessions_dir = os.path.join(os.path.dirname(__file__), '..', 'sessions')
                        session_file = os.path.join(sessions_dir, f"{task_id}.json")
                        if os.path.exists(session_file):
                            with open(session_file, 'r') as f:
                                session_data = json.load(f)
                                expected_session_id = session_data.get('session_id')
                    except Exception as e:
                        print(f"Error reading session mapping: {e}")

                    results_list = cad_analysis
                    matched_results = results_list
                    if expected_session_id:
                        matched_results = [
                            r for r in results_list
                            if isinstance(r, dict) and (
                                r.get('session_id') == expected_session_id or
                                r.get('sessionId') == expected_session_id
                            )
                        ]
                        if not matched_results:
                            return Response({
                                'id': task_id,
                                'status': 'processing',
                                'session_id': expected_session_id,
                                'message': 'Results received, waiting for this session_id'
                            })

                    return Response({
                        'id': task_id,
                        'status': 'completed',
                        'session_id': expected_session_id,
                        'results': matched_results
                    })
                
                # Fallback: Check if we have results array with base64 data (old format without session_id)
                if 'results' in cad_analysis and isinstance(cad_analysis['results'], list):
                    for result in cad_analysis['results']:
                        # Decode dimension data
                        if 'dimension' in result and isinstance(result['dimension'], str):
                            try:
                                dimension_bytes = base64.b64decode(result['dimension'])
                                dimension_csv = dimension_bytes.decode('utf-8')
                                
                                # Parse CSV data
                                dimension_data = []
                                csv_reader = csv.DictReader(StringIO(dimension_csv))
                                for row in csv_reader:
                                    dimension_data.append(row)
                                
                                formatted_results.append({
                                    "result_type": "dimensions",
                                    "raw_data": {
                                        "parts": self._group_dimensions_by_part(dimension_data)
                                    }
                                })
                            except Exception as e:
                                print(f"Error decoding dimension data: {e}")
                        
                        # Decode matching data
                        if 'matching' in result and isinstance(result['matching'], str):
                            try:
                                matching_bytes = base64.b64decode(result['matching'])
                                matching_csv = matching_bytes.decode('utf-8')
                                
                                # Parse CSV data
                                matching_data = []
                                csv_reader = csv.DictReader(StringIO(matching_csv))
                                for row in csv_reader:
                                    matching_data.append(row)
                                
                                formatted_results.append({
                                    "result_type": "matching",
                                    "raw_data": {
                                        "matches": matching_data
                                    }
                                })
                            except Exception as e:
                                print(f"Error decoding matching data: {e}")
                
                # Fallback to decoded data if available
                if 'dimension_decoded' in cad_analysis:
                    formatted_results.append({
                        "result_type": "dimensions",
                        "raw_data": cad_analysis['dimension_decoded']
                    })
                
                if 'matching_decoded' in cad_analysis:
                    formatted_results.append({
                        "result_type": "matching",
                        "raw_data": cad_analysis['matching_decoded']
                    })
                
                # Try to get session_id from stored mapping
                session_id = None
                try:
                    sessions_dir = os.path.join(os.path.dirname(__file__), '..', 'sessions')
                    session_file = os.path.join(sessions_dir, f"{task_id}.json")
                    if os.path.exists(session_file):
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)
                            session_id = session_data.get('session_id')
                except Exception as e:
                    print(f"Error reading session mapping: {e}")
                
                return Response({
                    'id': task_id,
                    'status': 'completed',
                    'session_id': session_id,
                    'results': formatted_results
                })
            else:
                # Return processing status
                # Try to get session_id from stored mapping
                session_id = None
                try:
                    sessions_dir = os.path.join(os.path.dirname(__file__), '..', 'sessions')
                    session_file = os.path.join(sessions_dir, f"{task_id}.json")
                    if os.path.exists(session_file):
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)
                            session_id = session_data.get('session_id')
                except Exception as e:
                    print(f"Error reading session mapping: {e}")
                
                return Response({
                    'id': task_id,
                    'status': 'processing',
                    'session_id': session_id,
                    'message': 'Results not yet available'
                })
                
        except Exception as e:
            return Response(
                {'error': f'Failed to get results: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """View for managing user preferences"""
    
    serializer_class = UserPreferencesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Get or create user preferences"""
        preferences, created = UserPreferences.objects.get_or_create(
            user=self.request.user
        )
        return preferences

class DashboardStatsView(generics.GenericAPIView):
    """View for dashboard statistics across all assistants"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard statistics"""
        user = request.user
        
        # Get statistics for each assistant
        stats = {
            'total_uploads': 0,
            'completed_uploads': 0,
            'failed_uploads': 0,
            'processing_uploads': 0,
            'assistants': {}
        }
        
        # CAD Assistant stats
        try:
            from assistants.cad.models import CADUpload
            cad_stats = self._get_assistant_stats(CADUpload, user)
            stats['assistants']['cad'] = cad_stats
            stats['total_uploads'] += cad_stats['total']
            stats['completed_uploads'] += cad_stats['completed']
            stats['failed_uploads'] += cad_stats['failed']
            stats['processing_uploads'] += cad_stats['processing']
        except ImportError:
            stats['assistants']['cad'] = {'total': 0, 'completed': 0, 'failed': 0, 'processing': 0}
        
        # Recent activity
        stats['recent_uploads'] = self._get_recent_uploads(user)
        
        return Response(stats)
    
    def _get_assistant_stats(self, model_class, user):
        """Get statistics for a specific assistant"""
        queryset = model_class.objects.filter(user=user)
        
        return {
            'total': queryset.count(),
            'completed': queryset.filter(status='completed').count(),
            'failed': queryset.filter(status='failed').count(),
            'processing': queryset.filter(status__in=['uploaded', 'processing']).count(),
        }
    
    def _get_recent_uploads(self, user):
        """Get recent uploads across all assistants"""
        recent_uploads = []
        
        # Get recent CAD uploads
        try:
            from assistants.cad.models import CADUpload
            cad_uploads = CADUpload.objects.filter(
                user=user
            ).order_by('-created_at')[:5]
            
            for upload in cad_uploads:
                recent_uploads.append({
                    'id': str(upload.id),
                    'assistant': 'cad',
                    'filename': upload.original_filename,
                    'status': upload.status,
                    'created_at': upload.created_at,
                    'project_name': upload.project_name
                })
        except ImportError:
            pass
        
        # Sort by creation date
        recent_uploads.sort(key=lambda x: x['created_at'], reverse=True)
        return recent_uploads[:10]

class HealthCheckView(generics.GenericAPIView):
    """Health check endpoint"""
    
    def get(self, request):
        """Return health status"""
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now(),
            'version': '1.0.0'
        })

class ProcessingLogView(generics.ListAPIView):
    """View for processing logs"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get processing logs for the user"""
        user = self.request.user
        
        # Get logs for all user's uploads across assistants
        logs = ProcessingLog.objects.filter(
            content_type__model__in=['cadupload', 'qualityupload', 'complaintupload'],
            object_id__in=self._get_user_upload_ids(user)
        ).order_by('-created_at')
        
        return logs
    
    def _get_user_upload_ids(self, user):
        """Get all upload IDs for the user across assistants"""
        upload_ids = []
        
        # CAD uploads
        try:
            from assistants.cad.models import CADUpload
            cad_ids = list(CADUpload.objects.filter(user=user).values_list('id', flat=True))
            upload_ids.extend(cad_ids)
        except ImportError:
            pass
        
        return upload_ids 