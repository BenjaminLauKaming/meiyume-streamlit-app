"""
Serializers for meiyume_core app - shared functionality across all assistants
"""

from rest_framework import serializers
from .models import UserPreferences, ProcessingLog

class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user preferences"""
    
    class Meta:
        model = UserPreferences
        fields = [
            'email_notifications',
            'processing_complete_notifications',
            'azure_ad_object_id',
            'department',
            'job_title',
            'assistant_preferences',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ProcessingLogSerializer(serializers.ModelSerializer):
    """Serializer for processing logs"""
    
    class Meta:
        model = ProcessingLog
        fields = [
            'id',
            'level',
            'message',
            'step',
            'execution_time_ms',
            'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at'] 