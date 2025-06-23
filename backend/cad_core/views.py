from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny

import requests
import json
import logging
import os
from datetime import timedelta

from .models import CADUpload, AnalysisOptions, AnalysisResult, ProcessingLog, UserPreferences
from .serializers import (
    CADUploadDetailSerializer, CADUploadListSerializer, CADUploadCreateSerializer,
    AnalysisResultSerializer, ProcessingStatusSerializer, UserPreferencesSerializer,
    N8NWebhookResponseSerializer, WebhookPayloadSerializer
)
from .utils import send_to_n8n_form, send_to_n8n_webhook, generate_download_urls

logger = logging.getLogger(__name__)

class CADUploadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing CAD file uploads"""
    
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return CADUpload.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CADUploadCreateSerializer
        elif self.action == 'list':
            return CADUploadListSerializer
        else:
            return CADUploadDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Handle file upload and trigger n8n processing"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the upload record
        cad_upload = serializer.save()
        
        # Log the upload
        ProcessingLog.objects.create(
            upload=cad_upload,
            level='info',
            message=f"File uploaded successfully: {cad_upload.original_filename}",
            step='file_upload'
        )
        
        # Send to n8n form
        try:
            success = send_to_n8n_form(cad_upload)
            if success:
                cad_upload.status = 'processing'
                cad_upload.processing_started_at = timezone.now()
                cad_upload.save()
                
                ProcessingLog.objects.create(
                    upload=cad_upload,
                    level='info',
                    message="Successfully sent to n8n for processing",
                    step='webhook_trigger'
                )
            else:
                cad_upload.status = 'failed'
                cad_upload.error_message = "Failed to send to n8n webhook"
                cad_upload.save()
                
                ProcessingLog.objects.create(
                    upload=cad_upload,
                    level='error',
                    message="Failed to send to n8n webhook",
                    step='webhook_trigger'
                )
        except Exception as e:
            logger.error(f"Error sending to n8n webhook: {str(e)}")
            cad_upload.status = 'failed'
            cad_upload.error_message = str(e)
            cad_upload.save()
        
        # Return response with task_id
        response_data = {
            'task_id': str(cad_upload.id),
            'status': cad_upload.status,
            'message': 'File uploaded successfully' if cad_upload.status != 'failed' else cad_upload.error_message
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get processing status for a specific upload"""
        cad_upload = self.get_object()
        
        response_data = {
            'task_id': str(cad_upload.id),
            'status': cad_upload.status,
            'progress': cad_upload.progress_percentage,
            'message': f"Processing {cad_upload.original_filename}"
        }
        
        # Add results if completed
        if cad_upload.status == 'completed':
            results = {}
            download_urls = {}
            
            for result in cad_upload.results.all():
                results[result.result_type] = result.processed_data or result.raw_data
                
                # Generate download URLs
                if result.csv_file_path:
                    download_urls[f"{result.result_type}_csv"] = request.build_absolute_uri(result.csv_file_path.url)
                if result.report_file_path:
                    download_urls[f"{result.result_type}_report"] = request.build_absolute_uri(result.report_file_path.url)
            
            response_data['results'] = results
            response_data['download_urls'] = download_urls
        
        # Add error message if failed
        if cad_upload.status == 'failed':
            response_data['error_message'] = cad_upload.error_message
        
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry failed processing"""
        cad_upload = self.get_object()
        
        if cad_upload.status != 'failed':
            return Response(
                {'error': 'Only failed uploads can be retried'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset upload status
        cad_upload.status = 'uploaded'
        cad_upload.error_message = None
        cad_upload.retry_count += 1
        cad_upload.save()
        
        # Send to n8n again
        try:
            success = send_to_n8n_form(cad_upload)
            if success:
                cad_upload.status = 'processing'
                cad_upload.processing_started_at = timezone.now()
                cad_upload.save()
        except Exception as e:
            cad_upload.status = 'failed'
            cad_upload.error_message = str(e)
            cad_upload.save()
        
        return Response({'status': cad_upload.status})

@api_view(['GET'])
@permission_classes([IsAuthenticated])  
def get_processing_status(request, task_id):
    """Get processing status for a specific task"""
    try:
        cad_upload = CADUpload.objects.get(id=task_id, user=request.user)
        
        response_data = {
            'task_id': str(cad_upload.id),
            'status': cad_upload.status,
            'progress': cad_upload.progress_percentage,
            'message': f"Processing {cad_upload.original_filename}"
        }
        
        if cad_upload.status == 'completed':
            # Include results and download URLs
            results = {}
            download_urls = {}
            
            for result in cad_upload.results.all():
                results[result.result_type] = result.processed_data or result.raw_data
                
                if result.csv_file_path:
                    download_urls[f"{result.result_type}_csv"] = request.build_absolute_uri(result.csv_file_path.url)
                if result.report_file_path:
                    download_urls[f"{result.result_type}_report"] = request.build_absolute_uri(result.report_file_path.url)
            
            response_data.update({
                'results': results,
                'download_urls': download_urls
            })
        elif cad_upload.status == 'failed':
            response_data['error_message'] = cad_upload.error_message
        
        return Response(response_data)
        
    except CADUpload.DoesNotExist:
        return Response(
            {'error': 'Upload not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([AllowAny])  # n8n webhook doesn't have user context
def n8n_webhook_callback(request):
    """Handle callback from n8n webhook with processing results"""
    
    # Validate webhook secret
    webhook_secret = request.data.get('webhook_secret')
    if webhook_secret != settings.N8N_WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret received")
        return Response(
            {'error': 'Invalid webhook secret'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = N8NWebhookResponseSerializer(data=request.data)
    if not serializer.is_valid():
        logger.error(f"Invalid webhook payload: {serializer.errors}")
        return Response(
            {'error': 'Invalid payload'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = serializer.validated_data
    upload_id = data['upload_id']
    
    try:
        cad_upload = CADUpload.objects.get(id=upload_id)
        
        # Update upload status
        cad_upload.n8n_execution_id = data['execution_id']
        cad_upload.status = data['status']
        cad_upload.progress_percentage = data.get('progress', 100 if data['status'] == 'completed' else 0)
        
        if data['status'] == 'completed':
            cad_upload.processing_completed_at = timezone.now()
            
            # Process results
            if 'results' in data:
                process_analysis_results(cad_upload, data['results'])
                
        elif data['status'] == 'failed':
            cad_upload.error_message = data.get('error_message', 'Processing failed')
        
        cad_upload.save()
        
        # Log the callback
        ProcessingLog.objects.create(
            upload=cad_upload,
            level='info' if data['status'] != 'failed' else 'error',
            message=f"Received n8n callback: {data['status']}",
            step='webhook_callback',
            metadata=data
        )
        
        return Response({'status': 'success'})
        
    except CADUpload.DoesNotExist:
        logger.error(f"Upload not found for callback: {upload_id}")
        return Response(
            {'error': 'Upload not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error processing webhook callback: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class UserPreferencesViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user preferences"""
    
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserPreferencesSerializer
    
    def get_queryset(self):
        return UserPreferences.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create user preferences"""
        obj, created = UserPreferences.objects.get_or_create(
            user=self.request.user,
            defaults={}
        )
        return obj

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for the user"""
    user_uploads = CADUpload.objects.filter(user=request.user)
    
    # Calculate date ranges
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    
    stats = {
        'total_uploads': user_uploads.count(),
        'completed_uploads': user_uploads.filter(status='completed').count(),
        'failed_uploads': user_uploads.filter(status='failed').count(), 
        'processing_uploads': user_uploads.filter(status__in=['uploaded', 'processing']).count(),
        'uploads_last_30_days': user_uploads.filter(created_at__gte=last_30_days).count(),
        'recent_uploads': CADUploadListSerializer(
            user_uploads.order_by('-created_at')[:5], 
            many=True,
            context={'request': request}
        ).data
    }
    
    return Response(stats)

def process_analysis_results(cad_upload, results_data):
    """Process and store analysis results from n8n"""
    
    # Define result type mapping
    result_types = {
        'dimensions': 'dimensions',
        'tolerances': 'tolerances', 
        'relationships': 'relationships',
        'materials': 'materials',
        'assembly': 'assembly'
    }
    
    for result_key, result_type in result_types.items():
        if result_key in results_data:
            result_data = results_data[result_key]
            
            # Create or update analysis result
            analysis_result, created = AnalysisResult.objects.get_or_create(
                upload=cad_upload,
                result_type=result_type,
                defaults={
                    'raw_data': result_data,
                    'confidence_score': result_data.get('confidence', 0.8),
                    'extraction_method': 'gemini-ai'
                }
            )
            
            if not created:
                analysis_result.raw_data = result_data
                analysis_result.confidence_score = result_data.get('confidence', 0.8)
                analysis_result.save()
            
            logger.info(f"Processed {result_type} results for upload {cad_upload.id}")

# Health check endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })
