"""
Serializers for CAD assistant
"""

import json
import hashlib
from rest_framework import serializers
from .models import CADUpload, CADAnalysisOptions, CADAnalysisResult

class CADAnalysisOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CADAnalysisOptions
        fields = [
            'extract_dimensions', 'extract_tolerances', 'analyze_part_relationships',
            'extract_material_specifications', 'detect_assembly_components',
            'ai_model_version', 'confidence_threshold', 'max_analysis_time',
            'custom_prompt_additions'
        ]

class CADAnalysisResultSerializer(serializers.ModelSerializer):
    upload_filename = serializers.CharField(source='upload.original_filename', read_only=True)
    upload_status = serializers.CharField(source='upload.status', read_only=True)
    
    class Meta:
        model = CADAnalysisResult
        fields = [
            'id', 'upload', 'upload_filename', 'upload_status', 'result_type',
            'raw_data', 'processed_data', 'confidence_score', 'extraction_method',
            'processing_time_seconds', 'csv_file_path', 'report_file_path',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CADUploadSerializer(serializers.ModelSerializer):
    analysis_options = CADAnalysisOptionsSerializer(read_only=True)
    results = CADAnalysisResultSerializer(many=True, read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = CADUpload
        fields = [
            'id', 'original_filename', 'file_path', 'file_size', 'file_size_mb',
            'project_name', 'drawing_number', 'revision', 'notes', 'status',
            'progress_percentage', 'processing_started_at', 'processing_completed_at',
            'error_message', 'analysis_options', 'results', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'file_hash', 'processing_started_at', 
            'processing_completed_at', 'n8n_execution_id', 'webhook_response',
            'created_at', 'updated_at'
        ]
    
    def get_file_size_mb(self, obj):
        """Display file size in MB"""
        return f"{obj.file_size / (1024*1024):.2f} MB"

class CADUploadCreateSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    metadata = serializers.CharField(write_only=True, required=False)
    analysis_options = CADAnalysisOptionsSerializer(write_only=True, required=False)
    
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
        
        CADAnalysisOptions.objects.create(
            upload=cad_upload,
            **analysis_options_data
        )
        
        return cad_upload 