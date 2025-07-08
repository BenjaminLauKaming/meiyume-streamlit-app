"""
Views for CAD assistant
"""

import json
import logging
from typing import Type
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from django.db import models

from .models import CADUpload, CADAnalysisOptions, CADAnalysisResult
from .serializers import (
    CADUploadSerializer, 
    CADUploadCreateSerializer,
    CADAnalysisOptionsSerializer,
    CADAnalysisResultSerializer
)
from .utils import send_to_n8n_webhook

logger = logging.getLogger(__name__)

class CADUploadListCreateView(generics.ListCreateAPIView):
    """View for listing and creating CAD uploads"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CADUploadCreateSerializer
        return CADUploadSerializer
    
    def get_queryset(self):
        return CADUpload.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create upload and trigger n8n processing"""
        cad_upload = serializer.save()
        
        # Create default analysis options (use get_or_create to avoid duplicates)
        CADAnalysisOptions.objects.get_or_create(upload=cad_upload)
        
        # Send to n8n for processing
        try:
            send_to_n8n_webhook(cad_upload)
            cad_upload.status = 'processing'
            cad_upload.processing_started_at = timezone.now()
            cad_upload.save()
        except Exception as e:
            logger.error(f"Failed to send CAD upload {cad_upload.id} to n8n: {str(e)}")
            cad_upload.status = 'failed'
            cad_upload.error_message = str(e)
            cad_upload.save()

class CADUploadDetailView(generics.RetrieveDestroyAPIView):
    """View for retrieving and deleting CAD uploads"""
    
    serializer_class = CADUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CADUpload.objects.filter(user=self.request.user)

class CADAnalysisResultListView(generics.ListAPIView):
    """View for listing analysis results"""
    
    serializer_class = CADAnalysisResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CADAnalysisResult.objects.filter(
            upload__user=self.request.user
        ).select_related('upload')

class CADAnalysisResultDetailView(generics.RetrieveAPIView):
    """View for retrieving specific analysis results"""
    
    serializer_class = CADAnalysisResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CADAnalysisResult.objects.filter(
            upload__user=self.request.user,
            upload_id=self.kwargs['upload_id']
        ).select_related('upload')

class CADAnalysisOptionsView(generics.RetrieveUpdateAPIView):
    """View for managing analysis options"""
    
    serializer_class = CADAnalysisOptionsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(
            CADAnalysisOptions,
            upload_id=self.kwargs['upload_id'],
            upload__user=self.request.user
        )

class N8nWebhookCallbackView(generics.GenericAPIView):
    """View for handling n8n webhook callbacks"""
    
    permission_classes = []  # No authentication required for webhooks
    authentication_classes = []  # No authentication required for webhooks
    
    def post(self, request, *args, **kwargs):
        """Handle n8n webhook callback"""
        try:
            # Validate webhook secret
            webhook_secret = request.data.get('webhook_secret')
            if webhook_secret != getattr(settings, 'N8N_WEBHOOK_SECRET', ''):
                logger.warning("Invalid webhook secret received")
                return Response({'error': 'Invalid webhook secret'}, status=status.HTTP_403_FORBIDDEN)
            
            # Extract data from webhook
            execution_id = request.data.get('execution_id')
            upload_id = request.data.get('upload_id')
            status_update = request.data.get('status')
            results = request.data.get('results', {})
            progress = request.data.get('progress', 0)
            
            # Find the upload
            try:
                cad_upload = CADUpload.objects.get(id=upload_id)
            except CADUpload.DoesNotExist:
                logger.error(f"CAD upload {upload_id} not found for webhook callback")
                return Response({'error': 'Upload not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Update upload status
            cad_upload.n8n_execution_id = execution_id
            cad_upload.webhook_response = request.data
            cad_upload.progress_percentage = progress
            
            if status_update == 'completed':
                cad_upload.status = 'completed'
                cad_upload.processing_completed_at = timezone.now()
                
                # Process and store results
                self._process_analysis_results(cad_upload, results)
                
            elif status_update == 'failed':
                cad_upload.status = 'failed'
                cad_upload.error_message = results.get('error', 'Processing failed')
            
            cad_upload.save()
            
            return Response({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Error processing n8n webhook: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _process_analysis_results(self, cad_upload: CADUpload, results_data: dict):
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
                analysis_result, created = CADAnalysisResult.objects.get_or_create(
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