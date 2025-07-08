"""
Views for meiyume_core app - shared functionality across all assistants
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import UserPreferences, ProcessingLog
from .serializers import UserPreferencesSerializer
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from rest_framework.request import Request

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
        
        # Quality Assistant stats (future)
        stats['assistants']['quality'] = {'total': 0, 'completed': 0, 'failed': 0, 'processing': 0}
        
        # Complaint Assistant stats (future)
        stats['assistants']['complaint'] = {'total': 0, 'completed': 0, 'failed': 0, 'processing': 0}
        
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