from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CADUpload, AnalysisOptions, AnalysisResult, ProcessingLog, UserPreferences
import json

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class AnalysisOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisOptions
        fields = [
            'extract_dimensions', 'extract_tolerances', 'analyze_part_relationships',
            'extract_material_specifications', 'detect_assembly_components',
            'ai_model_version', 'confidence_threshold', 'max_analysis_time',
            'custom_prompt_additions'
        ]

class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = [
            'id', 'result_type', 'raw_data', 'processed_data', 'confidence_score',
            'extraction_method', 'processing_time_seconds', 'csv_file_path',
            'report_file_path', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProcessingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingLog
        fields = [
            'id', 'level', 'message', 'step', 'execution_time_ms',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class CADUploadDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    analysis_options = AnalysisOptionsSerializer(read_only=True)
    results = AnalysisResultSerializer(many=True, read_only=True)
    processing_logs = ProcessingLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = CADUpload
        fields = [
            'id', 'user', 'original_filename', 'file_path', 'file_size', 'file_hash',
            'project_name', 'drawing_number', 'revision', 'notes',
            'status', 'processing_started_at', 'processing_completed_at', 'progress_percentage',
            'n8n_execution_id', 'webhook_response', 'error_message', 'retry_count',
            'created_at', 'updated_at', 'analysis_options', 'results', 'processing_logs'
        ]
        read_only_fields = [
            'id', 'user', 'file_size', 'file_hash', 'status', 'processing_started_at',
            'processing_completed_at', 'progress_percentage', 'n8n_execution_id',
            'webhook_response', 'error_message', 'retry_count', 'created_at', 'updated_at'
        ]

class CADUploadListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CADUpload
        fields = [
            'id', 'user', 'original_filename', 'file_size', 'project_name',
            'drawing_number', 'revision', 'status', 'progress_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'file_size', 'status', 'progress_percentage',
            'created_at', 'updated_at'
        ]

class CADUploadCreateSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    metadata = serializers.CharField(write_only=True, required=False)
    analysis_options = AnalysisOptionsSerializer(write_only=True, required=False)
    
    class Meta:
        model = CADUpload
        fields = [
            'file', 'metadata', 'analysis_options', 'project_name',
            'drawing_number', 'revision', 'notes'
        ]
    
    def validate_file(self, value):
        """Validate uploaded file"""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        
        return value
    
    def validate_metadata(self, value):
        """Validate and parse metadata JSON"""
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format for metadata.")
        return {}
    
    def create(self, validated_data):
        """Create CADUpload instance with associated AnalysisOptions"""
        import hashlib
        
        # Extract file and metadata
        file = validated_data.pop('file')
        metadata = validated_data.pop('metadata', {})
        analysis_options_data = validated_data.pop('analysis_options', {})
        
        # Merge metadata with direct fields
        if metadata:
            validated_data.update({
                'project_name': metadata.get('project_name', validated_data.get('project_name')),
                'drawing_number': metadata.get('drawing_number', validated_data.get('drawing_number')),
                'revision': metadata.get('revision', validated_data.get('revision')),
                'notes': metadata.get('notes', validated_data.get('notes')),
            })
        
        # Calculate file hash
        file_content = file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        file.seek(0)  # Reset file pointer
        
        # Create CADUpload instance
        cad_upload = CADUpload.objects.create(
            user=self.context['request'].user,
            original_filename=file.name,
            file_path=file,
            file_size=file.size,
            file_hash=file_hash,
            **validated_data
        )
        
        # Create associated AnalysisOptions
        if metadata.get('analysis_options'):
            analysis_options_data.update(metadata['analysis_options'])
        
        AnalysisOptions.objects.create(
            upload=cad_upload,
            **analysis_options_data
        )
        
        return cad_upload

class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = [
            'default_extract_dimensions', 'default_extract_tolerances',
            'default_analyze_relationships', 'email_notifications',
            'processing_complete_notifications', 'azure_ad_object_id',
            'department', 'job_title', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ProcessingStatusSerializer(serializers.Serializer):
    """Serializer for processing status responses"""
    task_id = serializers.UUIDField()
    status = serializers.CharField()
    progress = serializers.IntegerField()
    message = serializers.CharField(required=False)
    results = serializers.JSONField(required=False)
    download_urls = serializers.JSONField(required=False)
    error_message = serializers.CharField(required=False)

class WebhookPayloadSerializer(serializers.Serializer):
    """Serializer for n8n webhook payload"""
    upload_id = serializers.UUIDField()
    file_url = serializers.URLField()
    analysis_options = AnalysisOptionsSerializer()
    metadata = serializers.JSONField()
    webhook_secret = serializers.CharField()

class N8NWebhookResponseSerializer(serializers.Serializer):
    """Serializer for n8n webhook response handling"""
    execution_id = serializers.CharField()
    status = serializers.CharField()
    upload_id = serializers.UUIDField()
    results = serializers.JSONField(required=False)
    error_message = serializers.CharField(required=False)
    progress = serializers.IntegerField(required=False) 