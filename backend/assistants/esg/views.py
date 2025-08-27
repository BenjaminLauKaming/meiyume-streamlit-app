"""
ESG Assistant Views

Views for handling ESG audit document uploads, analysis results, and n8n webhooks.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging
import uuid

from .models import ESGUpload, ESGAnalysisResult, ESGWebhookLog
from .serializers import (
    ESGUploadSerializer, 
    ESGAnalysisResultSerializer, 
    ESGWebhookLogSerializer,
    ESGWebhookPayloadSerializer
)

logger = logging.getLogger(__name__)


class ESGUploadListCreateView(generics.ListCreateAPIView):
    """View for listing and creating ESG uploads"""
    
    serializer_class = ESGUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get ESG uploads for the authenticated user"""
        return ESGUpload.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create ESG upload with user association"""
        serializer.save(user=self.request.user)


class ESGUploadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting specific ESG uploads"""
    
    serializer_class = ESGUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get ESG uploads for the authenticated user"""
        return ESGUpload.objects.filter(user=self.request.user)


class ESGAnalysisResultView(generics.RetrieveAPIView):
    """View for retrieving ESG analysis results"""
    
    serializer_class = ESGAnalysisResultSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'upload_id'
    
    def get_queryset(self):
        """Get analysis results for user's uploads"""
        return ESGAnalysisResult.objects.filter(upload__user=self.request.user)


