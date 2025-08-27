"""
ESG Assistant Serializers

Serializers for ESG audit document uploads and analysis results.
"""

from rest_framework import serializers
from .models import ESGUpload, ESGAnalysisResult, ESGWebhookLog


class ESGUploadSerializer(serializers.ModelSerializer):
    """Serializer for ESG upload model"""
    
    class Meta:
        model = ESGUpload
        fields = [
            'id', 'original_filename', 'file_size', 'document_type',
            'facility_name', 'audit_period', 'project_name', 'notes',
            'status', 'progress_percentage', 'n8n_execution_id',
            'created_at', 'updated_at', 'processing_started_at', 
            'processing_completed_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'processing_started_at',
            'processing_completed_at', 'n8n_execution_id'
        ]


class ESGAnalysisResultSerializer(serializers.ModelSerializer):
    """Serializer for ESG analysis results"""
    
    upload = ESGUploadSerializer(read_only=True)
    
    class Meta:
        model = ESGAnalysisResult
        fields = [
            'upload', 'document_language', 'total_volume_litres',
            'currency', 'total_cost', 'billing_period', 'compliance_status',
            'raw_data', 'processed_data', 'confidence_score',
            'extraction_method', 'processing_time_seconds',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ESGWebhookLogSerializer(serializers.ModelSerializer):
    """Serializer for ESG webhook logs"""
    
    class Meta:
        model = ESGWebhookLog
        fields = [
            'id', 'upload', 'n8n_execution_id', 'webhook_payload',
            'processed', 'error_message', 'received_at', 'processed_at'
        ]
        read_only_fields = ['id', 'received_at', 'processed_at']


class ESGWebhookPayloadSerializer(serializers.Serializer):
    """Serializer for incoming webhook payload from n8n"""
    
    # Required fields that n8n should send
    execution_id = serializers.CharField(max_length=100, required=False)
    upload_id = serializers.UUIDField(required=False)
    
    # Analysis results
    document_language = serializers.CharField(max_length=50, required=False)
    total_volume_litres = serializers.FloatField(required=False, allow_null=True)
    
    # Optional fields
    currency = serializers.CharField(max_length=10, required=False)
    total_cost = serializers.FloatField(required=False, allow_null=True)
    billing_period = serializers.CharField(max_length=100, required=False)
    confidence_score = serializers.FloatField(required=False, allow_null=True)
    
    # Raw analysis data
    raw_analysis = serializers.JSONField(required=False)
    
    # Status and error handling
    status = serializers.ChoiceField(
        choices=['success', 'error', 'partial'],
        default='success'
    )
    error_message = serializers.CharField(required=False, allow_blank=True)
    
    def validate_total_volume_litres(self, value):
        """Validate volume is positive"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Volume cannot be negative")
        return value