class ESGUploadStatusView(generics.GenericAPIView):
    """View for checking ESG upload status and results"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, upload_id):
        """Get upload status and results if available"""
        try:
            upload = ESGUpload.objects.get(id=upload_id, user=request.user)
            
            response_data = {
                'upload': ESGUploadSerializer(upload).data,
                'has_results': hasattr(upload, 'analysis_result'),
                'results': None
            }
            
            if hasattr(upload, 'analysis_result'):
                response_data['results'] = ESGAnalysisResultSerializer(upload.analysis_result).data
            
            return Response(response_data)
            
        except ESGUpload.DoesNotExist:
            return Response(
                {'error': 'Upload not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def esg_webhook_receiver(request):
    """
    Webhook endpoint to receive results from n8n workflow
    
    This endpoint receives the analysis results from the n8n workflow
    and updates the corresponding ESG upload and creates analysis results.
    """
    try:
        # Parse the webhook payload
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
        else:
            payload = request.POST.dict()
        
        logger.info(f"Received ESG webhook payload: {payload}")
        
        # Log the webhook call
        webhook_log = ESGWebhookLog.objects.create(
            webhook_payload=payload,
            n8n_execution_id=payload.get('execution_id'),
            processed=False
        )
        
        # Validate the payload
        serializer = ESGWebhookPayloadSerializer(data=payload)
        if not serializer.is_valid():
            error_msg = f"Invalid webhook payload: {serializer.errors}"
            logger.error(error_msg)
            webhook_log.error_message = error_msg
            webhook_log.save()
            return JsonResponse({'error': error_msg}, status=400)
        
        validated_data = serializer.validated_data
        
        # Find the upload record
        upload = None
        upload_id = validated_data.get('upload_id')
        execution_id = validated_data.get('execution_id')
        
        if upload_id:
            try:
                upload = ESGUpload.objects.get(id=upload_id)
                webhook_log.upload = upload
                webhook_log.save()
            except ESGUpload.DoesNotExist:
                error_msg = f"Upload with ID {upload_id} not found"
                logger.error(error_msg)
                webhook_log.error_message = error_msg
                webhook_log.save()
                return JsonResponse({'error': error_msg}, status=404)
        elif execution_id:
            try:
                upload = ESGUpload.objects.get(n8n_execution_id=execution_id)
                webhook_log.upload = upload
                webhook_log.save()
            except ESGUpload.DoesNotExist:
                error_msg = f"Upload with execution ID {execution_id} not found"
                logger.error(error_msg)
                webhook_log.error_message = error_msg
                webhook_log.save()
                return JsonResponse({'error': error_msg}, status=404)
        else:
            error_msg = "No upload_id or execution_id provided in webhook"
            logger.error(error_msg)
            webhook_log.error_message = error_msg
            webhook_log.save()
            return JsonResponse({'error': error_msg}, status=400)
        
        # Process the webhook data
        if validated_data.get('status') == 'error':
            # Handle error from n8n
            upload.status = 'failed'
            upload.error_message = validated_data.get('error_message', 'Analysis failed')
            upload.processing_completed_at = timezone.now()
            upload.save()
            
            webhook_log.processed = True
            webhook_log.processed_at = timezone.now()
            webhook_log.save()
            
            logger.error(f"ESG analysis failed for upload {upload.id}: {upload.error_message}")
            return JsonResponse({'status': 'error_processed'})
        
        # Create or update analysis results
        analysis_result, created = ESGAnalysisResult.objects.get_or_create(
            upload=upload,
            defaults={
                'raw_data': validated_data.get('raw_analysis', payload),
                'document_language': validated_data.get('document_language'),
                'total_volume_litres': validated_data.get('total_volume_litres'),
                'currency': validated_data.get('currency'),
                'total_cost': validated_data.get('total_cost'),
                'billing_period': validated_data.get('billing_period'),
                'confidence_score': validated_data.get('confidence_score'),
                'extraction_method': 'n8n-ai',
            }
        )
        
        if not created:
            # Update existing result
            analysis_result.raw_data = validated_data.get('raw_analysis', payload)
            analysis_result.document_language = validated_data.get('document_language')
            analysis_result.total_volume_litres = validated_data.get('total_volume_litres')
            analysis_result.currency = validated_data.get('currency')
            analysis_result.total_cost = validated_data.get('total_cost')
            analysis_result.billing_period = validated_data.get('billing_period')
            analysis_result.confidence_score = validated_data.get('confidence_score')
            analysis_result.save()
        
        # Update upload status
        upload.status = 'completed'
        upload.processing_completed_at = timezone.now()
        upload.webhook_response = payload
        upload.save()
        
        # Mark webhook as processed
        webhook_log.processed = True
        webhook_log.processed_at = timezone.now()
        webhook_log.save()
        
        logger.info(f"Successfully processed ESG webhook for upload {upload.id}")
        
        return JsonResponse({
            'status': 'success',
            'upload_id': str(upload.id),
            'analysis_created': created
        })
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in webhook payload: {str(e)}"
        logger.error(error_msg)
        return JsonResponse({'error': error_msg}, status=400)
    
    except Exception as e:
        error_msg = f"Unexpected error processing webhook: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return JsonResponse({'error': error_msg}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def esg_dashboard_stats(request):
    """Get ESG dashboard statistics for the user"""
    
    user = request.user
    uploads = ESGUpload.objects.filter(user=user)
    
    stats = {
        'total_uploads': uploads.count(),
        'completed_uploads': uploads.filter(status='completed').count(),
        'processing_uploads': uploads.filter(status__in=['uploaded', 'processing']).count(),
        'failed_uploads': uploads.filter(status='failed').count(),
        'total_volume_analysed': 0,
        'recent_uploads': []
    }
    
    # Calculate total volume
    completed_results = ESGAnalysisResult.objects.filter(
        upload__user=user,
        total_volume_litres__isnull=False
    )
    stats['total_volume_analysed'] = sum(
        result.total_volume_litres for result in completed_results
    )
    
    # Get recent uploads
    recent_uploads = uploads.order_by('-created_at')[:5]
    stats['recent_uploads'] = ESGUploadSerializer(recent_uploads, many=True).data
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_esg_upload_record(request):
    """
    Create an ESG upload record before sending to n8n
    
    This endpoint creates the upload record and returns the upload_id
    that should be sent to n8n for tracking.
    """
    try:
        # Create upload record
        upload_data = {
            'original_filename': request.data.get('filename'),
            'file_size': request.data.get('file_size', 0),
            'document_type': request.data.get('document_type', 'other'),
            'facility_name': request.data.get('facility_name'),
            'audit_period': request.data.get('audit_period'),
            'project_name': request.data.get('project_name'),
            'notes': request.data.get('notes'),
            'status': 'uploaded',
            'n8n_execution_id': str(uuid.uuid4())  # Generate temporary ID
        }
        
        serializer = ESGUploadSerializer(data=upload_data)
        if serializer.is_valid():
            upload = serializer.save(user=request.user)
            
            return Response({
                'upload_id': str(upload.id),
                'n8n_execution_id': upload.n8n_execution_id,
                'status': 'created'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error creating ESG upload record: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)